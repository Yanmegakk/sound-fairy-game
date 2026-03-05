import numpy as np
import scipy.signal as signal
import sounddevice as sd
from scipy.io import wavfile
from config import (
    SAMPLE_RATE, MIN_FREQ, MAX_FREQ, MAX_DIST, VOICES_DIR,
    FOOTSTEP_DURATION, ENABLE_DELAY, DELAY_MS, DELAY_DECAY, LPF_BASE_FREQ, LPF_MAX_FREQ
)
import os

_voice_cache = {}

def apply_lpf(audio_data, cutoff_freq, sample_rate):
    """ローパスフィルタ（空気吸収による高音域の減衰シミュレーション）"""
    nyquist = sample_rate / 2.0
    normal_cutoff = cutoff_freq / nyquist
    if normal_cutoff >= 1.0:
        return audio_data

    b, a = signal.butter(2, normal_cutoff, btype='low', analog=False)
    filtered = np.zeros_like(audio_data)
    
    filtered[:, 0] = signal.lfilter(b, a, audio_data[:, 0])
    if audio_data.shape[1] > 1:
        filtered[:, 1] = signal.lfilter(b, a, audio_data[:, 1])
    else:
        filtered[:, 1] = filtered[:, 0]
        
    return filtered

# --- 変更点 1: 足音を独立したSE再生関数に変更し、音量を戻す ---
def play_footstep_se():
    """足音のSEを単独で再生（やまびこ無し）"""
    sample_rate = SAMPLE_RATE
    samples = int(sample_rate * FOOTSTEP_DURATION)
    
    # 以前の音量・音色設定に戻す
    noise = np.random.normal(0, 0.5, samples).astype(np.float32)
    t = np.linspace(0, 1, samples, endpoint=False)
    envelope = np.exp(-15 * t)
    noise *= envelope
    
    b, a = signal.butter(2, 600.0 / (sample_rate / 2.0), btype='low')
    noise = signal.lfilter(b, a, noise)
    
    stereo_sound = np.column_stack((noise, noise)) * 0.4
    
    try:
        sd.play(stereo_sound, sample_rate, blocking=False)
    except Exception as e:
        print(f"Error playing footstep: {e}")

def load_voice_file(speaker_id, voice_type):
    cache_key = (speaker_id, voice_type)
    if cache_key in _voice_cache:
        return _voice_cache[cache_key]

    if voice_type == "sample":
        filename = f"sample_{speaker_id + 1}.wav"
    elif voice_type.startswith("game_"):
        game_num = voice_type.split("_")[1]
        filename = f"voice_{speaker_id + 1}_{game_num}.wav"
    else:
        return None, None

    filepath = os.path.join(VOICES_DIR, filename)

    try:
        if os.path.exists(filepath):
            sample_rate, audio_data = wavfile.read(filepath)
            if len(audio_data.shape) == 1:
                audio_data = np.column_stack((audio_data, audio_data))
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

def play_voice_stereo(audio_data, sample_rate, left_vol, right_vol):
    if audio_data is None: return
    try:
        left_channel = audio_data[:, 0] * left_vol
        right_channel = audio_data[:, 1] * right_vol if audio_data.shape[1] > 1 else left_channel * right_vol
        stereo_sound = np.column_stack((left_channel, right_channel))
        sd.play(stereo_sound, sample_rate, blocking=False)
    except Exception as e:
        print(f"Error playing stereo voice: {e}")

# --- 変更点 2: 足音のフラグとミックス処理を削除 ---
def play_multiple_speakers_stereo(speakers_data, speaker_positions, grid_size, target_speaker_id, player_pos=(0,0), player_facing=(0, 1)):
    """全話者の音声をミックスし、向き・LPF・ディレイを統合して再生"""
    if not speakers_data: return

    sample_rate = None
    max_length = 0
    for speaker_id, (audio_data, sr) in speakers_data.items():
        if audio_data is not None:
            if sample_rate is None: sample_rate = sr
            max_length = max(max_length, len(audio_data))
    if sample_rate is None or max_length == 0: return

    mixed_left = np.zeros(max_length)
    mixed_right = np.zeros(max_length)

    for speaker_id, (audio_data, sr) in speakers_data.items():
        if audio_data is None: continue

        speaker_pos = speaker_positions.get(speaker_id, (grid_size // 2, grid_size // 2))
        dx = speaker_pos[0] - player_pos[0]
        dy = speaker_pos[1] - player_pos[1]

        fx, fy = player_facing
        rx, ry = fy, -fx 
        
        local_x = dx * rx + dy * ry
        local_y = dx * fx + dy * fy

        pan = local_x / (grid_size / 2.0)
        pan = np.clip(pan, -1.0, 1.0)

        distance = np.sqrt(dx ** 2 + dy ** 2)
        max_distance = np.sqrt(2) * (grid_size / 2.0)
        distance_factor = max(0.0, 1.0 - distance / max_distance) if max_distance > 0 else 1.0

        left_vol = (1.0 - pan) / 2.0 * distance_factor
        right_vol = (1.0 + pan) / 2.0 * distance_factor

        if speaker_id != target_speaker_id:
            left_vol *= 0.7
            right_vol *= 0.7

        cutoff = LPF_BASE_FREQ + (LPF_MAX_FREQ - LPF_BASE_FREQ) * distance_factor
        processed_audio = apply_lpf(audio_data, cutoff, sr)

        audio_length = len(processed_audio)
        padded_left = np.zeros(max_length)
        padded_right = np.zeros(max_length)

        padded_left[:audio_length] = processed_audio[:, 0] * left_vol
        padded_right[:audio_length] = processed_audio[:, 1] * right_vol

        mixed_left += padded_left
        mixed_right += padded_right

    if ENABLE_DELAY:
        delay_samples = int(sample_rate * (DELAY_MS / 1000.0))
        out_length = max_length + delay_samples

        final_left = np.zeros(out_length)
        final_right = np.zeros(out_length)

        final_left[:max_length] += mixed_left
        final_right[:max_length] += mixed_right

        final_left[delay_samples:] += mixed_left * DELAY_DECAY
        final_right[delay_samples:] += mixed_right * DELAY_DECAY
    else:
        final_left = mixed_left
        final_right = mixed_right

    max_val = max(np.max(np.abs(final_left)), np.max(np.abs(final_right)))
    if max_val > 1.0:
        final_left /= max_val
        final_right /= max_val

    try:
        stereo_sound = np.column_stack((final_left, final_right))
        sd.play(stereo_sound, sample_rate, blocking=False)
    except Exception as e:
        print(f"Error playing mixed speakers: {e}")