# ===== ゲーム画面設定 =====
WIDTH = 960
HEIGHT = 720

# ===== グリッド設定 =====
GRID_SIZES = [3, 5, 10]
NUM_SPEAKERS = [1, 2, 3]

# グリッド表示設定
GRID_CELL_SIZE = 60
GRID_PADDING = 40
GRID_COLOR = (100, 100, 100)
GRID_SELECTED_COLOR = (200, 200, 0)
GRID_VISITED_COLOR = (150, 100, 100)

# ===== ゲーム設定 =====
MAX_LIFE = 3
SAMPLE_DURATION = 2.0
SPEECH_DURATION = 2.0
COUNTDOWN_DURATION = 3

# ===== 話者設定 =====
SPEAKER_NAMES = ["男の子", "女の子", "お兄さん"]

# ===== UI文字色設定 =====
TEXT_COLOR = (200, 200, 200)
TITLE_COLOR = (255, 255, 100)
ERROR_COLOR = (255, 100, 100)
SUCCESS_COLOR = (100, 255, 100)

FONT_SIZE_TITLE = 48
FONT_SIZE_BODY = 20
FONT_SIZE_SMALL = 16

# ===== 音声設定 =====
SAMPLE_RATE = 44100
VOICES_DIR = "voices"

# ===== DSP / 空間音響設定 (NEW) =====
ENABLE_DELAY = True        # やまびこ（反響）のON/OFFフラグ
FOOTSTEP_DURATION = 0.15   # 足音の長さ（秒）
DELAY_MS = 250             # ディレイ（反響）の遅延時間
DELAY_DECAY = 0.35         # ディレイの減衰率
LPF_BASE_FREQ = 400.0      # 最遠距離でのLPFカットオフ周波数
LPF_MAX_FREQ = 8000.0      # ゼロ距離でのLPFカットオフ周波数

# 従来周波数ベース設定（互換性用）
MIN_FREQ = 200
MAX_FREQ = 2000
MAX_DIST = 600