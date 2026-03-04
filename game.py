import numpy as np
import arcade
from config import WIDTH, HEIGHT, DISCOVERY_DIST


class GameState:
    """ゲームの状態を管理するクラス"""

    def __init__(self):
        # プレイヤーの開始位置（マウス位置から更新）
        self.player_pos = np.array([WIDTH // 2, HEIGHT // 2], dtype=float)

        # ターゲットのランダムな位置
        self.target_pos = np.array(
            [
                np.random.randint(50, WIDTH - 50),
                np.random.randint(50, HEIGHT - 50),
            ],
            dtype=float,
        )

        # ゲーム状態
        self.discovered = False

    def update_player_position_from_mouse(self, mouse_x, mouse_y):
        """マウス位置からプレイヤー位置を更新"""
        self.player_pos[0] = np.clip(mouse_x, 0, WIDTH)
        self.player_pos[1] = np.clip(mouse_y, 0, HEIGHT)

    def get_distance(self):
        """プレイヤーとターゲット間の距離を取得"""
        return np.linalg.norm(self.target_pos - self.player_pos)

    def check_discovery(self):
        """ターゲット発見の判定"""
        dist = self.get_distance()
        if not self.discovered and dist < DISCOVERY_DIST:
            self.discovered = True
            return True
        return False

    def reset(self):
        """ゲームをリセット"""
        self.__init__()

