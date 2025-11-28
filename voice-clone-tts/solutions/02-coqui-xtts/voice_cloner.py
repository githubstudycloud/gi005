"""
Coqui XTTS-v2 语音克隆实现

XTTS-v2 是一个强大的多语言零样本语音克隆模型，只需 6 秒参考音频。

安装: pip install TTS
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple
import torch
import numpy as np

# 检查 TTS 是否安装
try:
    from TTS.api import TTS
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("警告: Coqui TTS 未安装")
    print("安装命令: pip install TTS")


class XTTSCloner:
    """
    XTTS-v2 语音克隆器

    功能:
    1. 从参考音频提取说话人嵌入
    2. 使用嵌入生成任意文本的语音
    3. 支持多语言克隆
    """

    # 支持的语言
    SUPPORTED_LANGUAGES = [
        "en", "es", "fr", "de", "it", "pt", "pl", "tr",
        "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"
    ]

    def __init__(
        self,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        use_gpu: bool = True
    ):
        """
        初始化 XTTS 克隆器

        Args:
            model_name: 模型名称
            use_gpu: 是否使用 GPU
        """
        if not TTS_AVAILABLE:
            raise ImportError("Coqui TTS 未安装，请运行: pip install TTS")

        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        print(f"[XTTS] 使用设备: {self.device}")

        print(f"[XTTS] 加载模型: {model_name}")
        print("[XTTS] 首次运行会自动下载模型（约1.5GB）...")
        self.tts = TTS(model_name, gpu=use_gpu)
        print("[XTTS] 模型加载完成")

    def list_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return self.SUPPORTED_LANGUAGES

    def clone_and_speak(
        self,
        text: str,
        reference_audio: str,
        output_path: str,
        language: str = "zh-cn"
    ) -> str:
        """
        使用参考音频的音色生成语音（一键克隆）

        Args:
            text: 要合成的文本
            reference_audio: 参考音频路径
            output_path: 输出音频路径
            language: 目标语言

        Returns:
            输出音频路径
        """
        if not os.path.exists(reference_audio):
            raise FileNotFoundError(f"参考音频不存在: {reference_audio}")

        if language not in self.SUPPORTED_LANGUAGES:
            print(f"警告: {language} 可能不受支持，尝试继续...")

        print(f"[XTTS] 克隆音色: {reference_audio}")
        print(f"[XTTS] 生成文本: {text[:50]}..." if len(text) > 50 else f"[XTTS] 生成文本: {text}")

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        # 使用 XTTS 进行语音克隆
        self.tts.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=reference_audio,
            language=language
        )

        print(f"[XTTS] 生成完成: {output_path}")
        return output_path

    def extract_speaker_embedding(
        self,
        audio_path: str
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        提取说话人嵌入

        Args:
            audio_path: 音频文件路径

        Returns:
            (speaker_embedding, gpt_cond_latent) 元组
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频不存在: {audio_path}")

        print(f"[XTTS] 提取说话人嵌入: {audio_path}")

        # 获取底层模型
        model = self.tts.synthesizer.tts_model

        # 提取嵌入
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
            audio_path=[audio_path]
        )

        print(f"[XTTS] Speaker embedding shape: {speaker_embedding.shape}")
        print(f"[XTTS] GPT cond latent shape: {gpt_cond_latent.shape}")

        return speaker_embedding, gpt_cond_latent

    def save_speaker_embedding(
        self,
        speaker_embedding: torch.Tensor,
        gpt_cond_latent: torch.Tensor,
        save_path: str
    ):
        """保存说话人嵌入"""
        os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
        torch.save({
            'speaker_embedding': speaker_embedding,
            'gpt_cond_latent': gpt_cond_latent
        }, save_path)
        print(f"[XTTS] 说话人嵌入已保存: {save_path}")

    def load_speaker_embedding(
        self,
        load_path: str
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """加载说话人嵌入"""
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"嵌入文件不存在: {load_path}")
        data = torch.load(load_path, map_location=self.device)
        print(f"[XTTS] 已加载说话人嵌入: {load_path}")
        return data['speaker_embedding'], data['gpt_cond_latent']

    def speak_with_embedding(
        self,
        text: str,
        speaker_embedding: torch.Tensor,
        gpt_cond_latent: torch.Tensor,
        output_path: str,
        language: str = "zh-cn",
        temperature: float = 0.7
    ) -> str:
        """
        使用预提取的嵌入生成语音

        Args:
            text: 文本
            speaker_embedding: 说话人嵌入
            gpt_cond_latent: GPT 条件潜变量
            output_path: 输出路径
            language: 语言
            temperature: 温度

        Returns:
            输出路径
        """
        print(f"[XTTS] 使用预存嵌入生成语音...")

        model = self.tts.synthesizer.tts_model

        # 使用模型推理
        out = model.inference(
            text,
            language,
            gpt_cond_latent,
            speaker_embedding,
            temperature=temperature,
        )

        # 保存音频
        wav = out["wav"]
        import torchaudio
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        if isinstance(wav, np.ndarray):
            wav = torch.from_numpy(wav)
        if wav.ndim == 1:
            wav = wav.unsqueeze(0)

        torchaudio.save(output_path, wav.cpu(), 24000)
        print(f"[XTTS] 生成完成: {output_path}")
        return output_path

    def clone_multi_language(
        self,
        texts: dict,
        reference_audio: str,
        output_dir: str
    ) -> List[str]:
        """
        多语言克隆

        Args:
            texts: {语言代码: 文本} 字典
            reference_audio: 参考音频
            output_dir: 输出目录

        Returns:
            输出文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        outputs = []

        for lang, text in texts.items():
            output_path = os.path.join(output_dir, f"output_{lang}.wav")
            try:
                self.clone_and_speak(text, reference_audio, output_path, lang)
                outputs.append(output_path)
            except Exception as e:
                print(f"[XTTS] {lang} 生成失败: {e}")

        return outputs


def demo():
    """演示示例"""
    print("="*60)
    print("Coqui XTTS-v2 语音克隆演示")
    print("="*60)

    if not TTS_AVAILABLE:
        print("\n请先安装 Coqui TTS:")
        print("  pip install TTS")
        return

    # 初始化
    cloner = XTTSCloner()
    print(f"\n支持的语言: {cloner.list_languages()}")

    # 检查参考音频
    reference_audio = "samples/reference.wav"
    os.makedirs("samples", exist_ok=True)

    if not os.path.exists(reference_audio):
        print(f"\n请提供参考音频: {reference_audio}")
        print("要求:")
        print("  - 时长: 6-30 秒")
        print("  - 清晰的单人语音")
        print("  - 无背景噪音")
        return

    # 中文克隆
    text_zh = "你好，这是使用 XTTS 语音克隆技术生成的语音。"
    cloner.clone_and_speak(text_zh, reference_audio, "samples/output_zh.wav", "zh-cn")

    # 英文克隆（同一音色）
    text_en = "Hello, this is the voice cloned using XTTS technology."
    cloner.clone_and_speak(text_en, reference_audio, "samples/output_en.wav", "en")

    print("\n完成！")


if __name__ == "__main__":
    demo()
