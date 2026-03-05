# ===== ゲーム画面設定 =====
WIDTH = 800
HEIGHT = 600

# ===== プレイヤー設定 =====
PLAYER_RADIUS = 8

# ===== ゲーム設定 =====
DISCOVERY_DIST = 50  # 発見と判定する距離

# ===== スター評価設定 =====
STAR_THRESHOLDS = {
    5: 10,    # ★★★★★ 10px以内
    4: 20,    # ★★★★ 20px以内
    3: 30,    # ★★★ 30px以内
    2: 40,    # ★★ 40px以内
    1: 50,    # ★ 50px以内
}

SCORE_MESSAGES = {
    5: "Perfect!",
    4: "Great!",
    3: "Good",
    2: "Fair",
    1: "OK",
    0: "Missed!",
}

# 表示色設定
SCORE_TEXT_COLOR = (255, 255, 100)
STAR_TEXT_SIZE = 24
DISTANCE_TEXT_SIZE = 16

# ===== 音声設定 =====
SAMPLE_RATE = 44100        # サンプリングレート
MIN_FREQ = 200             # 最小周波数（Hz）
MAX_FREQ = 2000            # 最大周波数（Hz）
MAX_DIST = 600             # 最大探知距離（px）
AUDIO_TONE_DURATION = 0.01  # トーン継続時間（秒）