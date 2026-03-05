import arcade
import numpy as np
import time
import threading
import queue
import os
from config import (
    WIDTH, HEIGHT,
    GRID_SIZES, NUM_SPEAKERS, MAX_LIFE,
    GRID_CELL_SIZE, GRID_PADDING,
    GRID_COLOR, GRID_SELECTED_COLOR, GRID_VISITED_COLOR,
    TEXT_COLOR, TITLE_COLOR, ERROR_COLOR, SUCCESS_COLOR,
    FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL,
    SAMPLE_RATE, VOICES_DIR, SPEAKER_NAMES
)
from game import GameState
import sound_manager

class SoundFairyGame(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Sound Fairy Game - Voice Search")
        arcade.set_background_color((20, 20, 30))
        self.game = None
        self.current_screen = "title"

        self.select_grid_idx = 1
        self.select_speaker_idx = 0
        self.selected_grid_size = GRID_SIZES[self.select_grid_idx]
        self.selected_num_speakers = NUM_SPEAKERS[self.select_speaker_idx]

        self.target_speaker_name = None
        self.last_feedback = None
        self.feedback_time = 0
        self.show_answer_dialog = False
        self.is_running = True

    def on_update(self, delta_time):
        if self.current_screen == "game":
            if self.last_feedback:
                self.feedback_time += delta_time
                if self.feedback_time > 3.0:
                    self.last_feedback = None
                    self.feedback_time = 0

    def on_draw(self):
        self.clear()
        if self.current_screen == "title": self.draw_title()
        elif self.current_screen == "select": self.draw_select()
        elif self.current_screen == "instruction": self.draw_instruction()
        elif self.current_screen == "game": self.draw_game()
        elif self.current_screen == "result": self.draw_result()

    def draw_title(self):
        arcade.Text("Sound Fairy Game", WIDTH // 2, HEIGHT - 100, TITLE_COLOR, FONT_SIZE_TITLE, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Voice Search - Find the target speaker!", WIDTH // 2, HEIGHT - 180, TEXT_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Press ENTER to start", WIDTH // 2, HEIGHT // 2 - 100, SUCCESS_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Press Q to quit", WIDTH // 2, 50, TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center", anchor_y="center").draw()

    def draw_select(self):
        arcade.Text("Select Difficulty", WIDTH // 2, HEIGHT - 60, TITLE_COLOR, FONT_SIZE_TITLE, anchor_x="center", anchor_y="center").draw()
        grid_y = HEIGHT - 150
        arcade.Text("Grid Size:", 100, grid_y, TEXT_COLOR, FONT_SIZE_BODY, anchor_x="left", anchor_y="center").draw()
        for idx, size in enumerate(GRID_SIZES):
            x_pos = 300 + idx * 120
            color = SUCCESS_COLOR if idx == self.select_grid_idx else TEXT_COLOR
            arcade.Text(f"{size}x{size}", x_pos, grid_y, color, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()

        speaker_y = grid_y - 80
        arcade.Text("Speakers:", 100, speaker_y, TEXT_COLOR, FONT_SIZE_BODY, anchor_x="left", anchor_y="center").draw()
        for idx, num in enumerate(NUM_SPEAKERS):
            x_pos = 300 + idx * 120
            color = SUCCESS_COLOR if idx == self.select_speaker_idx else TEXT_COLOR
            arcade.Text(f"{num}", x_pos, speaker_y, color, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()

        arcade.Text("1/2/3: Grid Size | Q/W: Speakers | ENTER: Start", WIDTH // 2, 50, TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center", anchor_y="center").draw()

    def draw_instruction(self):
        arcade.Text("Game Instructions", WIDTH // 2, HEIGHT - 80, TITLE_COLOR, FONT_SIZE_TITLE, anchor_x="center", anchor_y="center").draw()
        y_pos = HEIGHT - 180
        arcade.Text(f"Target Speaker: {self.target_speaker_name}", WIDTH // 2, y_pos, TEXT_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Sample voice playing...", WIDTH // 2, y_pos - 60, SUCCESS_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Press ENTER to start the game", WIDTH // 2, y_pos - 160, TITLE_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()

    def draw_game(self):
        if not self.game: return
        arcade.Text(f"Life: {'❤' * self.game.remaining_life} (Turns: {self.game.current_turn})", 20, HEIGHT - 30, TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="left", anchor_y="top").draw()
        self.draw_grid()
        
        help_str = "Y: Answer | N: Skip" if self.show_answer_dialog else "↑↓←→: Move | SHIFT+矢印: Look | SPACE: Sample"
        arcade.Text(help_str, WIDTH // 2, 20, TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center", anchor_y="bottom").draw()

        if self.last_feedback:
            arcade.Text(self.last_feedback, WIDTH // 2, HEIGHT // 2, ERROR_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()
        if self.show_answer_dialog:
            self.draw_answer_dialog()

    def draw_grid(self):
        grid_size, cell_size = self.game.grid_size, GRID_CELL_SIZE
        total_width, total_height = grid_size * cell_size, grid_size * cell_size
        grid_start_x = (WIDTH - total_width) // 2
        grid_start_y = (HEIGHT - total_height) // 2 + 40

        for i in range(grid_size + 1):
            arcade.draw_line(grid_start_x + i * cell_size, grid_start_y, grid_start_x + i * cell_size, grid_start_y + total_height, GRID_COLOR, 2)
            arcade.draw_line(grid_start_x, grid_start_y + i * cell_size, grid_start_x + total_width, grid_start_y + i * cell_size, GRID_COLOR, 2)

        for x in range(grid_size):
            for y in range(grid_size):
                cell_x = grid_start_x + x * cell_size + cell_size // 2
                cell_y = grid_start_y + y * cell_size + cell_size // 2

                if (x, y) == self.game.current_pos:
                    arcade.draw_circle_filled(cell_x, cell_y, 8, GRID_SELECTED_COLOR)
                    
                    # プレイヤーの向いている方向（視線）を描画
                    fx, fy = self.game.facing_dir
                    arcade.draw_line(cell_x, cell_y, cell_x + fx * 15, cell_y + fy * 15, (255, 50, 50), 3)
                    
                elif (x, y) in self.game.visited_cells:
                    arcade.draw_circle_filled(cell_x, cell_y, 6, GRID_VISITED_COLOR)

    def draw_answer_dialog(self):
        dx, dy, dw, dh = WIDTH // 2, HEIGHT // 2, 400, 150
        x1, x2, y1, y2 = dx - dw // 2, dx + dw // 2, dy - dh // 2, dy + dh // 2
        arcade.draw_line(x1, y1, x2, y1, TITLE_COLOR, 3); arcade.draw_line(x1, y2, x2, y2, TITLE_COLOR, 3)
        arcade.draw_line(x1, y1, x1, y2, TITLE_COLOR, 3); arcade.draw_line(x2, y1, x2, y2, TITLE_COLOR, 3)
        
        arcade.Text("Is this the target?", dx, dy + 50, TITLE_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Y: Answer", dx - 100, dy - 30, SUCCESS_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()
        arcade.Text("N: Skip", dx + 100, dy - 30, ERROR_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()

    def draw_result(self):
        title_text, title_color = ("Correct!", SUCCESS_COLOR) if self.game.is_won else ("Game Over", ERROR_COLOR)
        arcade.Text(title_text, WIDTH // 2, HEIGHT - 100, title_color, FONT_SIZE_TITLE, anchor_x="center", anchor_y="center").draw()
        arcade.Text(f"Turns: {self.game.current_turn}", WIDTH // 2, HEIGHT - 180, TEXT_COLOR, FONT_SIZE_BODY, anchor_x="center", anchor_y="center").draw()
        
        self.draw_result_grid()
        arcade.Text("ENTER: Play Again | M: Change Rules | Q: Quit", WIDTH // 2, 30, TEXT_COLOR, FONT_SIZE_SMALL, anchor_x="center", anchor_y="bottom").draw()

    def draw_result_grid(self):
        grid_size, cell_size = self.game.grid_size, 40
        total_width, total_height = grid_size * cell_size, grid_size * cell_size
        grid_start_x = (WIDTH - total_width) // 2
        grid_start_y = (HEIGHT - total_height - 280) // 2 + 40

        for i in range(grid_size + 1):
            arcade.draw_line(grid_start_x + i * cell_size, grid_start_y, grid_start_x + i * cell_size, grid_start_y + total_height, GRID_COLOR, 1)
            arcade.draw_line(grid_start_x, grid_start_y + i * cell_size, grid_start_x + total_width, grid_start_y + i * cell_size, GRID_COLOR, 1)

        for speaker_id in range(self.game.num_speakers):
            x, y = self.game.speaker_positions[speaker_id]
            cell_x = grid_start_x + x * cell_size + cell_size // 2
            cell_y = grid_start_y + y * cell_size + cell_size // 2

            if speaker_id == self.game.target_speaker:
                arcade.draw_circle_filled(cell_x, cell_y, 8, SUCCESS_COLOR)
                arcade.draw_circle_outline(cell_x, cell_y, 12, GRID_SELECTED_COLOR, 2)
            else:
                arcade.draw_circle_filled(cell_x, cell_y, 5, (150, 150, 150))

        label_y = grid_start_y + total_height + 30
        for speaker_id in range(self.game.num_speakers):
            speaker_name = self.get_speaker_name(speaker_id)
            color = SUCCESS_COLOR if speaker_id == self.game.target_speaker else (150, 150, 150)
            text = f"● {speaker_name}" + (" (目標)" if speaker_id == self.game.target_speaker else "")
            arcade.Text(text, WIDTH // 2 + (speaker_id - 1) * 150, label_y, color, FONT_SIZE_SMALL, anchor_x="center", anchor_y="top").draw()

    def on_key_press(self, key, modifiers):
        if self.current_screen == "title":
            if key == arcade.key.ENTER: self.current_screen = "select"
            elif key == arcade.key.Q: self.is_running = False; arcade.close_window()
        elif self.current_screen == "select":
            if key == arcade.key.KEY_1: self.select_grid_idx = 0
            elif key == arcade.key.KEY_2: self.select_grid_idx = 1
            elif key == arcade.key.KEY_3: self.select_grid_idx = 2
            elif key == arcade.key.Q: self.select_speaker_idx = max(0, self.select_speaker_idx - 1)
            elif key == arcade.key.W: self.select_speaker_idx = min(2, self.select_speaker_idx + 1)
            elif key == arcade.key.ENTER:
                self.selected_grid_size = GRID_SIZES[self.select_grid_idx]
                self.selected_num_speakers = NUM_SPEAKERS[self.select_speaker_idx]
                self.start_instruction()
        elif self.current_screen == "instruction":
            if key == arcade.key.ENTER: self.start_game()
        elif self.current_screen == "game":
            is_shift = modifiers & arcade.key.MOD_SHIFT

            if key == arcade.key.UP:
                self.show_answer_dialog = False
                if is_shift:
                    self.game.change_facing(0, 1)
                    self.start_game_turn() # 首を振るだけなので声だけ再生
                else:
                    sound_manager.play_footstep_se() # 移動した瞬間に足音を鳴らす
                    self.game.move_player(0, 1)
                    if self.game.input_mode == "move_only": self.start_game_turn()
            elif key == arcade.key.DOWN:
                self.show_answer_dialog = False
                if is_shift:
                    self.game.change_facing(0, -1)
                    self.start_game_turn()
                else:
                    sound_manager.play_footstep_se()
                    self.game.move_player(0, -1)
                    if self.game.input_mode == "move_only": self.start_game_turn()
            elif key == arcade.key.LEFT:
                self.show_answer_dialog = False
                if is_shift:
                    self.game.change_facing(-1, 0)
                    self.start_game_turn()
                else:
                    sound_manager.play_footstep_se()
                    self.game.move_player(-1, 0)
                    if self.game.input_mode == "move_only": self.start_game_turn()
            elif key == arcade.key.RIGHT:
                self.show_answer_dialog = False
                if is_shift:
                    self.game.change_facing(1, 0)
                    self.start_game_turn()
                else:
                    sound_manager.play_footstep_se()
                    self.game.move_player(1, 0)
                    if self.game.input_mode == "move_only": self.start_game_turn()
            elif key == arcade.key.ENTER:
                self.show_answer_dialog = True
            elif key == arcade.key.Y:
                if self.show_answer_dialog:
                    self.show_answer_dialog = False
                    self.handle_cell_confirm()
            elif key == arcade.key.N:
                if self.show_answer_dialog:
                    self.show_answer_dialog = False
                    self.game.skip_turn()
                    self.start_game_turn()
            elif key == arcade.key.SPACE:
                self.play_sample_voice()
            elif key == arcade.key.Q:
                self.is_running = False; arcade.close_window()
        elif self.current_screen == "result":
            if key == arcade.key.ENTER: self.start_instruction()
            elif key == arcade.key.M: self.current_screen = "select"
            elif key == arcade.key.Q: self.is_running = False; arcade.close_window()

    def start_instruction(self):
        self.game = GameState(self.selected_grid_size, self.selected_num_speakers)
        self.game.input_mode = "move_and_confirm"
        self.target_speaker_name = self.get_speaker_name(self.game.target_speaker)
        
        # バグ修正：前回のUI状態をリセット
        self.last_feedback = None
        self.feedback_time = 0
        self.show_answer_dialog = False
        
        self.current_screen = "instruction"
        self.play_sample_voice()

    def start_game(self):
        self.current_screen = "game"
        self.start_game_turn()

    def start_game_turn(self):
        if not self.game: return
        speakers_data = {}
        voice_type = "game_1" if self.game.current_turn % 2 == 0 else "game_2"
        for speaker_id in range(self.game.num_speakers):
            audio_data, sample_rate = sound_manager.load_voice_file(speaker_id, voice_type)
            if audio_data is not None:
                speakers_data[speaker_id] = (audio_data, sample_rate)

        if speakers_data:
            sound_manager.play_multiple_speakers_stereo(
                speakers_data,
                self.game.speaker_positions,
                self.game.grid_size,
                self.game.target_speaker,
                self.game.current_pos,
                self.game.facing_dir
            )
        

    def play_sample_voice(self):
        if not self.game: return
        speaker_id = self.game.target_speaker
        audio_data, sample_rate = sound_manager.load_voice_file(speaker_id, "sample")
        if audio_data is not None:
            sound_manager.play_voice_stereo(audio_data, sample_rate, 0.5, 0.5)

    def handle_cell_confirm(self):
        if not self.game: return
        is_correct = self.game.confirm_cell()
        if is_correct:
            self.current_screen = "result"
        else:
            closest_id = self.game.get_closest_speaker()
            closest_name = self.get_speaker_name(closest_id)
            self.last_feedback = f"Wrong! {closest_name} is closest"
            self.feedback_time = 0
            if self.game.is_game_over:
                self.current_screen = "result"
            else:
                self.start_game_turn()

    def get_speaker_name(self, speaker_id):
        return SPEAKER_NAMES[speaker_id] if speaker_id < len(SPEAKER_NAMES) else "Unknown"

def main():
    app = SoundFairyGame()
    app.run()

if __name__ == "__main__":
    main()