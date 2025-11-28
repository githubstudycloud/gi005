"""
Coqui XTTS-v2 音色克隆实现

特点：
1. 端到端语音克隆，一步到位
2. 支持17种语言
3. 只需6秒参考音频
4. 安装简单：pip install TTS
"""

import os
import sys
from pathlib import Path
from typing import Union, Optional
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.base import VoiceClonerBase, VoiceEmbedding
from common.utils import ensure_dir, get_device, generate_voice_id


class XTTSCloner(VoiceClonerBase):
    """
    XTTS-v2 音色克隆器

    最简单的方案，安装简单，使用方便。
    一个命令完成克隆：tts.tts_to_file(text, output, speaker_wav=ref)
    """

    ENGINE_NAME = "xtts"
    SUPPORTED_LANGUAGES = [
        "en", "es", "fr", "de", "it", "pt", "pl", "tr",
        "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"
    ]

    def __init__(
        self,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        model_path: str = None,
        device: str = None
    ):
        """
        初始化 XTTS

        Args:
            model_name: 模型名称（用于在线下载）
            model_path: 本地模型路径（优先使用，如 tts_model/xtts_v2）
            device: 设备
        """
        super().__init__(model_path=model_path or model_name, device=device)
        self.model_name = model_name
        self.local_model_path = model_path
        self.device = device or get_device()

        # 模型
        self.tts = None

    def load_model(self):
        """加载 XTTS 模型"""
        import os
        os.environ['COQUI_TOS_AGREED'] = '1'

        try:
            from TTS.api import TTS
        except ImportError:
            raise ImportError(
                "Coqui TTS 未安装。请运行:\n"
                "  pip install TTS"
            )

        use_gpu = self.device == "cuda"

        # 优先使用本地模型
        if self.local_model_path and os.path.exists(self.local_model_path):
            config_path = os.path.join(self.local_model_path, "config.json")
            print(f"[XTTS] 加载本地模型: {self.local_model_path}")
            self.tts = TTS(model_path=self.local_model_path, config_path=config_path, gpu=use_gpu)
        else:
            print(f"[XTTS] 加载模型: {self.model_name}")
            print("[XTTS] 首次运行会自动下载模型（约1.5GB）...")
            self.tts = TTS(self.model_name, gpu=use_gpu)

        self._model_loaded = True
        print(f"[XTTS] 模型加载完成，设备: {self.device}")

    def extract_voice(
        self,
        audio_path: str,
        voice_id: str = None,
        voice_name: str = "",
        save_dir: str = "./voices"
    ) -> VoiceEmbedding:
        """
        从音频提取音色

        XTTS 提取的是 (gpt_cond_latent, speaker_embedding) 组合

        Args:
            audio_path: 参考音频路径（建议6-30秒）
            voice_id: 音色ID
            voice_name: 音色名称
            save_dir: 保存目录

        Returns:
            VoiceEmbedding 对象
        """
        import torch

        self.ensure_loaded()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        voice_id = voice_id or generate_voice_id()
        voice_dir = ensure_dir(Path(save_dir) / voice_id)

        print(f"[XTTS] 提取音色: {audio_path}")

        # 获取底层模型
        model = self.tts.synthesizer.tts_model

        # 提取条件嵌入
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
            audio_path=[audio_path]
        )

        # 保存嵌入
        embedding_path = voice_dir / "embedding.pt"
        torch.save({
            "gpt_cond_latent": gpt_cond_latent,
            "speaker_embedding": speaker_embedding
        }, embedding_path)

        # 复制原始音频
        ref_audio_path = voice_dir / f"reference{Path(audio_path).suffix}"
        shutil.copy2(audio_path, ref_audio_path)

        # 创建音色对象
        voice = VoiceEmbedding(
            voice_id=voice_id,
            name=voice_name or voice_id,
            source_audio=str(ref_audio_path),
            embedding_path=str(embedding_path),
            engine=self.ENGINE_NAME,
            metadata={
                "gpt_cond_latent_shape": list(gpt_cond_latent.shape),
                "speaker_embedding_shape": list(speaker_embedding.shape)
            }
        )

        voice.save_meta(voice_dir / "voice.json")

        print(f"[XTTS] 音色已保存: {voice_dir}")
        return voice

    def synthesize(
        self,
        text: str,
        voice: Union[VoiceEmbedding, str],
        output_path: str,
        language: str = "zh-cn"
    ) -> str:
        """
        使用音色合成语音

        Args:
            text: 文本
            voice: VoiceEmbedding 或音色目录
            output_path: 输出路径
            language: 语言代码

        Returns:
            输出文件路径
        """
        import torch

        self.ensure_loaded()

        # 加载音色
        if isinstance(voice, str):
            voice = self.load_voice(voice)

        # 加载嵌入
        data = torch.load(voice.embedding_path, map_location=self.device)
        gpt_cond_latent = data["gpt_cond_latent"]
        speaker_embedding = data["speaker_embedding"]

        print(f"[XTTS] 合成语音: {text[:30]}...")

        # 获取底层模型
        model = self.tts.synthesizer.tts_model

        # 合成
        out = model.inference(
            text=text,
            language=language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            temperature=0.7,
        )

        # 保存
        ensure_dir(Path(output_path).parent)

        wav = out["wav"]
        import torchaudio
        import numpy as np

        if isinstance(wav, np.ndarray):
            wav = torch.from_numpy(wav)
        if wav.ndim == 1:
            wav = wav.unsqueeze(0)

        torchaudio.save(output_path, wav.cpu().float(), 24000)

        print(f"[XTTS] 合成完成: {output_path}")
        return output_path

    def synthesize_simple(
        self,
        text: str,
        reference_audio: str,
        output_path: str,
        language: str = "zh-cn"
    ) -> str:
        """
        简单合成（不保存音色，直接使用参考音频）

        Args:
            text: 文本
            reference_audio: 参考音频路径
            output_path: 输出路径
            language: 语言

        Returns:
            输出路径
        """
        self.ensure_loaded()

        print(f"[XTTS] 直接克隆: {reference_audio}")

        ensure_dir(Path(output_path).parent)

        self.tts.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=reference_audio,
            language=language
        )

        print(f"[XTTS] 合成完成: {output_path}")
        return output_path


# 便捷函数
def create_cloner(device: str = None) -> XTTSCloner:
    """
    创建 XTTS 克隆器

    Args:
        device: 设备

    Returns:
        XTTSCloner 实例
    """
    cloner = XTTSCloner(device=device)
    cloner.load_model()
    return cloner
