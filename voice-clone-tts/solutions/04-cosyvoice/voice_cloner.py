"""
CosyVoice 语音克隆实现

CosyVoice 是阿里通义实验室的多语言零样本语音合成模型。

安装:
  git clone https://github.com/FunAudioLLM/CosyVoice.git
  cd CosyVoice && pip install -r requirements.txt

模型下载:
  从 ModelScope 或 HuggingFace 下载
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Generator
import numpy as np

# 检查是否安装
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 尝试导入 CosyVoice
COSYVOICE_AVAILABLE = False
try:
    from cosyvoice.cli.cosyvoice import CosyVoice as CosyVoiceModel
    from cosyvoice.utils.file_utils import load_wav
    COSYVOICE_AVAILABLE = True
except ImportError:
    pass


class CosyVoiceCloner:
    """
    CosyVoice 语音克隆器

    功能:
    1. 零样本语音克隆（3秒参考音频）
    2. 跨语言合成
    3. 指令控制合成
    4. 预训练角色合成
    """

    # 支持的语言
    SUPPORTED_LANGUAGES = ["中文", "英文", "日语", "粤语", "韩语"]

    def __init__(
        self,
        model_dir: str = "pretrained_models/CosyVoice-300M",
        device: str = None
    ):
        """
        初始化 CosyVoice

        Args:
            model_dir: 模型目录路径
            device: 计算设备
        """
        if not COSYVOICE_AVAILABLE:
            raise ImportError(
                "CosyVoice 未安装。安装方法:\n"
                "  git clone https://github.com/FunAudioLLM/CosyVoice.git\n"
                "  cd CosyVoice && pip install -r requirements.txt"
            )

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[CosyVoice] 使用设备: {self.device}")

        print(f"[CosyVoice] 加载模型: {model_dir}")
        self.model = CosyVoiceModel(model_dir)
        print(f"[CosyVoice] 模型加载完成")

    def zero_shot_clone(
        self,
        text: str,
        reference_audio: str,
        reference_text: str,
        output_path: str,
        stream: bool = False
    ) -> str:
        """
        零样本语音克隆

        Args:
            text: 要合成的文本
            reference_audio: 参考音频路径（3-10秒）
            reference_text: 参考音频对应的文本
            output_path: 输出路径
            stream: 是否使用流式合成

        Returns:
            输出路径
        """
        if not os.path.exists(reference_audio):
            raise FileNotFoundError(f"参考音频不存在: {reference_audio}")

        print(f"[CosyVoice] 零样本克隆")
        print(f"[CosyVoice] 参考音频: {reference_audio}")
        print(f"[CosyVoice] 合成文本: {text[:50]}...")

        # 使用零样本推理
        if stream:
            output_generator = self.model.inference_zero_shot(
                text, reference_text, reference_audio, stream=True
            )
            audio_chunks = []
            for chunk in output_generator:
                audio_chunks.append(chunk['tts_speech'])
            audio = torch.cat(audio_chunks, dim=1)
        else:
            output = self.model.inference_zero_shot(
                text, reference_text, reference_audio
            )
            audio = output['tts_speech']

        # 保存
        self._save_audio(audio, output_path)
        print(f"[CosyVoice] 合成完成: {output_path}")
        return output_path

    def cross_lingual_clone(
        self,
        text: str,
        reference_audio: str,
        output_path: str
    ) -> str:
        """
        跨语言克隆（用一种语言的音频克隆另一种语言）

        Args:
            text: 目标语言文本
            reference_audio: 参考音频（可以是不同语言）
            output_path: 输出路径

        Returns:
            输出路径
        """
        if not os.path.exists(reference_audio):
            raise FileNotFoundError(f"参考音频不存在: {reference_audio}")

        print(f"[CosyVoice] 跨语言克隆")
        print(f"[CosyVoice] 合成文本: {text[:50]}...")

        output = self.model.inference_cross_lingual(text, reference_audio)
        audio = output['tts_speech']

        self._save_audio(audio, output_path)
        print(f"[CosyVoice] 合成完成: {output_path}")
        return output_path

    def instruct_clone(
        self,
        text: str,
        speaker: str,
        instruct: str,
        output_path: str
    ) -> str:
        """
        指令控制合成（需要 Instruct 模型）

        Args:
            text: 合成文本
            speaker: 说话人名称
            instruct: 风格指令（如 "用开心的语气"）
            output_path: 输出路径

        Returns:
            输出路径
        """
        print(f"[CosyVoice] 指令控制合成")
        print(f"[CosyVoice] 指令: {instruct}")

        output = self.model.inference_instruct(text, speaker, instruct)
        audio = output['tts_speech']

        self._save_audio(audio, output_path)
        print(f"[CosyVoice] 合成完成: {output_path}")
        return output_path

    def sft_clone(
        self,
        text: str,
        speaker: str,
        output_path: str
    ) -> str:
        """
        预训练角色合成（需要 SFT 模型）

        Args:
            text: 合成文本
            speaker: 预训练说话人名称
            output_path: 输出路径

        Returns:
            输出路径
        """
        print(f"[CosyVoice] SFT 角色合成")
        print(f"[CosyVoice] 说话人: {speaker}")

        output = self.model.inference_sft(text, speaker)
        audio = output['tts_speech']

        self._save_audio(audio, output_path)
        print(f"[CosyVoice] 合成完成: {output_path}")
        return output_path

    def list_sft_speakers(self) -> List[str]:
        """获取可用的 SFT 说话人列表"""
        return self.model.list_available_spks()

    def _save_audio(
        self,
        audio: "torch.Tensor",
        output_path: str,
        sample_rate: int = 22050
    ):
        """保存音频"""
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        torchaudio.save(output_path, audio.cpu(), sample_rate)


class CosyVoiceSimple:
    """
    CosyVoice 简化接口

    当完整的 CosyVoice 不可用时，提供基于 API 的替代方案
    """

    def __init__(self, api_url: str = None):
        """
        初始化简化接口

        Args:
            api_url: 可选的 API 服务地址
        """
        self.api_url = api_url
        print("[CosyVoice] 使用简化接口")

        if not TORCH_AVAILABLE:
            print("[CosyVoice] 警告: PyTorch 未安装")

    def clone(
        self,
        text: str,
        reference_audio: str,
        reference_text: str = "",
        output_path: str = "output.wav"
    ) -> str:
        """
        简化的克隆接口

        Args:
            text: 合成文本
            reference_audio: 参考音频
            reference_text: 参考文本（可选）
            output_path: 输出路径

        Returns:
            输出路径
        """
        if COSYVOICE_AVAILABLE:
            cloner = CosyVoiceCloner()
            return cloner.zero_shot_clone(
                text, reference_audio, reference_text, output_path
            )
        else:
            raise RuntimeError(
                "CosyVoice 未安装。请安装后使用:\n"
                "  git clone https://github.com/FunAudioLLM/CosyVoice.git\n"
                "  cd CosyVoice && pip install -r requirements.txt"
            )


def demo():
    """演示示例"""
    print("="*60)
    print("CosyVoice 语音克隆演示")
    print("="*60)

    if not COSYVOICE_AVAILABLE:
        print("\nCosyVoice 未安装。")
        print("\n安装步骤:")
        print("1. git clone https://github.com/FunAudioLLM/CosyVoice.git")
        print("2. cd CosyVoice")
        print("3. pip install -r requirements.txt")
        print("4. 下载模型到 pretrained_models/")
        return

    # 检查模型
    model_dir = "pretrained_models/CosyVoice-300M"
    if not os.path.exists(model_dir):
        print(f"\n请下载模型到: {model_dir}")
        print("下载地址:")
        print("  - ModelScope: https://modelscope.cn/models/iic/CosyVoice-300M")
        print("  - HuggingFace: https://huggingface.co/FunAudioLLM/CosyVoice-300M")
        return

    cloner = CosyVoiceCloner(model_dir)

    # 检查参考音频
    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"\n请提供参考音频: {reference_audio}")
        return

    # 零样本克隆
    text = "你好，这是使用 CosyVoice 合成的语音。"
    reference_text = "这是参考音频的内容。"  # 应与参考音频匹配

    cloner.zero_shot_clone(
        text=text,
        reference_audio=reference_audio,
        reference_text=reference_text,
        output_path="samples/output_cosyvoice.wav"
    )

    print("\n完成！")


if __name__ == "__main__":
    demo()
