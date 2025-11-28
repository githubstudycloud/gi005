"""
通用工具函数
"""

import os
import subprocess
from pathlib import Path
from typing import Union, Optional


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在

    Args:
        path: 目录路径

    Returns:
        Path 对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_audio_duration(audio_path: str) -> float:
    """
    获取音频时长（秒）

    Args:
        audio_path: 音频文件路径

    Returns:
        时长（秒）
    """
    try:
        import librosa
        duration = librosa.get_duration(path=audio_path)
        return duration
    except ImportError:
        # 使用 ffprobe 作为备选
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    audio_path
                ],
                capture_output=True, text=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0


def convert_audio_format(
    input_path: str,
    output_path: str,
    sample_rate: int = 22050,
    channels: int = 1
) -> str:
    """
    转换音频格式

    Args:
        input_path: 输入文件
        output_path: 输出文件
        sample_rate: 采样率
        channels: 声道数

    Returns:
        输出文件路径
    """
    try:
        import soundfile as sf
        import librosa

        # 加载音频
        audio, sr = librosa.load(input_path, sr=sample_rate, mono=(channels == 1))

        # 保存
        ensure_dir(Path(output_path).parent)
        sf.write(output_path, audio, sample_rate)

        return output_path
    except ImportError:
        # 使用 ffmpeg 作为备选
        ensure_dir(Path(output_path).parent)
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-ar', str(sample_rate),
            '-ac', str(channels),
            output_path
        ], capture_output=True)
        return output_path


def generate_voice_id() -> str:
    """生成唯一的音色ID"""
    import uuid
    return str(uuid.uuid4())[:8]


def validate_audio_file(audio_path: str) -> bool:
    """
    验证音频文件是否有效

    Args:
        audio_path: 音频文件路径

    Returns:
        是否有效
    """
    if not os.path.exists(audio_path):
        return False

    # 检查文件大小
    if os.path.getsize(audio_path) < 1000:  # 小于1KB
        return False

    # 检查扩展名
    valid_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac'}
    ext = Path(audio_path).suffix.lower()
    if ext not in valid_extensions:
        return False

    return True


def get_device(prefer_gpu: bool = True) -> str:
    """
    获取计算设备

    Args:
        prefer_gpu: 是否优先使用GPU

    Returns:
        设备字符串 ('cuda' / 'cpu')
    """
    if prefer_gpu:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
    return "cpu"
