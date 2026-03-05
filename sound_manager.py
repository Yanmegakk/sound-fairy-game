import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from config import SAMPLE_RATE, MIN_FREQ, MAX_FREQ, MAX_DIST, VOICES_DIR
import os


# キャッシュ：読み込んだWAVファイル
_voice_cache = {}


def load_voice_file(speaker_id, voice_type):
    """
    WAVファイルを読み込む（キャッシュ済み）

    Args:
        speaker_id (int): 話者ID (0, 1, 2)
        voice_type (str): "sample" または "game_1" または "game_2"

    Returns:
        tuple: (audio_data: np.ndarray, sample_rate: int) or (None, None) if failed
    """
    cache_key = (speaker_id, voice_type)

    if cache_key in _voice_cache:
        return _voice_cache[cache_key]

    # ファイル名パターン
    # sample: sample_1.wav, sample_2.wav, sample_3.wav
    # game: voice_1_1.wav, voice_1_2.wav, voice_2_1.wav, etc.
    if voice_type == "sample":
        filename = f"sample_{speaker_id + 1}.wav"
    elif voice_type.startswith("game_"):
        game_num = voice_type.split("_")[1]  # "1" or "2"
        filename = f"voice_{speaker_id + 1}_{game_num}.wav"
    else:
        return None, None

    filepath = os.path.join(VOICES_DIR, filename)

    try:
        if os.path.exists(filepath):
            sample_rate, audio_data = wavfile.read(filepath)
            # ステレオに変換（モノラルの場合）
            if len(audio_data.shape) == 1:
                audio_data = np.column_stack((audio_data, audio_data))
            # float32に正規化
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32) / 32768.0
            _voice_cache[cache_key] = (audio_data, sample_rate)
            return audio_data, sample_rate
        else:
            print(f"Warning: Voice file not found: {filepath}")
            _voice_cache[cache_key] = (None, None)
            return None, None
    except Exception as e:
        print(f"Error loading voice file {filepath}: {e}")
        _voice_cache[cache_key] = (None, None)
        return None, None


def calculate_speaker_panning(speaker_pos, grid_size):
    """
    話者のグリッド位置からステレオパンニングを計算

    Args:
        speaker_pos (tuple): 話者のグリッド位置 (x, y)
        grid_size (int): グリッドサイズ

    Returns:
        tuple: (left_vol, right_vol, distance_factor)
               distance_factor: グリッド内の距離に基づく音量減衰（0.0～1.0）
    """
    # グリッド中央からの距離で音量を計算
    center = grid_size / 2.0
    x, y = speaker_pos

    # X位置（左右のパンニング）：-1.0（左）～ 1.0（右）
    pan = (x - center) / (grid_size / 2.0)
    pan = np.clip(pan, -1.0, 1.0)

    # Y位置（上下）：グリッド中央が最大音量、端ほど小さい
    distance = np.sqrt((x - center) ** 2 + (y - center) ** 2)
    max_distance = np.sqrt(2) * (grid_size / 2.0)
    distance_factor = max(0.0, 1.0 - distance / max_distance) if max_distance > 0 else 1.0

    # ステレオ左右の音量を計算
    # パンニング：-1（左100%）→ 0（中央50%-50%）→ 1（右100%）
    left_vol = (1.0 - pan) / 2.0 * distance_factor
    right_vol = (1.0 + pan) / 2.0 * distance_factor

    return left_vol, right_vol, distance_factor


def play_voice_stereo(audio_data, sample_rate, left_vol, right_vol):
    """
    ボイスをステレオパンニング付きで再生

    Args:
        audio_data (np.ndarray): 音声データ（ステレオ）
        sample_rate (int): サンプルレート
        left_vol (float): 左チャンネルの音量（0.0～1.0）
        right_vol (float): 右チャンネルの音量（0.0～1.0）
    """
    if audio_data is None:
        return

    try:
        # 音格チャンネルに音量を適用
        left_channel = audio_data[:, 0] * left_vol
        right_channel = audio_data[:, 1] * right_vol if audio_data.shape[1] > 1 else left_channel * right_vol

        stereo_sound = np.column_stack((left_channel, right_channel))
        sd.play(stereo_sound, sample_rate, blocking=False)
    except Exception as e:
        print(f"Error playing stereo voice: {e}")


def play_multiple_speakers_stereo(speakers_data, speaker_positions, grid_size, target_speaker_id, player_pos=None):
    """
    複数話者の音声をステレオで同時再生

    Args:
        speakers_data (dict): {speaker_id: (audio_data, sample_rate), ...}
        speaker_positions (dict): {speaker_id: (x, y), ...}
        grid_size (int): グリッドサイズ
        target_speaker_id (int): ハイライトする（最大音量）話者ID
        player_pos (tuple): プレイヤーの位置 (x, y)。Noneの場合はグリッド中央が基準
    """
    if not speakers_data:
        return

    # プレイヤー位置を設定（デフォルトはグリッド中央）
    if player_pos is None:
        player_pos = (grid_size / 2.0, grid_size / 2.0)

    # サンプルレートを取得（全て同じと仮定）
    sample_rate = None
    max_length = 0

    for speaker_id, (audio_data, sr) in speakers_data.items():
        if audio_data is not None:
            if sample_rate is None:
                sample_rate = sr
            max_length = max(max_length, len(audio_data))

    if sample_rate is None or max_length == 0:
        return

    # 全話者の音声を合成
    mixed_left = np.zeros(max_length)
    mixed_right = np.zeros(max_length)

    for speaker_id, (audio_data, sr) in speakers_data.items():
        if audio_data is None:
            continue

        # パンニングを計算（プレイヤー位置を基準）
        speaker_pos = speaker_positions.get(speaker_id, (grid_size // 2, grid_size // 2))

        # スピーカーから見たプレイヤーへの相対位置
        dx = speaker_pos[0] - player_pos[0]
        dy = speaker_pos[1] - player_pos[1]

        # X位置（左右のパンニング）：-1.0（左）～ 1.0（右）
        # グリッドの最大幅で正規化
        pan = dx / (grid_size / 2.0)
        pan = np.clip(pan, -1.0, 1.0)

        # Y位置（上下）：距離が近いほど大きい音量
        distance = np.sqrt(dx ** 2 + dy ** 2)
        max_distance = np.sqrt(2) * (grid_size / 2.0)
        distance_factor = max(0.0, 1.0 - distance / max_distance) if max_distance > 0 else 1.0

        # ステレオ左右の音量を計算
        # パンニング：-1（左100%）→ 0（中央50%-50%）→ 1（右100%）
        left_vol = (1.0 - pan) / 2.0 * distance_factor
        right_vol = (1.0 + pan) / 2.0 * distance_factor

        # 目標話者は最大音量、その他は減衰
        if speaker_id != target_speaker_id:
            left_vol *= 0.7
            right_vol *= 0.7

        # 長さを合わせる
        audio_length = len(audio_data)
        padded_left = np.zeros(max_length)
        padded_right = np.zeros(max_length)

        padded_left[:audio_length] = audio_data[:, 0] * left_vol
        if audio_data.shape[1] > 1:
            padded_right[:audio_length] = audio_data[:, 1] * right_vol
        else:
            padded_right[:audio_length] = audio_data[:, 0] * right_vol

        mixed_left += padded_left
        mixed_right += padded_right

    # 正規化（クリップ防止）
    max_val = max(np.max(np.abs(mixed_left)), np.max(np.abs(mixed_right)))
    if max_val > 1.0:
        mixed_left /= max_val
        mixed_right /= max_val

    # 再生
    try:
        stereo_sound = np.column_stack((mixed_left, mixed_right))
        sd.play(stereo_sound, sample_rate, blocking=False)
    except Exception as e:
        print(f"Error playing mixed speakers: {e}")


# ===== 従来関数（互換性用） =====

def generate_tone(freq, duration):
    """指定された周波数の正弦波を生成"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tone = np.sin(freq * t * 2 * np.pi)
    return tone.astype(np.float32)


def make_stereo(sound, left_vol, right_vol):
    """モノラル音をステレオに変換"""
    return np.column_stack((sound * left_vol, sound * right_vol))


def calculate_frequency(dist):
    """距離から周波数を計算（近いほど周波数が高くなる）"""
    ratio = max(0.0, 1.0 - dist / MAX_DIST)
    freq = MIN_FREQ + (MAX_FREQ - MIN_FREQ) * ratio
    return freq


def calculate_volumes(player_pos, target_pos):
    """距離とパンニングから左右の音量を計算"""
    diff = target_pos - player_pos
    dist = np.linalg.norm(diff)

    # 距離に応じた音量（近いほど大きい）
    volume = max(0.0, 1.0 - dist / MAX_DIST)

    # 左右位置に応じたパンニング
    pan = diff[0] / MAX_DIST
    pan = np.clip(pan, -1, 1)

    # ステレオ左右の音量
    left_vol = volume * (1 - pan) / 2
    right_vol = volume * (1 + pan) / 2

    return left_vol, right_vol, dist


def play_stereo_sound(freq, left_vol, right_vol, duration=0.15):
    """ステレオ音を再生"""
    try:
        tone = generate_tone(freq, duration)
        stereo_sound = make_stereo(tone, left_vol, right_vol)
        sd.play(stereo_sound, SAMPLE_RATE, blocking=False)
    except Exception:
        pass
