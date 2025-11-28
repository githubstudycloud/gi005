"""
音色克隆基类 - 统一接口定义

所有音色克隆方案都继承此基类，保证接口一致性。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union, Dict, Any
import json
import time


@dataclass
class VoiceEmbedding:
    """
    音色嵌入数据类

    用于保存和加载音色特征，便于复用。
    """
    # 音色标识
    voice_id: str
    # 音色名称（可选）
    name: str = ""
    # 创建时间
    created_at: float = field(default_factory=time.time)
    # 来源音频路径
    source_audio: str = ""
    # 嵌入数据路径（.pt/.npy等）
    embedding_path: str = ""
    # 使用的引擎
    engine: str = ""
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "voice_id": self.voice_id,
            "name": self.name,
            "created_at": self.created_at,
            "source_audio": self.source_audio,
            "embedding_path": self.embedding_path,
            "engine": self.engine,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceEmbedding":
        """从字典创建"""
        return cls(**data)

    def save_meta(self, path: Union[str, Path]):
        """保存元数据到JSON"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_meta(cls, path: Union[str, Path]) -> "VoiceEmbedding":
        """从JSON加载元数据"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


class VoiceClonerBase(ABC):
    """
    音色克隆基类

    所有引擎实现必须继承此类并实现抽象方法。

    使用流程:
    1. extract_voice() - 从音频提取音色
    2. synthesize() - 使用音色合成语音

    示例:
        cloner = XTTSCloner()

        # 提取音色
        voice = cloner.extract_voice("reference.wav", voice_id="my_voice")

        # 合成语音
        cloner.synthesize("你好世界", voice, "output.wav")
    """

    # 引擎名称
    ENGINE_NAME: str = "base"

    # 支持的语言
    SUPPORTED_LANGUAGES: list = []

    def __init__(self, model_path: str = None, device: str = None):
        """
        初始化克隆器

        Args:
            model_path: 模型路径
            device: 计算设备 ('cuda' / 'cpu')
        """
        self.model_path = model_path
        self.device = device
        self._model_loaded = False

    @abstractmethod
    def load_model(self):
        """
        加载模型

        子类必须实现此方法。
        """
        pass

    @abstractmethod
    def extract_voice(
        self,
        audio_path: str,
        voice_id: str,
        voice_name: str = "",
        save_dir: str = "./voices"
    ) -> VoiceEmbedding:
        """
        从音频提取音色特征

        Args:
            audio_path: 参考音频路径
            voice_id: 音色唯一标识
            voice_name: 音色名称（可选）
            save_dir: 保存目录

        Returns:
            VoiceEmbedding 对象
        """
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: Union[VoiceEmbedding, str],
        output_path: str,
        language: str = "zh"
    ) -> str:
        """
        使用音色合成语音

        Args:
            text: 要合成的文本
            voice: VoiceEmbedding对象 或 音色目录路径
            output_path: 输出音频路径
            language: 语言代码

        Returns:
            输出音频路径
        """
        pass

    def load_voice(self, voice_dir: str) -> VoiceEmbedding:
        """
        加载已保存的音色

        Args:
            voice_dir: 音色目录路径

        Returns:
            VoiceEmbedding 对象
        """
        voice_dir = Path(voice_dir)
        meta_path = voice_dir / "voice.json"

        if not meta_path.exists():
            raise FileNotFoundError(f"音色元数据不存在: {meta_path}")

        return VoiceEmbedding.load_meta(meta_path)

    def list_voices(self, voices_dir: str = "./voices") -> list:
        """
        列出所有已保存的音色

        Args:
            voices_dir: 音色存储目录

        Returns:
            VoiceEmbedding 列表
        """
        voices_dir = Path(voices_dir)
        voices = []

        if voices_dir.exists():
            for voice_path in voices_dir.iterdir():
                if voice_path.is_dir():
                    meta_path = voice_path / "voice.json"
                    if meta_path.exists():
                        try:
                            voice = VoiceEmbedding.load_meta(meta_path)
                            voices.append(voice)
                        except Exception:
                            pass

        return voices

    def delete_voice(self, voice_id: str, voices_dir: str = "./voices") -> bool:
        """
        删除音色

        Args:
            voice_id: 音色ID
            voices_dir: 音色存储目录

        Returns:
            是否删除成功
        """
        import shutil
        voice_path = Path(voices_dir) / voice_id

        if voice_path.exists():
            shutil.rmtree(voice_path)
            return True
        return False

    @property
    def is_loaded(self) -> bool:
        """模型是否已加载"""
        return self._model_loaded

    def ensure_loaded(self):
        """确保模型已加载"""
        if not self._model_loaded:
            self.load_model()
