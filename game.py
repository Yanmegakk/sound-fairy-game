import numpy as np
import random
from config import GRID_SIZES, NUM_SPEAKERS, MAX_LIFE


class GameState:
    """ターンベース・グリッド探索ゲームの状態管理"""

    def __init__(self, grid_size, num_speakers):
        """
        ゲーム状態を初期化

        Args:
            grid_size: グリッドサイズ (3, 5, または 10)
            num_speakers: 話者数 (1, 2, または 3)
        """
        self.grid_size = grid_size
        self.num_speakers = num_speakers

        # ゲーム状態
        self.current_turn = 0
        self.remaining_life = MAX_LIFE
        self.is_game_over = False
        self.is_won = False

        # 目標話者とマス
        self.target_speaker = np.random.randint(0, num_speakers)
        self.target_pos = (
            np.random.randint(0, grid_size),
            np.random.randint(0, grid_size)
        )

        # 話者の位置（ランダム配置、重複なし）
        self.speaker_positions = self._generate_speaker_positions()

        # プレイヤー位置（グリッド中央から開始）
        self.current_pos = (grid_size // 2, grid_size // 2)
        self.visited_cells = set()

        # ゲーム中の操作モード: "move_only" (移動のみ) または "move_and_confirm" (移動+確定)
        self.input_mode = "move_only"  # デフォルト

    def _generate_speaker_positions(self):
        """
        話者をグリッド内にランダム配置（重複なし）

        Returns:
            dict: {speaker_id: (x, y), ...}
        """
        positions = {}
        available_cells = [
            (x, y) for x in range(self.grid_size) for y in range(self.grid_size)
        ]

        for speaker_id in range(self.num_speakers):
            # ランダムにセルを選択
            cell = random.choice(available_cells)
            positions[speaker_id] = cell
            available_cells.remove(cell)

        return positions

    def move_player(self, dx, dy):
        """
        プレイヤーを移動（グリッド境界内）

        Args:
            dx: X方向の移動 (-1, 0, または 1)
            dy: Y方向の移動 (-1, 0, または 1)
        """
        new_x = max(0, min(self.current_pos[0] + dx, self.grid_size - 1))
        new_y = max(0, min(self.current_pos[1] + dy, self.grid_size - 1))
        self.current_pos = (new_x, new_y)

    def confirm_cell(self):
        """
        現在のマスを確定して判定

        Returns:
            bool: Trueなら正解、Falseなら不正解
        """
        self.visited_cells.add(self.current_pos)

        # 目標話者がいるマスに到達したか判定
        target_speaker_pos = self.speaker_positions[self.target_speaker]
        if self.current_pos == target_speaker_pos:
            # 正解
            self.is_game_over = True
            self.is_won = True
            self.current_turn += 1
            return True
        else:
            # 不正解
            self.remaining_life -= 1
            self.current_turn += 1

            if self.remaining_life <= 0:
                self.is_game_over = True
                self.is_won = False

            return False

    def skip_turn(self):
        """スキップターン（確定なし、ターン数と訪問セル記録のみ）"""
        self.visited_cells.add(self.current_pos)
        self.current_turn += 1

    def get_closest_speaker(self):
        """
        不正解時に最も近い話者を計算

        Returns:
            int: 最も近い話者のID (0, 1, または 2)
        """
        min_distance = float('inf')
        closest_speaker = 0

        for speaker_id, speaker_pos in self.speaker_positions.items():
            # Manhattan距離で計算
            distance = abs(self.current_pos[0] - speaker_pos[0]) + \
                      abs(self.current_pos[1] - speaker_pos[1])

            if distance < min_distance:
                min_distance = distance
                closest_speaker = speaker_id

        return closest_speaker

    def get_all_speaker_distances(self):
        """
        全話者への距離を取得

        Returns:
            dict: {speaker_id: distance, ...}
        """
        distances = {}
        for speaker_id, speaker_pos in self.speaker_positions.items():
            distance = abs(self.current_pos[0] - speaker_pos[0]) + \
                      abs(self.current_pos[1] - speaker_pos[1])
            distances[speaker_id] = distance

        return distances
