"""
方案三示例：使用 Coqui TTS (XTTS-v2) 进行语音克隆

XTTS-v2 是功能强大的多语言语音克隆模型，只需 6 秒参考音频。

安装步骤：
pip install TTS
"""

import os
import torch

# 检查是否安装了 TTS
try:
    from TTS.api import TTS
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
except ImportError:
    print("请先安装 Coqui TTS:")
    print("  pip install TTS")
    exit(1)


class XTTSCloner:
    """XTTS-v2 语音克隆器"""

    def __init__(self,
                 model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
                 use_gpu: bool = True):
        """
        初始化 XTTS 模型

        Args:
            model_name: 模型名称
            use_gpu: 是否使用 GPU
        """
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        print(f"使用设备: {self.device}")

        print(f"正在加载模型: {model_name}")
        self.tts = TTS(model_name, gpu=use_gpu)
        print("模型加载完成")

    def list_languages(self) -> list:
        """获取支持的语言列表"""
        return self.tts.languages

    def clone_and_speak(self,
                        text: str,
                        reference_audio: str,
                        output_path: str,
                        language: str = "zh-cn"):
        """
        使用参考音频的音色生成语音

        Args:
            text: 要合成的文本
            reference_audio: 参考音频路径（用于提取音色）
            output_path: 输出音频路径
            language: 目标语言
        """
        if not os.path.exists(reference_audio):
            raise FileNotFoundError(f"参考音频不存在: {reference_audio}")

        print(f"正在使用 {reference_audio} 的音色生成语音...")
        print(f"文本: {text[:50]}..." if len(text) > 50 else f"文本: {text}")

        # 直接使用参考音频进行语音克隆
        self.tts.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=reference_audio,
            language=language
        )

        print(f"语音已保存到: {output_path}")

    def extract_speaker_embedding(self, audio_path: str) -> torch.Tensor:
        """
        提取说话人嵌入

        Args:
            audio_path: 音频文件路径

        Returns:
            说话人嵌入张量
        """
        # 获取底层模型
        model = self.tts.synthesizer.tts_model

        # 加载音频
        import torchaudio
        wav, sr = torchaudio.load(audio_path)

        # 如果需要重采样
        if sr != 22050:
            resampler = torchaudio.transforms.Resample(sr, 22050)
            wav = resampler(wav)

        # 提取嵌入
        with torch.no_grad():
            gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
                audio_path=[audio_path]
            )

        print(f"Speaker embedding shape: {speaker_embedding.shape}")
        return speaker_embedding, gpt_cond_latent

    def save_speaker_embedding(self,
                               embedding: torch.Tensor,
                               gpt_latent: torch.Tensor,
                               save_path: str):
        """保存说话人嵌入"""
        torch.save({
            'speaker_embedding': embedding,
            'gpt_cond_latent': gpt_latent
        }, save_path)
        print(f"说话人嵌入已保存到: {save_path}")

    def load_speaker_embedding(self, load_path: str):
        """加载说话人嵌入"""
        data = torch.load(load_path, map_location=self.device)
        return data['speaker_embedding'], data['gpt_cond_latent']


class XTTSAdvanced:
    """高级 XTTS 用法，直接使用模型"""

    def __init__(self,
                 config_path: str = None,
                 checkpoint_path: str = None,
                 use_gpu: bool = True):
        """
        直接加载 XTTS 模型

        Args:
            config_path: 配置文件路径
            checkpoint_path: 检查点路径
            use_gpu: 是否使用 GPU
        """
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"

        if config_path and checkpoint_path:
            # 从本地加载
            config = XttsConfig()
            config.load_json(config_path)
            self.model = Xtts.init_from_config(config)
            self.model.load_checkpoint(config, checkpoint_path)
        else:
            # 使用默认模型
            from TTS.utils.manage import ModelManager
            model_manager = ModelManager()
            model_path, config_path, _ = model_manager.download_model(
                "tts_models/multilingual/multi-dataset/xtts_v2"
            )
            config = XttsConfig()
            config.load_json(config_path)
            self.model = Xtts.init_from_config(config)
            self.model.load_checkpoint(config, checkpoint_dir=model_path)

        self.model.to(self.device)
        print(f"XTTS 模型已加载到 {self.device}")

    def generate_with_latents(self,
                              text: str,
                              speaker_embedding: torch.Tensor,
                              gpt_cond_latent: torch.Tensor,
                              language: str = "zh-cn",
                              temperature: float = 0.7) -> torch.Tensor:
        """
        使用预提取的说话人嵌入生成语音

        Args:
            text: 文本
            speaker_embedding: 说话人嵌入
            gpt_cond_latent: GPT 条件潜变量
            language: 语言
            temperature: 温度

        Returns:
            音频张量
        """
        out = self.model.inference(
            text,
            language,
            gpt_cond_latent,
            speaker_embedding,
            temperature=temperature,
        )
        return out["wav"]


def demo_basic_cloning():
    """基础语音克隆示例"""
    print("\n=== 基础语音克隆示例 ===\n")

    cloner = XTTSCloner()

    # 列出支持的语言
    print(f"支持的语言: {cloner.list_languages()}")

    # 检查参考音频
    reference_audio = "reference_speaker.wav"
    if not os.path.exists(reference_audio):
        print(f"\n请提供参考音频文件: {reference_audio}")
        print("参考音频建议：")
        print("  - 时长 6-30 秒")
        print("  - 清晰的单人语音")
        print("  - 无背景噪音")
        return

    # 生成克隆语音
    text = "你好，这是使用 XTTS 语音克隆技术生成的语音。"
    cloner.clone_and_speak(
        text=text,
        reference_audio=reference_audio,
        output_path="output_xtts_cloned.wav",
        language="zh-cn"
    )


def demo_embedding_extraction():
    """说话人嵌入提取示例"""
    print("\n=== 说话人嵌入提取示例 ===\n")

    cloner = XTTSCloner()

    reference_audio = "reference_speaker.wav"
    if not os.path.exists(reference_audio):
        print(f"请提供参考音频: {reference_audio}")
        return

    # 提取说话人嵌入
    speaker_emb, gpt_latent = cloner.extract_speaker_embedding(reference_audio)

    # 保存嵌入
    cloner.save_speaker_embedding(
        speaker_emb,
        gpt_latent,
        "speaker_embedding_xtts.pt"
    )


def demo_multi_language():
    """多语言克隆示例"""
    print("\n=== 多语言克隆示例 ===\n")

    cloner = XTTSCloner()

    reference_audio = "reference_speaker.wav"
    if not os.path.exists(reference_audio):
        print(f"请提供参考音频: {reference_audio}")
        return

    # 使用同一个参考音频生成多种语言
    texts = {
        "zh-cn": "你好，这是中文语音。",
        "en": "Hello, this is English speech.",
        "ja": "こんにちは、これは日本語の音声です。",
        "ko": "안녕하세요, 이것은 한국어 음성입니다.",
    }

    for lang, text in texts.items():
        print(f"\n生成 {lang} 语音...")
        try:
            cloner.clone_and_speak(
                text=text,
                reference_audio=reference_audio,
                output_path=f"output_xtts_{lang}.wav",
                language=lang
            )
        except Exception as e:
            print(f"  生成 {lang} 失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("Coqui XTTS-v2 语音克隆示例")
    print("=" * 60)

    demo_basic_cloning()
    demo_embedding_extraction()
    demo_multi_language()

    print("\n" + "=" * 60)
    print("所有示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
