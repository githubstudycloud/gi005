"""
音频预处理工具

提供音频降噪、增强、格式转换等功能。
"""

import os
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Union
import tempfile


def load_audio(
    audio_path: str,
    target_sr: int = 22050,
    mono: bool = True
) -> Tuple[np.ndarray, int]:
    """
    加载音频文件

    Args:
        audio_path: 音频路径
        target_sr: 目标采样率
        mono: 是否转为单声道

    Returns:
        (音频数据, 采样率)
    """
    try:
        import librosa
        audio, sr = librosa.load(audio_path, sr=target_sr, mono=mono)
        return audio, sr
    except ImportError:
        import soundfile as sf
        audio, sr = sf.read(audio_path)
        if mono and len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        return audio, sr


def save_audio(
    audio: np.ndarray,
    output_path: str,
    sample_rate: int = 22050
) -> str:
    """
    保存音频文件

    Args:
        audio: 音频数据
        output_path: 输出路径
        sample_rate: 采样率

    Returns:
        输出文件路径
    """
    import soundfile as sf
    sf.write(output_path, audio, sample_rate)
    return output_path


def normalize_audio(
    audio: np.ndarray,
    target_db: float = -20.0
) -> np.ndarray:
    """
    音频响度归一化

    Args:
        audio: 音频数据
        target_db: 目标响度 (dB)

    Returns:
        归一化后的音频
    """
    # 计算当前 RMS
    rms = np.sqrt(np.mean(audio ** 2))
    if rms == 0:
        return audio

    # 计算目标 RMS
    target_rms = 10 ** (target_db / 20)

    # 归一化
    normalized = audio * (target_rms / rms)

    # 防止削波
    max_val = np.max(np.abs(normalized))
    if max_val > 0.99:
        normalized = normalized * (0.99 / max_val)

    return normalized


def remove_silence(
    audio: np.ndarray,
    sample_rate: int = 22050,
    top_db: int = 30,
    min_silence_duration: float = 0.5
) -> np.ndarray:
    """
    移除音频中的静音段

    Args:
        audio: 音频数据
        sample_rate: 采样率
        top_db: 静音阈值 (dB)
        min_silence_duration: 最小静音时长 (秒)

    Returns:
        处理后的音频
    """
    try:
        import librosa
        # 检测非静音区间
        intervals = librosa.effects.split(
            audio,
            top_db=top_db,
            frame_length=2048,
            hop_length=512
        )

        # 合并非静音片段
        if len(intervals) == 0:
            return audio

        non_silent = []
        for start, end in intervals:
            non_silent.append(audio[start:end])

        return np.concatenate(non_silent)

    except ImportError:
        # 简单的静音移除实现
        threshold = 0.01
        mask = np.abs(audio) > threshold
        return audio[mask]


def denoise_audio(
    audio: np.ndarray,
    sample_rate: int = 22050,
    method: str = "spectral_gating"
) -> np.ndarray:
    """
    音频降噪

    Args:
        audio: 音频数据
        sample_rate: 采样率
        method: 降噪方法 (spectral_gating, wiener)

    Returns:
        降噪后的音频
    """
    if method == "spectral_gating":
        return _spectral_gating_denoise(audio, sample_rate)
    elif method == "wiener":
        return _wiener_denoise(audio, sample_rate)
    else:
        return audio


def _spectral_gating_denoise(
    audio: np.ndarray,
    sample_rate: int,
    noise_reduce_factor: float = 0.8
) -> np.ndarray:
    """
    频谱门控降噪

    基于噪声估计的频谱减法
    """
    try:
        import librosa

        # STFT
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        phase = np.angle(stft)

        # 估计噪声频谱（使用前几帧）
        noise_frames = min(10, magnitude.shape[1] // 10)
        noise_estimate = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)

        # 频谱减法
        magnitude_denoised = np.maximum(
            magnitude - noise_reduce_factor * noise_estimate,
            0.0
        )

        # 重建
        stft_denoised = magnitude_denoised * np.exp(1j * phase)
        audio_denoised = librosa.istft(stft_denoised)

        return audio_denoised

    except ImportError:
        return audio


def _wiener_denoise(
    audio: np.ndarray,
    sample_rate: int
) -> np.ndarray:
    """
    维纳滤波降噪
    """
    try:
        from scipy.signal import wiener
        return wiener(audio)
    except ImportError:
        return audio


def enhance_audio(
    audio: np.ndarray,
    sample_rate: int = 22050,
    enhance_bass: bool = False,
    enhance_clarity: bool = True
) -> np.ndarray:
    """
    音频增强

    Args:
        audio: 音频数据
        sample_rate: 采样率
        enhance_bass: 增强低频
        enhance_clarity: 增强清晰度

    Returns:
        增强后的音频
    """
    try:
        from scipy.signal import butter, filtfilt

        result = audio.copy()

        if enhance_clarity:
            # 高通滤波去除低频噪声
            b, a = butter(4, 80 / (sample_rate / 2), btype='high')
            result = filtfilt(b, a, result)

            # 轻微高频增强
            b, a = butter(2, 3000 / (sample_rate / 2), btype='high')
            high_freq = filtfilt(b, a, result)
            result = result + 0.1 * high_freq

        if enhance_bass:
            # 低频增强
            b, a = butter(2, 200 / (sample_rate / 2), btype='low')
            low_freq = filtfilt(b, a, result)
            result = result + 0.2 * low_freq

        # 归一化
        result = normalize_audio(result)

        return result

    except ImportError:
        return audio


def resample_audio(
    audio: np.ndarray,
    orig_sr: int,
    target_sr: int
) -> np.ndarray:
    """
    重采样音频

    Args:
        audio: 音频数据
        orig_sr: 原始采样率
        target_sr: 目标采样率

    Returns:
        重采样后的音频
    """
    if orig_sr == target_sr:
        return audio

    try:
        import librosa
        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    except ImportError:
        from scipy.signal import resample
        num_samples = int(len(audio) * target_sr / orig_sr)
        return resample(audio, num_samples)


def trim_audio(
    audio: np.ndarray,
    sample_rate: int = 22050,
    max_duration: float = 30.0,
    min_duration: float = 1.0
) -> np.ndarray:
    """
    裁剪音频到指定时长范围

    Args:
        audio: 音频数据
        sample_rate: 采样率
        max_duration: 最大时长（秒）
        min_duration: 最小时长（秒）

    Returns:
        裁剪后的音频
    """
    duration = len(audio) / sample_rate

    if duration > max_duration:
        # 截取前 max_duration 秒
        max_samples = int(max_duration * sample_rate)
        audio = audio[:max_samples]

    if duration < min_duration:
        # 填充静音
        min_samples = int(min_duration * sample_rate)
        padding = np.zeros(min_samples - len(audio))
        audio = np.concatenate([audio, padding])

    return audio


class AudioProcessor:
    """
    音频处理器类

    封装所有音频处理功能，提供统一的接口。
    """

    def __init__(
        self,
        target_sr: int = 22050,
        normalize_db: float = -20.0
    ):
        """
        初始化处理器

        Args:
            target_sr: 目标采样率
            normalize_db: 归一化响度
        """
        self.target_sr = target_sr
        self.normalize_db = normalize_db

    def process(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        denoise: bool = True,
        remove_silence: bool = True,
        enhance: bool = True,
        normalize: bool = True,
        max_duration: float = 30.0
    ) -> str:
        """
        完整处理音频

        Args:
            audio_path: 输入音频路径
            output_path: 输出路径（可选）
            denoise: 是否降噪
            remove_silence: 是否移除静音
            enhance: 是否增强
            normalize: 是否归一化
            max_duration: 最大时长

        Returns:
            处理后的音频路径
        """
        # 加载音频
        audio, sr = load_audio(audio_path, self.target_sr)

        # 裁剪
        audio = trim_audio(audio, self.target_sr, max_duration)

        # 降噪
        if denoise:
            audio = denoise_audio(audio, self.target_sr)

        # 移除静音
        if remove_silence:
            audio = remove_silence(audio, self.target_sr)

        # 增强
        if enhance:
            audio = enhance_audio(audio, self.target_sr)

        # 归一化
        if normalize:
            audio = normalize_audio(audio, self.normalize_db)

        # 保存
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

        save_audio(audio, output_path, self.target_sr)
        return output_path

    def preprocess_for_cloning(
        self,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        为音色克隆预处理音频

        优化的预处理流程，适合音色提取。

        Args:
            audio_path: 输入音频路径
            output_path: 输出路径

        Returns:
            处理后的音频路径
        """
        return self.process(
            audio_path=audio_path,
            output_path=output_path,
            denoise=True,
            remove_silence=True,
            enhance=True,
            normalize=True,
            max_duration=30.0
        )


# 便捷函数
def preprocess_audio(
    audio_path: str,
    output_path: Optional[str] = None,
    **kwargs
) -> str:
    """
    便捷的音频预处理函数

    Args:
        audio_path: 输入音频路径
        output_path: 输出路径
        **kwargs: 其他处理参数

    Returns:
        处理后的音频路径
    """
    processor = AudioProcessor()
    return processor.process(audio_path, output_path, **kwargs)
