"""
OpenVoice 音色克隆实现

使用 OpenVoice 从参考音频提取音色，并将其应用到任意语音上。

安装步骤：
1. git clone https://github.com/myshell-ai/OpenVoice.git
2. cd OpenVoice && pip install -e .
3. 下载模型: https://huggingface.co/myshell-ai/OpenVoiceV2
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple
import torch
import numpy as np

# 检查 OpenVoice 是否安装
try:
    from openvoice import se_extractor
    from openvoice.api import ToneColorConverter
    OPENVOICE_AVAILABLE = True
except ImportError:
    OPENVOICE_AVAILABLE = False
    print("警告: OpenVoice 未安装")
    print("安装步骤:")
    print("  git clone https://github.com/myshell-ai/OpenVoice.git")
    print("  cd OpenVoice && pip install -e .")


class OpenVoiceCloner:
    """
    OpenVoice 音色克隆器

    功能:
    1. 从任意音频提取音色特征 (Tone Color Embedding)
    2. 将音色应用到其他语音上
    3. 保存和加载音色嵌入
    """

    def __init__(
        self,
        ckpt_converter: str = "checkpoints_v2/converter",
        device: str = None
    ):
        """
        初始化 OpenVoice 克隆器

        Args:
            ckpt_converter: 音色转换器检查点路径
            device: 计算设备 ('cuda:0' 或 'cpu')
        """
        if not OPENVOICE_AVAILABLE:
            raise ImportError("OpenVoice 未安装，请先安装")

        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f"[OpenVoice] 使用设备: {self.device}")

        # 加载音色转换器
        config_path = f'{ckpt_converter}/config.json'
        ckpt_path = f'{ckpt_converter}/checkpoint.pth'

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"配置文件不存在: {config_path}\n"
                "请下载模型: https://huggingface.co/myshell-ai/OpenVoiceV2"
            )

        print(f"[OpenVoice] 加载音色转换器...")
        self.tone_color_converter = ToneColorConverter(config_path, device=self.device)
        self.tone_color_converter.load_ckpt(ckpt_path)
        print(f"[OpenVoice] 音色转换器加载完成")

        self.ckpt_converter = ckpt_converter

    def extract_tone_color(
        self,
        audio_path: str,
        use_vad: bool = True
    ) -> torch.Tensor:
        """
        从音频提取音色特征

        Args:
            audio_path: 参考音频路径 (wav/mp3/flac等)
            use_vad: 是否使用语音活动检测过滤静音

        Returns:
            tone_color_embedding: 音色嵌入张量
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        print(f"[OpenVoice] 从 {audio_path} 提取音色...")

        # 使用 se_extractor 提取音色嵌入
        target_se, audio_name = se_extractor.get_se(
            audio_path,
            self.tone_color_converter,
            vad=use_vad
        )

        print(f"[OpenVoice] 音色提取完成，embedding shape: {target_se.shape}")
        return target_se

    def convert_voice(
        self,
        source_audio_path: str,
        target_tone_embedding: torch.Tensor,
        output_path: str,
        source_se_path: str = None,
        tau: float = 0.3
    ) -> str:
        """
        将源音频转换为目标音色

        Args:
            source_audio_path: 源音频路径 (要转换的音频)
            target_tone_embedding: 目标音色嵌入
            output_path: 输出音频路径
            source_se_path: 源音色嵌入路径 (可选)
            tau: 转换强度 (0-1, 越大越接近目标音色)

        Returns:
            输出音频路径
        """
        if not os.path.exists(source_audio_path):
            raise FileNotFoundError(f"源音频不存在: {source_audio_path}")

        # 加载源音色嵌入
        if source_se_path and os.path.exists(source_se_path):
            source_se = torch.load(source_se_path, map_location=self.device)
        else:
            # 从源音频提取音色
            source_se, _ = se_extractor.get_se(
                source_audio_path,
                self.tone_color_converter,
                vad=True
            )

        print(f"[OpenVoice] 转换音色: {source_audio_path} -> {output_path}")

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        # 执行音色转换
        self.tone_color_converter.convert(
            audio_src_path=source_audio_path,
            src_se=source_se,
            tgt_se=target_tone_embedding,
            output_path=output_path,
            tau=tau
        )

        print(f"[OpenVoice] 转换完成: {output_path}")
        return output_path

    def save_tone_color(
        self,
        tone_embedding: torch.Tensor,
        save_path: str
    ):
        """保存音色嵌入到文件"""
        os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
        torch.save(tone_embedding, save_path)
        print(f"[OpenVoice] 音色已保存到: {save_path}")

    def load_tone_color(self, load_path: str) -> torch.Tensor:
        """从文件加载音色嵌入"""
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"音色文件不存在: {load_path}")
        tone_embedding = torch.load(load_path, map_location=self.device)
        print(f"[OpenVoice] 已加载音色: {load_path}")
        return tone_embedding

    def clone_voice(
        self,
        reference_audio: str,
        source_audio: str,
        output_path: str,
        save_embedding: str = None
    ) -> str:
        """
        一键音色克隆（端到端）

        Args:
            reference_audio: 参考音频（目标音色）
            source_audio: 源音频（要转换的内容）
            output_path: 输出路径
            save_embedding: 可选，保存音色嵌入的路径

        Returns:
            输出音频路径
        """
        # 1. 提取目标音色
        target_se = self.extract_tone_color(reference_audio)

        # 2. 可选保存音色
        if save_embedding:
            self.save_tone_color(target_se, save_embedding)

        # 3. 转换音色
        return self.convert_voice(source_audio, target_se, output_path)


def demo():
    """演示示例"""
    print("="*60)
    print("OpenVoice 音色克隆演示")
    print("="*60)

    if not OPENVOICE_AVAILABLE:
        print("\n请先安装 OpenVoice:")
        print("  git clone https://github.com/myshell-ai/OpenVoice.git")
        print("  cd OpenVoice && pip install -e .")
        return

    # 检查模型检查点
    ckpt_path = "checkpoints_v2/converter"
    if not os.path.exists(ckpt_path):
        print(f"\n请下载模型检查点到 {ckpt_path}:")
        print("  https://huggingface.co/myshell-ai/OpenVoiceV2")
        return

    # 初始化
    cloner = OpenVoiceCloner(ckpt_converter=ckpt_path)

    # 检查测试音频
    reference_audio = "samples/reference.wav"
    source_audio = "samples/source.wav"

    if not os.path.exists(reference_audio):
        print(f"\n请提供参考音频: {reference_audio}")
        print("  (这是你想要克隆的音色)")
        return

    if not os.path.exists(source_audio):
        print(f"\n请提供源音频: {source_audio}")
        print("  (这是要转换的语音内容)")
        return

    # 执行克隆
    output_path = "samples/output_cloned.wav"
    cloner.clone_voice(
        reference_audio=reference_audio,
        source_audio=source_audio,
        output_path=output_path,
        save_embedding="samples/my_voice.pt"
    )

    print(f"\n完成！输出文件: {output_path}")


if __name__ == "__main__":
    demo()
