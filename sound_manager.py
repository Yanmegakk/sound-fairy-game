import numpy as np
import sounddevice as sd
from config import SAMPLE_RATE, MIN_FREQ, MAX_FREQ, MAX_DIST


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


