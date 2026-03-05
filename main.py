import arcade
import numpy as np
import time
import threading
import queue
from config import WIDTH, HEIGHT, PLAYER_RADIUS, SCORE_MESSAGES, SCORE_TEXT_COLOR, STAR_TEXT_SIZE, DISTANCE_TEXT_SIZE, SAMPLE_RATE, MIN_FREQ, MAX_FREQ, MAX_DIST, AUDIO_TONE_DURATION
from game import GameState
import sound_manager


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

        # ターゲット範囲内フラグ
        self.near_target = False

        # スコア関連
        self.last_score = -1  # -1 = スコア未計算、0-5 = スコア値
        self.last_distance = 0.0  # クリック時の距離を保存

        # オーディオスレッド用
        self.audio_queue = queue.Queue(maxsize=1)  # 最新の周波数を保持
        self.audio_thread = None
        self.is_running = True

        # テキストオブジェクト（パフォーマンス向上）
        self.found_text = arcade.Text("Found!", WIDTH // 2, HEIGHT // 2, (255, 255, 100), 56,
                                       anchor_x="center", anchor_y="center")
        self.restart_text = arcade.Text("Press R to restart", WIDTH // 2, HEIGHT // 2 - 60,
                                        (200, 200, 200), 16, anchor_x="center", anchor_y="center")

        print("ゲーム開始")
        print("マウスを動かして目標を探してください")

        # オーディオスレッドを開始
        self.start_audio_thread()

    def start_audio_thread(self):
        """バックグラウンドでオーディオを再生するスレッドを開始"""
        def audio_worker():
            current_freq = 200  # デフォルト周波数
            last_freq = None
            last_play_time = 0  # 前回再生した時刻

            while self.is_running:
                # キューから最新の周波数を取得（ブロッキングなし）
                try:
                    current_freq = self.audio_queue.get(timeout=0.05)
                except queue.Empty:
                    pass  # キューが空の場合は前回の周波数を使用

                current_time = time.time()

                # 周波数が変わった、または前回再生後一定時間経過した場合のみ音を再生
                if (last_freq != current_freq or last_freq is None or
                    (current_time - last_play_time) >= AUDIO_TONE_DURATION):

                    left_vol, right_vol, _ = sound_manager.calculate_volumes(
                        self.game.player_pos, self.game.target_pos
                    )
                    sound_manager.play_stereo_sound(
                        current_freq, left_vol, right_vol, AUDIO_TONE_DURATION
                    )
                    last_freq = current_freq
                    last_play_time = current_time

                time.sleep(0.05)  # 50ms ごとにチェック

        self.audio_thread = threading.Thread(target=audio_worker, daemon=True)
        self.audio_thread.start()

    def on_draw(self):
        """画面を描画"""
        # 背景をクリア
        self.clear()

        # プレイヤーを描画（緑色の円 = マウスの位置）
        px, py = self.game.player_pos
        arcade.draw_circle_filled(px, py, PLAYER_RADIUS, (100, 255, 100))
        arcade.draw_circle_outline(px, py, PLAYER_RADIUS - 2, (150, 255, 150), 2)

        # ターゲット範囲内の視覚化フィードバック
        if self.near_target and not self.game.discovered:
            # ターゲット周辺をハイライト
            tx, ty = self.game.target_pos
            arcade.draw_circle_outline(tx, ty, 60, (255, 255, 100), 3)
            # テキスト表示
            prompt_text = arcade.Text("Click to confirm!", WIDTH // 2, HEIGHT - 40,
                                      (255, 255, 100), 20, anchor_x="center")
            prompt_text.draw()

        # クリア後の表示
        if self.game.discovered:
            # 発光アニメーション
            elapsed = (time.time() - self.start_time) * 1000
            glow_size = int(100 + 50 * np.sin(elapsed / 200))
            arcade.draw_circle_outline(px, py, glow_size, (255, 200, 100), 2)

            # テキスト表示
            self.found_text.draw()
            self.restart_text.draw()

            # スコア表示（画面下部）
            if self.last_score >= 0:
                # スター生成（★を繰り返す）
                star_display = "★" * self.last_score if self.last_score > 0 else "☆"
                message = SCORE_MESSAGES.get(self.last_score, "")

                # スコア表示テキスト
                score_text = arcade.Text(
                    f"{star_display} {message}",
                    WIDTH // 2,
                    50,
                    SCORE_TEXT_COLOR,
                    STAR_TEXT_SIZE,
                    anchor_x="center",
                    anchor_y="center",
                )
                score_text.draw()

                # 距離表示テキスト
                distance_text = arcade.Text(
                    f"({self.last_distance:.1f}px)",
                    WIDTH // 2,
                    20,
                    SCORE_TEXT_COLOR,
                    DISTANCE_TEXT_SIZE,
                    anchor_x="center",
                    anchor_y="center",
                )
                distance_text.draw()

    def on_update(self, delta_time):
        """ゲーム状態更新"""
        # マウス位置からプレイヤー位置を更新
        self.game.update_player_position_from_mouse(self.mouse_x, self.mouse_y)

        # ターゲット範囲内かチェック（視覚フィードバック用）
        self.near_target = self.game.is_near_target()

        # 軽量：周波数をキューに入れるだけ（オーディオスレッドで処理）
        if not self.game.discovered:
            dist = self.game.get_distance()
            freq = sound_manager.calculate_frequency(dist)
            try:
                self.audio_queue.put_nowait(freq)  # ブロッキングなし
            except queue.Full:
                pass  # キューが満杯の場合は無視（古い値は破棄）

    def on_mouse_motion(self, x, y, dx, dy):
        """マウス移動時の処理"""
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        """マウスクリック時の処理"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.near_target and not self.game.discovered:
                # ターゲット範囲内でのみクリア確定
                self.game.confirm_discovery()

                # スコア計算（クリア後）
                self.last_distance = self.game.get_distance()
                self.last_score = self.game.calculate_score_at_discovery()

                print(f"ターゲットをクリック確定しました！（精度: {self.last_distance:.1f}px）")
            elif not self.near_target and not self.game.discovered:
                # 範囲外クリック時の処理
                print("ターゲット範囲内ではありません")

    def on_key_press(self, key, modifiers):
        """キー押下時の処理"""
        # R キー: ゲーム再開
        if key == arcade.key.R:
            self.game.reset()
            self.start_time = time.time()
            self.last_score = -1  # スコアをリセット
            self.near_target = False  # 範囲内フラグもリセット
        # Q キー: 終了
        elif key == arcade.key.Q:
            self.is_running = False  # オーディオスレッドを停止
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



