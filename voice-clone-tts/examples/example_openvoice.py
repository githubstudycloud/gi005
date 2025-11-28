"""
方案二示例：使用 OpenVoice 进行音色克隆

OpenVoice 是目前最推荐的音色克隆方案，支持从任意音频提取音色特征。

安装步骤：
1. git clone https://github.com/myshell-ai/OpenVoice.git
2. cd OpenVoice && pip install -e .
3. 下载模型: https://huggingface.co/myshell-ai/OpenVoiceV2
"""

import os
import torch

# 检查是否安装了 OpenVoice
try:
    from openvoice import se_extractor
    from openvoice.api import ToneColorConverter, BaseSpeakerTTS
except ImportError:
    print("请先安装 OpenVoice:")
    print("  git clone https://github.com/myshell-ai/OpenVoice.git")
    print("  cd OpenVoice && pip install -e .")
    exit(1)


class OpenVoiceCloner:
    """OpenVoice 音色克隆器"""

    def __init__(self,
                 converter_ckpt: str = "checkpoints_v2/converter",
                 base_tts_ckpt: str = "checkpoints_v2/base_speakers/ses",
                 device: str = None):
        """
        初始化 OpenVoice 克隆器

        Args:
            converter_ckpt: 音色转换器检查点路径
            base_tts_ckpt: 基础TTS检查点路径
            device: 计算设备 (cuda/cpu)
        """
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f"使用设备: {self.device}")

        # 加载音色转换器
        self.tone_color_converter = ToneColorConverter(
            f'{converter_ckpt}/config.json',
            device=self.device
        )
        self.tone_color_converter.load_ckpt(f'{converter_ckpt}/checkpoint.pth')

        self.converter_ckpt = converter_ckpt
        self.base_tts_ckpt = base_tts_ckpt

    def extract_tone_color(self,
                           audio_path: str,
                           use_vad: bool = True) -> torch.Tensor:
        """
        从音频中提取音色特征 (Speaker Embedding)

        Args:
            audio_path: 参考音频路径
            use_vad: 是否使用语音活动检测

        Returns:
            音色嵌入向量 (Tone Color Embedding)
        """
        print(f"正在从 {audio_path} 提取音色...")

        target_se, audio_name = se_extractor.get_se(
            audio_path,
            self.tone_color_converter,
            vad=use_vad
        )

        print(f"音色提取完成，embedding shape: {target_se.shape}")
        return target_se

    def save_tone_color(self,
                        tone_embedding: torch.Tensor,
                        save_path: str):
        """保存音色嵌入到文件"""
        torch.save(tone_embedding, save_path)
        print(f"音色已保存到: {save_path}")

    def load_tone_color(self, load_path: str) -> torch.Tensor:
        """从文件加载音色嵌入"""
        tone_embedding = torch.load(load_path, map_location=self.device)
        print(f"已加载音色: {load_path}")
        return tone_embedding

    def clone_voice(self,
                    source_audio: str,
                    target_tone_embedding: torch.Tensor,
                    output_path: str,
                    source_se_path: str = None):
        """
        将源音频转换为目标音色

        Args:
            source_audio: 源音频路径（由基础TTS生成）
            target_tone_embedding: 目标音色嵌入
            output_path: 输出音频路径
            source_se_path: 源音色嵌入路径
        """
        # 加载源音色（基础TTS的音色）
        if source_se_path:
            source_se = torch.load(source_se_path, map_location=self.device)
        else:
            # 使用默认的基础说话人音色
            source_se = torch.load(
                f'{self.base_tts_ckpt}/zh_default_se.pth',
                map_location=self.device
            )

        print(f"正在进行音色转换...")

        # 执行音色转换
        self.tone_color_converter.convert(
            audio_src_path=source_audio,
            src_se=source_se,
            tgt_se=target_tone_embedding,
            output_path=output_path
        )

        print(f"音色克隆完成: {output_path}")


def main():
    """主函数示例"""

    # ========== 配置 ==========
    REFERENCE_AUDIO = "reference_speaker.wav"  # 参考音频（要克隆的音色）
    SOURCE_AUDIO = "tts_output.wav"            # TTS生成的基础音频
    OUTPUT_AUDIO = "cloned_output.wav"         # 输出音频
    TONE_EMBEDDING_PATH = "my_tone_color.pt"   # 音色嵌入保存路径

    # ========== 初始化克隆器 ==========
    cloner = OpenVoiceCloner(
        converter_ckpt="checkpoints_v2/converter",
        device="cuda:0" if torch.cuda.is_available() else "cpu"
    )

    # ========== 步骤1: 提取音色 ==========
    print("\n=== 步骤1: 从参考音频提取音色 ===")

    if os.path.exists(REFERENCE_AUDIO):
        tone_embedding = cloner.extract_tone_color(REFERENCE_AUDIO)

        # 保存音色以便复用
        cloner.save_tone_color(tone_embedding, TONE_EMBEDDING_PATH)
    else:
        print(f"参考音频不存在: {REFERENCE_AUDIO}")
        print("请提供一段参考音频文件")
        return

    # ========== 步骤2: 音色克隆 ==========
    print("\n=== 步骤2: 应用音色到TTS输出 ===")

    if os.path.exists(SOURCE_AUDIO):
        # 加载之前保存的音色（或直接使用 tone_embedding）
        loaded_tone = cloner.load_tone_color(TONE_EMBEDDING_PATH)

        # 执行音色克隆
        cloner.clone_voice(
            source_audio=SOURCE_AUDIO,
            target_tone_embedding=loaded_tone,
            output_path=OUTPUT_AUDIO
        )
    else:
        print(f"源音频不存在: {SOURCE_AUDIO}")
        print("请先使用 TTS 生成基础音频")

    print("\n=== 完成 ===")


if __name__ == "__main__":
    main()
