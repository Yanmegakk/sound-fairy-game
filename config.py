# ===== ゲーム画面設定 =====
WIDTH = 960
HEIGHT = 720

# ===== グリッド設定 =====
GRID_SIZES = [3, 5, 10]
NUM_SPEAKERS = [1, 2, 3]

# グリッド表示設定
GRID_CELL_SIZE = 60          # 1マスのピクセルサイズ
GRID_PADDING = 40            # グリッド外側のパディング
GRID_COLOR = (100, 100, 100)
GRID_SELECTED_COLOR = (200, 200, 0)    # 選択中のマス（黄色）
GRID_VISITED_COLOR = (150, 100, 100)   # 訪問済みのマス（茶色）

# ===== ゲーム設定 =====
MAX_LIFE = 3
SAMPLE_DURATION = 2.0       # サンプル音声の長さ（秒）
SPEECH_DURATION = 2.0       # ゲーム中の音声の長さ（秒）
COUNTDOWN_DURATION = 3      # カウントダウン時間（秒）

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
SAMPLE_RATE = 44100        # サンプリングレート
VOICES_DIR = "voices"      # 音声ファイルディレクトリ

# 従来周波数ベース設定（互換性用）
MIN_FREQ = 200             # 最小周波数（Hz）
MAX_FREQ = 2000            # 最大周波数（Hz）
MAX_DIST = 600             # 最大探知距離（px）
