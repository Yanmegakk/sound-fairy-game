import numpy as np
import random
from config import GRID_SIZES, NUM_SPEAKERS, MAX_LIFE

class GameState:
    """ターンベース・グリッド探索ゲームの状態管理"""

    def __init__(self, grid_size, num_speakers):
        self.grid_size = grid_size
        self.num_speakers = num_speakers
        self.current_turn = 0
        self.remaining_life = MAX_LIFE
        self.is_game_over = False
        self.is_won = False

        self.target_speaker = np.random.randint(0, num_speakers)
        self.target_pos = (
            np.random.randint(0, grid_size),
            np.random.randint(0, grid_size)
        )
        self.speaker_positions = self._generate_speaker_positions()

        # プレイヤー位置と向き
        self.current_pos = (grid_size // 2, grid_size // 2)
        self.facing_dir = (0, 1)  # デフォルトは上向き (dx=0, dy=1)
        self.visited_cells = set()

        self.input_mode = "move_only"

    def _generate_speaker_positions(self):
        positions = {}
        available_cells = [(x, y) for x in range(self.grid_size) for y in range(self.grid_size)]
        for speaker_id in range(self.num_speakers):
            cell = random.choice(available_cells)
            positions[speaker_id] = cell
            available_cells.remove(cell)
        return positions

    def move_player(self, dx, dy):
        # 向きを更新（移動した方向を向く）
        if dx != 0 or dy != 0:
            self.facing_dir = (dx, dy)
            
        new_x = max(0, min(self.current_pos[0] + dx, self.grid_size - 1))
        new_y = max(0, min(self.current_pos[1] + dy, self.grid_size - 1))
        self.current_pos = (new_x, new_y)

    def change_facing(self, dx, dy):
        """プレイヤーの向き（視点）だけを変更する"""
        if dx != 0 or dy != 0:
            self.facing_dir = (dx, dy)

    def confirm_cell(self):
        self.visited_cells.add(self.current_pos)
        target_speaker_pos = self.speaker_positions[self.target_speaker]
        if self.current_pos == target_speaker_pos:
            self.is_game_over = True
            self.is_won = True
            self.current_turn += 1
            return True
        else:
            self.remaining_life -= 1
            self.current_turn += 1
            if self.remaining_life <= 0:
                self.is_game_over = True
                self.is_won = False
            return False

    def skip_turn(self):
        self.visited_cells.add(self.current_pos)
        self.current_turn += 1

    def get_closest_speaker(self):
        min_distance = float('inf')
        closest_speaker = 0
        for speaker_id, speaker_pos in self.speaker_positions.items():
            distance = abs(self.current_pos[0] - speaker_pos[0]) + abs(self.current_pos[1] - speaker_pos[1])
            if distance < min_distance:
                min_distance = distance
                closest_speaker = speaker_id
        return closest_speaker