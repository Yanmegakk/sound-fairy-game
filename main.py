import arcade
import numpy as np
import time
from config import WIDTH, HEIGHT, PLAYER_RADIUS
from game import GameState


class SoundFairyGame(arcade.Window):
    """Sound Fairy Game - Simple Version"""

    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Sound Fairy Game")

        # ゲーム状態
        self.game = GameState()

        # マウス位置
        self.mouse_x = 0
        self.mouse_y = 0

        # アニメーション時間
        self.start_time = time.time()

        # 背景色
        arcade.set_background_color((20, 20, 30))

        # テキストオブジェクト（パフォーマンス向上）
        self.found_text = arcade.Text("Found!", WIDTH // 2, HEIGHT // 2, (255, 255, 100), 56,
                                       anchor_x="center", anchor_y="center")
        self.restart_text = arcade.Text("Press R to restart", WIDTH // 2, HEIGHT // 2 - 60,
                                        (200, 200, 200), 16, anchor_x="center", anchor_y="center")

        print("ゲーム開始")
        print("マウスを動かして目標を探してください")

    def on_draw(self):
        """画面を描画"""
        # 背景をクリア
        self.clear()

        # プレイヤーを描画（緑色の円 = マウスの位置）
        px, py = self.game.player_pos
        arcade.draw_circle_filled(px, py, PLAYER_RADIUS, (100, 255, 100))
        arcade.draw_circle_outline(px, py, PLAYER_RADIUS - 2, (150, 255, 150), 2)

        # 発見判定
        dist = self.game.get_distance()
        discovered = self.game.check_discovery()

        # 発見時の表示
        if self.game.discovered:
            # 発光アニメーション
            elapsed = (time.time() - self.start_time) * 1000
            glow_size = int(100 + 50 * np.sin(elapsed / 200))
            arcade.draw_circle_outline(px, py, glow_size, (255, 200, 100), 2)

            # テキスト表示
            self.found_text.draw()
            self.restart_text.draw()

    def on_update(self, delta_time):
        """ゲーム状態更新"""
        # マウス位置からプレイヤー位置を更新
        self.game.update_player_position_from_mouse(self.mouse_x, self.mouse_y)

        # 発見判定
        self.game.check_discovery()

    def on_mouse_motion(self, x, y, dx, dy):
        """マウス移動時の処理"""
        self.mouse_x = x
        self.mouse_y = y

    def on_key_press(self, key, modifiers):
        """キー押下時の処理"""
        # R キー: ゲーム再開
        if key == arcade.key.R:
            self.game.reset()
            self.start_time = time.time()
        # Q キー: 終了
        elif key == arcade.key.Q:
            arcade.close_window()


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



