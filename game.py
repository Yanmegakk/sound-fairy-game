import numpy as np
import arcade
from config import WIDTH, HEIGHT, DISCOVERY_DIST, STAR_THRESHOLDS


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
        """ターゲット発見の判定（廃止予定：後方互換性のため保持）"""
        # 自動判定は行わず、何もしない
        return False

    def is_near_target(self):
        """ターゲット範囲内にいるかを判定"""
        dist = self.get_distance()
        return dist < DISCOVERY_DIST

    def confirm_discovery(self):
        """マウスクリック時にクリアを確定"""
        if not self.discovered:
            self.discovered = True
            return True
        return False

    def calculate_score_at_discovery(self):
        """クリック時の距離に基づいてスコアを計算"""
        if not self.discovered:
            return 0

        dist = self.get_distance()

        # 距離に応じてスター数を判定
        for stars in range(5, 0, -1):
            if dist <= STAR_THRESHOLDS[stars]:
                return stars

        return 0  # 範囲外（51px以上）

    def reset(self):
        """ゲームをリセット"""
        self.__init__()

