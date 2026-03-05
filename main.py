import arcade
import numpy as np
import time
import threading
import queue
import os
from config import (
    WIDTH,
    HEIGHT,
    GRID_SIZES,
    NUM_SPEAKERS,
    MAX_LIFE,
    GRID_CELL_SIZE,
    GRID_PADDING,
    GRID_COLOR,
    GRID_SELECTED_COLOR,
    GRID_VISITED_COLOR,
    TEXT_COLOR,
    TITLE_COLOR,
    ERROR_COLOR,
    SUCCESS_COLOR,
    FONT_SIZE_TITLE,
    FONT_SIZE_BODY,
    FONT_SIZE_SMALL,
    SAMPLE_RATE,
    VOICES_DIR,
    SPEAKER_NAMES,
)
from game import GameState
import sound_manager


class SoundFairyGame(arcade.Window):
    """グリッド探索ゲーム - マルチスピーカー立体音響探索"""

    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Sound Fairy Game - Voice Search")
        arcade.set_background_color((20, 20, 30))

        # ゲーム状態管理
        self.game = None
        self.current_screen = (
            "title"  # "title", "select", "instruction", "game", "result"
        )

        # 難易度選択（保存用）
        self.select_grid_idx = 1  # デフォルト: 5×5
        self.select_speaker_idx = 0  # デフォルト: 1人
        self.selected_grid_size = GRID_SIZES[self.select_grid_idx]
        self.selected_num_speakers = NUM_SPEAKERS[self.select_speaker_idx]

        # ゲーム画面管理
        self.target_speaker_name = None
        self.last_feedback = None
        self.feedback_time = 0
        self.show_answer_dialog = False  # Answer/Skip ダイアログ表示フラグ

        # オーディオ・スレッド
        self.audio_queue = queue.Queue()
        self.audio_thread = None
        self.is_running = True

        print("Sound Fairy Game 初期化完了")

    def on_update(self, delta_time):
        """ゲーム更新"""
        if self.current_screen == "game":
            self.update_game(delta_time)

    def update_game(self, delta_time):
        """ゲーム画面の更新"""
        # フィードバック時間の管理
        if self.last_feedback:
            self.feedback_time += delta_time
            if self.feedback_time > 3.0:  # 3秒後にフィードバックをクリア
                self.last_feedback = None
                self.feedback_time = 0

    def on_draw(self):
        """画面描画"""
        self.clear()

        if self.current_screen == "title":
            self.draw_title()
        elif self.current_screen == "select":
            self.draw_select()
        elif self.current_screen == "instruction":
            self.draw_instruction()
        elif self.current_screen == "game":
            self.draw_game()
        elif self.current_screen == "result":
            self.draw_result()

    def draw_title(self):
        """タイトル画面描画"""
        # タイトル
        title_text = arcade.Text(
            "Sound Fairy Game",
            WIDTH // 2,
            HEIGHT - 100,
            TITLE_COLOR,
            FONT_SIZE_TITLE,
            anchor_x="center",
            anchor_y="center",
        )
        title_text.draw()

        # サブタイトル
        subtitle_text = arcade.Text(
            "Voice Search - Find the target speaker!",
            WIDTH // 2,
            HEIGHT - 180,
            TEXT_COLOR,
            FONT_SIZE_BODY,
            anchor_x="center",
            anchor_y="center",
        )
        subtitle_text.draw()

        # スタート指示
        start_text = arcade.Text(
            "Press ENTER to start",
            WIDTH // 2,
            HEIGHT // 2 - 100,
            SUCCESS_COLOR,
            FONT_SIZE_BODY,
            anchor_x="center",
            anchor_y="center",
        )
        start_text.draw()

        # 終了指示
        quit_text = arcade.Text(
            "Press Q to quit",
            WIDTH // 2,
            50,
            TEXT_COLOR,
            FONT_SIZE_SMALL,
            anchor_x="center",
            anchor_y="center",
        )
        quit_text.draw()

    def draw_select(self):
        """難易度選択画面描画"""
        # タイトル
        title = arcade.Text(
            "Select Difficulty",
            WIDTH // 2,
            HEIGHT - 60,
            TITLE_COLOR,
            FONT_SIZE_TITLE,
            anchor_x="center",
            anchor_y="center",
        )
        title.draw()

        # グリッドサイズ選択
        grid_y = HEIGHT - 150
        grid_label = arcade.Text(
            "Grid Size:",
            100,
            grid_y,
            TEXT_COLOR,
            FONT_SIZE_BODY,
            anchor_x="left",
            anchor_y="center",
        )
        grid_label.draw()

        for idx, size in enumerate(GRID_SIZES):
            x_pos = 300 + idx * 120
            color = SUCCESS_COLOR if idx == self.select_grid_idx else TEXT_COLOR
            text = arcade.Text(
                f"{size}x{size}",
                x_pos,
                grid_y,
                color,
                FONT_SIZE_BODY,
                anchor_x="center",
                anchor_y="center",
            )
            text.draw()

        # 話者数選択
        speaker_y = grid_y - 80
        speaker_label = arcade.Text(
            "Speakers:",
            100,
            speaker_y,
            TEXT_COLOR,
            FONT_SIZE_BODY,
            anchor_x="left",
            anchor_y="center",
        )
        speaker_label.draw()

        for idx, num in enumerate(NUM_SPEAKERS):
            x_pos = 300 + idx * 120
            color = SUCCESS_COLOR if idx == self.select_speaker_idx else TEXT_COLOR
            text = arcade.Text(
                f"{num}",
                x_pos,
                speaker_y,
                color,
                FONT_SIZE_BODY,
                anchor_x="center",
                anchor_y="center",
            )
            text.draw()

        # 操作説明
        instruction = arcade.Text(
            "1/2/3: Grid Size | Q/W: Speakers | ENTER: Start",
            WIDTH // 2,
            50,
            TEXT_COLOR,
            FONT_SIZE_SMALL,
            anchor_x="center",
            anchor_y="center",
        )
        instruction.draw()

    def draw_instruction(self):
        """ゲーム説明画面描画"""
        # タイトル
        title = arcade.Text(
            "Game Instructions",
            WIDTH // 2,
            HEIGHT - 80,
            TITLE_COLOR,
            FONT_SIZE_TITLE,
            anchor_x="center",
            anchor_y="center",
        )
        title.draw()

        # サンプル音声再生状態表示
        y_pos = HEIGHT - 180
        message = arcade.Text(
            f"Target Speaker: {self.target_speaker_name}",
            WIDTH // 2,
            y_pos,
            TEXT_COLOR,
            FONT_SIZE_BODY,
            anchor_x="center",
            anchor_y="center",
        )
        message.draw()

        y_pos -= 60
        sample_status = arcade.Text(
            "Sample voice playing...",
            WIDTH // 2,
            y_pos,
            SUCCESS_COLOR,
            FONT_SIZE_BODY,
            anchor_x="center",
            anchor_y="center",
        )
        sample_status.draw()

        y_pos -= 100
        start_instruction = arcade.Text(
            "Press ENTER to start the game",
            WIDTH // 2,
            y_pos,
            TITLE_COLOR,
            FONT_SIZE_BODY,
            anchor_x="center",
            anchor_y="center",
        )
        start_instruction.draw()

    def draw_game(self):
        """ゲーム画面描画"""
        if not self.game:
            return

        # 左上: ライフとターンヌ情報
        ui_left = 20
        ui_top = HEIGHT - 30

        life_text = arcade.Text(
            f"Life: {'❤' * self.game.remaining_life} (Turns: {self.game.current_turn})",
            ui_left,
            ui_top,
            TEXT_COLOR,
            FONT_SIZE_SMALL,
            anchor_x="left",
            anchor_y="top",
        )
        life_text.draw()

        # グリッド描画
        self.draw_grid()

        # 下部: キー操作説明
        if self.show_answer_dialog:
            help_text_str = "Y: Answer | N: Skip"
        elif self.game.input_mode == "move_only":
            help_text_str = "↑↓←→: Move (auto-advance) | SPACE: Sample | Q: Quit"
        else:
            help_text_str = "↑↓←→: Move | ENTER: Confirm | SPACE: Sample | Q: Quit"

        help_text = arcade.Text(
            help_text_str,
            WIDTH // 2,
            20,
            TEXT_COLOR,
            FONT_SIZE_SMALL,
            anchor_x="center",
            anchor_y="bottom",
        )
        help_text.draw()

        # フィードバック表示
        if self.last_feedback:
            feedback_text = arcade.Text(
                self.last_feedback,
                WIDTH // 2,
                HEIGHT // 2,
                ERROR_COLOR,
                FONT_SIZE_BODY,
                anchor_x="center",
                anchor_y="center",
            )
            feedback_text.draw()

        # Answer/Skip ダイアログ表示
        if self.show_answer_dialog:
            self.draw_answer_dialog()

    def draw_grid(self):
        """グリッド描画（シンプル版：線のみ）"""
        if not self.game:
            return

        grid_size = self.game.grid_size
        cell_size = GRID_CELL_SIZE

        # グリッド全体の計算
        total_width = grid_size * cell_size
        total_height = grid_size * cell_size
        grid_start_x = (WIDTH - total_width) // 2
        grid_start_y = (HEIGHT - total_height) // 2 + 40

        # グリッド線を描画（縦横）
        line_color = GRID_COLOR
        for i in range(grid_size + 1):
            # 縦線
            arcade.draw_line(
                grid_start_x + i * cell_size,
                grid_start_y,
                grid_start_x + i * cell_size,
                grid_start_y + total_height,
                line_color,
                2,
            )
            # 横線
            arcade.draw_line(
                grid_start_x,
                grid_start_y + i * cell_size,
                grid_start_x + total_width,
                grid_start_y + i * cell_size,
                line_color,
                2,
            )

        # 各セルに選択状態を表示
        for x in range(grid_size):
            for y in range(grid_size):
                cell_x = grid_start_x + x * cell_size + cell_size // 2
                cell_y = grid_start_y + y * cell_size + cell_size // 2

                # 選択中のマスに色付きテキストを表示
                if (x, y) == self.game.current_pos:
                    arcade.draw_circle_filled(cell_x, cell_y, 8, GRID_SELECTED_COLOR)
                elif (x, y) in self.game.visited_cells:
                    arcade.draw_circle_filled(cell_x, cell_y, 6, GRID_VISITED_COLOR)

    def draw_answer_dialog(self):
        """Answer/Skip ダイアログ描画"""
        # ダイアログボックス
        dialog_x = WIDTH // 2
        dialog_y = HEIGHT // 2
        dialog_width = 400
        dialog_height = 150

        # ダイアログ背景を矩形で描画（線で囲む）
        x1 = dialog_x - dialog_width // 2
        x2 = dialog_x + dialog_width // 2
        y1 = dialog_y - dialog_height // 2
        y2 = dialog_y + dialog_height // 2

        # 矩形の枠線を描画
        arcade.draw_line(x1, y1, x2, y1, TITLE_COLOR, 3)  # 上
        arcade.draw_line(x1, y2, x2, y2, TITLE_COLOR, 3)  # 下
        arcade.draw_line(x1, y1, x1, y2, TITLE_COLOR, 3)  # 左
        arcade.draw_line(x2, y1, x2, y2, TITLE_COLOR, 3)  # 右

        # ダイアログタイトル
        title = arcade.Text(
            "Is this the target?",
            dialog_x,
            dialog_y + 50,
            TITLE_COLOR,
            FONT_SIZE_BODY,
            anchor_x="center",
            anchor_y="center",
        )
        title.draw()

        # Yes/No ボタンテキスト
        yes_text = arcade.Text(
            "Y: Answer",
            dialog_x - 100,
            dialog_y - 30,
            SUCCESS_COLOR,
            FONT_SIZE_BODY,
            anchor_x="center",
            anchor_y="center",
        )
        yes_text.draw()

        no_text = arcade.Text(
            "N: Skip",
            dialog_x + 100,
            dialog_y - 30,
            ERROR_COLOR,
            FONT_SIZE_BODY,
            anchor_x="center",
            anchor_y="center",
        )
        no_text.draw()

    def draw_result(self):
        """リザルト画面描画（全話者位置表示）"""
        if not self.game:
            return

        # 背景は既に clear() で描画されているのでスキップ

        # 結果タイトル
        if self.game.is_won:
            title_text = "Correct!"
            title_color = SUCCESS_COLOR
        else:
            title_text = "Game Over"
            title_color = ERROR_COLOR

        title = arcade.Text(
            title_text,
            WIDTH // 2,
            HEIGHT - 100,
            title_color,
            FONT_SIZE_TITLE,
            anchor_x="center",
            anchor_y="center",
        )
        title.draw()

        # スコア（ターン数）
        score_text = arcade.Text(
            f"Turns: {self.game.current_turn}",
            WIDTH // 2,
            HEIGHT - 180,
            TEXT_COLOR,
            FONT_SIZE_BODY,
            anchor_x="center",
            anchor_y="center",
        )
        score_text.draw()

        # グリッド表示（話者位置入り）
        self.draw_result_grid()

        # 再スタート指示
        restart_text = arcade.Text(
            "ENTER: Play Again | M: Change Rules | Q: Quit",
            WIDTH // 2, 30,
            TEXT_COLOR, FONT_SIZE_SMALL,
            anchor_x="center", anchor_y="bottom"
        )
        restart_text.draw()

    def draw_result_grid(self):
        """リザルト画面のグリッド描画（全話者位置表示）"""
        if not self.game:
            return

        grid_size = self.game.grid_size
        cell_size = 40  # 小さめのセルサイズ

        # グリッド全体の計算
        total_width = grid_size * cell_size
        total_height = grid_size * cell_size
        grid_start_x = (WIDTH - total_width) // 2
        grid_start_y = (HEIGHT - total_height - 280) // 2 + 40

        # グリッド線を描画
        line_color = GRID_COLOR
        for i in range(grid_size + 1):
            # 縦線
            arcade.draw_line(
                grid_start_x + i * cell_size,
                grid_start_y,
                grid_start_x + i * cell_size,
                grid_start_y + total_height,
                line_color,
                1,
            )
            # 横線
            arcade.draw_line(
                grid_start_x,
                grid_start_y + i * cell_size,
                grid_start_x + total_width,
                grid_start_y + i * cell_size,
                line_color,
                1,
            )

        # 話者位置を表示
        for speaker_id in range(self.game.num_speakers):
            speaker_pos = self.game.speaker_positions[speaker_id]
            x, y = speaker_pos
            cell_x = grid_start_x + x * cell_size + cell_size // 2
            cell_y = grid_start_y + y * cell_size + cell_size // 2

            if speaker_id == self.game.target_speaker:
                # 目標話者は大きな丸（目標色）
                arcade.draw_circle_filled(cell_x, cell_y, 8, SUCCESS_COLOR)
            else:
                # その他の話者は小さな丸（グレー）
                arcade.draw_circle_filled(cell_x, cell_y, 5, (150, 150, 150))

        # 正解マスを表示（目標話者の位置）
        target_speaker_pos = self.game.speaker_positions[self.game.target_speaker]
        target_x, target_y = target_speaker_pos
        target_cell_x = grid_start_x + target_x * cell_size + cell_size // 2
        target_cell_y = grid_start_y + target_y * cell_size + cell_size // 2
        arcade.draw_circle_outline(
            target_cell_x, target_cell_y, 12, GRID_SELECTED_COLOR, 2
        )

        # 話者位置にテキストラベルを追加
        label_y = grid_start_y + total_height + 30
        for speaker_id in range(self.game.num_speakers):
            speaker_name = self.get_speaker_name(speaker_id)
            if speaker_id == self.game.target_speaker:
                label_text = arcade.Text(
                    f"● {speaker_name} (目標)",
                    WIDTH // 2 + (speaker_id - 1) * 150,
                    label_y,
                    SUCCESS_COLOR,
                    FONT_SIZE_SMALL,
                    anchor_x="center",
                    anchor_y="top",
                )
            else:
                label_text = arcade.Text(
                    f"● {speaker_name}",
                    WIDTH // 2 + (speaker_id - 1) * 150,
                    label_y,
                    (150, 150, 150),
                    FONT_SIZE_SMALL,
                    anchor_x="center",
                    anchor_y="top",
                )
            label_text.draw()

    def on_key_press(self, key, modifiers):
        """キー入力処理"""
        if self.current_screen == "title":
            if key == arcade.key.ENTER:
                self.current_screen = "select"
            elif key == arcade.key.Q:
                self.is_running = False
                arcade.close_window()

        elif self.current_screen == "select":
            if key == arcade.key.KEY_1:
                self.select_grid_idx = 0
            elif key == arcade.key.KEY_2:
                self.select_grid_idx = 1
            elif key == arcade.key.KEY_3:
                self.select_grid_idx = 2
            elif key == arcade.key.Q:
                self.select_speaker_idx = max(0, self.select_speaker_idx - 1)
            elif key == arcade.key.W:
                self.select_speaker_idx = min(2, self.select_speaker_idx + 1)
            elif key == arcade.key.ENTER:
                # 難易度選択完了 → instruction画面へ
                self.selected_grid_size = GRID_SIZES[self.select_grid_idx]
                self.selected_num_speakers = NUM_SPEAKERS[self.select_speaker_idx]
                self.start_instruction()

        elif self.current_screen == "instruction":
            if key == arcade.key.ENTER:
                # ENTER to start game directly
                self.start_game()

        elif self.current_screen == "game":
            if key == arcade.key.UP:
                self.show_answer_dialog = False  # Close dialog if open
                self.game.move_player(0, 1)
                # Move Onlyモードの場合は自動的に次のターンへ
                if self.game.input_mode == "move_only":
                    self.start_game_turn()
            elif key == arcade.key.DOWN:
                self.show_answer_dialog = False
                self.game.move_player(0, -1)
                if self.game.input_mode == "move_only":
                    self.start_game_turn()
            elif key == arcade.key.LEFT:
                self.show_answer_dialog = False
                self.game.move_player(-1, 0)
                if self.game.input_mode == "move_only":
                    self.start_game_turn()
            elif key == arcade.key.RIGHT:
                self.show_answer_dialog = False
                self.game.move_player(1, 0)
                if self.game.input_mode == "move_only":
                    self.start_game_turn()
            elif key == arcade.key.ENTER:
                # ENTER キーで Answer/Skip ダイアログを表示
                if not self.show_answer_dialog:
                    self.show_answer_dialog = True
                else:
                    # ダイアログが既に表示されている場合は何もしない
                    pass
            elif key == arcade.key.Y:
                # Answer を選択
                if self.show_answer_dialog:
                    self.show_answer_dialog = False
                    self.handle_cell_confirm()
            elif key == arcade.key.N:
                # Skip を選択
                if self.show_answer_dialog:
                    self.show_answer_dialog = False
                    # スキップ：ターン数と訪問セルを記録
                    self.game.skip_turn()
                    print(f"スキップ (ターン数: {self.game.current_turn})")
                    # 次のターン開始
                    self.start_game_turn()
            elif key == arcade.key.SPACE:
                self.play_sample_voice()
            elif key == arcade.key.Q:
                self.is_running = False
                arcade.close_window()

        elif self.current_screen == "result":
            if key == arcade.key.ENTER:
                # 同じ難易度で再スタート（選択画面に戻らない）
                self.start_instruction()
            elif key == arcade.key.M:
                # 難易度（ルール）選択画面に戻る
                self.current_screen = "select"
            elif key == arcade.key.Q:
                self.is_running = False
                arcade.close_window()

    def start_instruction(self):
        """instruction画面を開始（サンプル再生）"""
        self.game = GameState(self.selected_grid_size, self.selected_num_speakers)
        self.game.input_mode = "move_and_confirm"  # Default mode
        self.target_speaker_name = self.get_speaker_name(self.game.target_speaker)

        self.last_feedback = None
        self.feedback_time = 0
        self.show_answer_dialog = False
        self.current_screen = "instruction"
        # サンプル音声を再生
        self.play_sample_voice()
        print(
            f"Instruction開始: {self.selected_grid_size}×{self.selected_grid_size}, {self.selected_num_speakers}人"
        )
        print(f"目標話者: {self.target_speaker_name}")

    def start_game(self):
        """実際のゲームを開始（ゲーム画面へ遷移）"""
        self.current_screen = "game"
        self.start_game_turn()  # ターン開始時の音声再生
        print(f"ゲーム開始: Mode={self.game.input_mode}")

    def start_game_turn(self):
        """ターン開始時の音声再生（全話者を同時にステレオ再生）"""
        if not self.game:
            return

        speakers_data = {}

        # ゲーム用のボイスを交互に選択（奇数ターンは voice_1、偶数ターンは voice_2）
        voice_type = "game_1" if self.game.current_turn % 2 == 0 else "game_2"

        # 全話者のボイスをロード
        for speaker_id in range(self.game.num_speakers):
            audio_data, sample_rate = sound_manager.load_voice_file(
                speaker_id, voice_type
            )
            if audio_data is not None:
                speakers_data[speaker_id] = (audio_data, sample_rate)

        # 全話者の音声をステレオで再生（プレイヤー位置を基準にパンニング）
        if speakers_data:
            sound_manager.play_multiple_speakers_stereo(
                speakers_data,
                self.game.speaker_positions,
                self.game.grid_size,
                self.game.target_speaker,
                self.game.current_pos,  # プレイヤーの現在位置を渡す
            )
            print(f"ターン {self.game.current_turn + 1}: 音声再生完了")

    def play_sample_voice(self):
        """サンプル音声再生（ヒント）"""
        if not self.game:
            return

        speaker_id = self.game.target_speaker
        speaker_name = self.get_speaker_name(speaker_id)

        audio_data, sample_rate = sound_manager.load_voice_file(speaker_id, "sample")

        if audio_data is not None:
            # ステレオでセンター再生(パンニングなし)
            sound_manager.play_voice_stereo(audio_data, sample_rate, 0.5, 0.5)
            print(f"サンプル再生: {speaker_name}")
        else:
            print(f"警告: {speaker_name} のサンプル音声が見つかりません")

    def handle_cell_confirm(self):
        """マス確定時の処理"""
        if not self.game:
            return

        is_correct = self.game.confirm_cell()

        if is_correct:
            print(f"正解! ターン数: {self.game.current_turn}")
            self.current_screen = "result"
        else:
            closest_id = self.game.get_closest_speaker()
            closest_name = self.get_speaker_name(closest_id)
            self.last_feedback = f"Wrong! {closest_name} is closest"
            self.feedback_time = 0
            print(
                f"不正解。{closest_name}が一番近い (残りライフ: {self.game.remaining_life})"
            )

            if self.game.is_game_over:
                self.current_screen = "result"
            else:
                # 次のターン開始
                self.start_game_turn()

    def get_speaker_name(self, speaker_id):
        """話者IDを名前に変換"""
        return (
            SPEAKER_NAMES[speaker_id] if speaker_id < len(SPEAKER_NAMES) else "Unknown"
        )


def main():
    """ゲーム開始"""
    try:
        app = SoundFairyGame()
        app.run()
        print("ゲーム終了")
    except Exception as e:
        import traceback

        print(f"ERROR: {e}")
        traceback.print_exc()
        with open("error.log", "w") as f:
            f.write(traceback.format_exc())


if __name__ == "__main__":
    main()
