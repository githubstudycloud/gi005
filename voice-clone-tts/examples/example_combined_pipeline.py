"""
综合方案示例：OpenVoice + ChatTTS 组合流程

这是推荐的最佳实践方案：
1. 使用 OpenVoice 从参考音频提取音色
2. 使用 ChatTTS 生成高质量中文语音
3. 使用 OpenVoice 将 ChatTTS 输出转换为目标音色

优点：
- ChatTTS 的中文语音质量最佳
- OpenVoice 的音色克隆效果优秀
- 两者结合取长补短

安装步骤：
pip install chattts
git clone https://github.com/myshell-ai/OpenVoice.git
cd OpenVoice && pip install -e .
"""

import os
import torch
import numpy as np
from typing import Optional

# 检查依赖
def check_dependencies():
    missing = []

    try:
        import ChatTTS
    except ImportError:
        missing.append("ChatTTS (pip install chattts)")

    try:
        from openvoice import se_extractor
        from openvoice.api import ToneColorConverter
    except ImportError:
        missing.append("OpenVoice (git clone + pip install -e .)")

    if missing:
        print("缺少以下依赖:")
        for dep in missing:
            print(f"  - {dep}")
        return False
    return True


class VoiceCloneTTSPipeline:
    """音色克隆 TTS 流水线"""

    def __init__(self,
                 openvoice_converter_ckpt: str = "checkpoints_v2/converter",
                 openvoice_base_se_path: str = "checkpoints_v2/base_speakers/ses/zh_default_se.pth",
                 device: str = None,
                 compile_chattts: bool = False):
        """
        初始化流水线

        Args:
            openvoice_converter_ckpt: OpenVoice 转换器检查点路径
            openvoice_base_se_path: OpenVoice 基础说话人嵌入路径
            device: 计算设备
            compile_chattts: 是否编译 ChatTTS 模型
        """
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f"使用设备: {self.device}")

        # 初始化 ChatTTS
        print("\n[1/2] 正在加载 ChatTTS...")
        import ChatTTS
        self.chat_tts = ChatTTS.Chat()
        self.chat_tts.load(compile=compile_chattts)
        print("ChatTTS 加载完成")

        # 初始化 OpenVoice
        print("\n[2/2] 正在加载 OpenVoice...")
        from openvoice import se_extractor
        from openvoice.api import ToneColorConverter

        self.se_extractor = se_extractor
        self.tone_color_converter = ToneColorConverter(
            f'{openvoice_converter_ckpt}/config.json',
            device=self.device
        )
        self.tone_color_converter.load_ckpt(f'{openvoice_converter_ckpt}/checkpoint.pth')

        # 加载基础说话人嵌入（ChatTTS 默认音色对应的 OpenVoice 嵌入）
        self.base_speaker_se = torch.load(openvoice_base_se_path, map_location=self.device)
        print("OpenVoice 加载完成")

        # 缓存目标音色
        self.target_speaker_se = None

        print("\n流水线初始化完成！")

    def extract_voice_from_audio(self, audio_path: str, use_vad: bool = True) -> torch.Tensor:
        """
        从参考音频提取音色

        Args:
            audio_path: 参考音频路径
            use_vad: 是否使用语音活动检测

        Returns:
            音色嵌入
        """
        print(f"正在从 {audio_path} 提取音色...")

        target_se, audio_name = self.se_extractor.get_se(
            audio_path,
            self.tone_color_converter,
            vad=use_vad
        )

        self.target_speaker_se = target_se
        print(f"音色提取完成")
        return target_se

    def set_target_voice(self, voice_embedding: torch.Tensor):
        """设置目标音色"""
        self.target_speaker_se = voice_embedding

    def generate_tts(self,
                     text: str,
                     chattts_speaker: Optional[str] = None,
                     temperature: float = 0.3,
                     top_p: float = 0.7,
                     top_k: int = 20) -> np.ndarray:
        """
        使用 ChatTTS 生成语音

        Args:
            text: 输入文本
            chattts_speaker: ChatTTS 说话人嵌入（可选）
            temperature: 温度参数
            top_p: nucleus sampling
            top_k: top-k sampling

        Returns:
            音频数组
        """
        import ChatTTS

        params_infer_code = ChatTTS.Chat.InferCodeParams(
            temperature=temperature,
            top_P=top_p,
            top_K=top_k,
        )

        if chattts_speaker is not None:
            params_infer_code.spk_emb = chattts_speaker

        params_refine_text = ChatTTS.Chat.RefineTextParams(
            prompt='[oral_2][laugh_0][break_6]',
        )

        wavs = self.chat_tts.infer(
            [text],
            params_refine_text=params_refine_text,
            params_infer_code=params_infer_code,
        )

        return wavs[0]

    def convert_voice(self,
                      source_audio_path: str,
                      output_path: str,
                      target_se: Optional[torch.Tensor] = None):
        """
        转换音色

        Args:
            source_audio_path: 源音频路径
            output_path: 输出路径
            target_se: 目标音色嵌入（如果为 None 则使用之前提取的）
        """
        if target_se is None:
            target_se = self.target_speaker_se

        if target_se is None:
            raise ValueError("请先提取目标音色或提供 target_se 参数")

        self.tone_color_converter.convert(
            audio_src_path=source_audio_path,
            src_se=self.base_speaker_se,
            tgt_se=target_se,
            output_path=output_path
        )

    def synthesize(self,
                   text: str,
                   output_path: str,
                   reference_audio: Optional[str] = None,
                   chattts_speaker: Optional[str] = None,
                   temperature: float = 0.3) -> str:
        """
        完整的语音合成流程

        Args:
            text: 输入文本
            output_path: 输出音频路径
            reference_audio: 参考音频路径（用于音色克隆）
            chattts_speaker: ChatTTS 说话人嵌入
            temperature: 温度参数

        Returns:
            输出音频路径
        """
        import tempfile
        import torchaudio

        print(f"\n{'='*50}")
        print("开始语音合成流程")
        print(f"{'='*50}")

        # 步骤1：提取目标音色（如果提供了参考音频）
        if reference_audio is not None:
            print(f"\n[步骤 1/3] 提取目标音色")
            self.extract_voice_from_audio(reference_audio)
        elif self.target_speaker_se is None:
            print("\n[步骤 1/3] 跳过音色提取（无参考音频，将使用 ChatTTS 默认音色）")
        else:
            print("\n[步骤 1/3] 使用缓存的目标音色")

        # 步骤2：使用 ChatTTS 生成基础语音
        print(f"\n[步骤 2/3] 使用 ChatTTS 生成语音")
        print(f"  文本: {text[:50]}..." if len(text) > 50 else f"  文本: {text}")

        audio = self.generate_tts(
            text,
            chattts_speaker=chattts_speaker,
            temperature=temperature
        )

        # 保存临时文件
        temp_audio_path = tempfile.mktemp(suffix=".wav")
        audio_tensor = torch.from_numpy(audio).unsqueeze(0).float()
        torchaudio.save(temp_audio_path, audio_tensor, 24000)
        print(f"  ChatTTS 输出已保存到临时文件")

        # 步骤3：音色转换（如果有目标音色）
        if self.target_speaker_se is not None:
            print(f"\n[步骤 3/3] 进行音色转换")
            self.convert_voice(temp_audio_path, output_path)
            # 清理临时文件
            os.remove(temp_audio_path)
        else:
            print(f"\n[步骤 3/3] 跳过音色转换（无目标音色）")
            os.rename(temp_audio_path, output_path)

        print(f"\n{'='*50}")
        print(f"合成完成: {output_path}")
        print(f"{'='*50}")

        return output_path

    def save_target_voice(self, save_path: str):
        """保存目标音色"""
        if self.target_speaker_se is None:
            raise ValueError("没有目标音色可保存")
        torch.save(self.target_speaker_se, save_path)
        print(f"目标音色已保存到: {save_path}")

    def load_target_voice(self, load_path: str):
        """加载目标音色"""
        self.target_speaker_se = torch.load(load_path, map_location=self.device)
        print(f"已加载目标音色: {load_path}")


def demo_full_pipeline():
    """完整流程演示"""
    print("\n" + "="*60)
    print("完整音色克隆 TTS 流程演示")
    print("="*60)

    if not check_dependencies():
        return

    # 初始化流水线
    pipeline = VoiceCloneTTSPipeline(
        openvoice_converter_ckpt="checkpoints_v2/converter",
        device="cuda:0" if torch.cuda.is_available() else "cpu"
    )

    # 检查参考音频
    reference_audio = "reference_speaker.wav"
    if not os.path.exists(reference_audio):
        print(f"\n请提供参考音频文件: {reference_audio}")
        print("将使用 ChatTTS 默认音色进行演示...")
        reference_audio = None

    # 合成语音
    text = "你好，这是使用音色克隆技术生成的语音。声音应该和参考音频很像。"

    pipeline.synthesize(
        text=text,
        output_path="output_cloned_voice.wav",
        reference_audio=reference_audio,
        temperature=0.3
    )

    # 如果提取了音色，保存它以便复用
    if pipeline.target_speaker_se is not None:
        pipeline.save_target_voice("my_voice_embedding.pt")


def demo_batch_synthesis():
    """批量合成演示"""
    print("\n" + "="*60)
    print("批量音色克隆 TTS 演示")
    print("="*60)

    if not check_dependencies():
        return

    # 初始化
    pipeline = VoiceCloneTTSPipeline()

    # 加载之前保存的音色
    voice_embedding_path = "my_voice_embedding.pt"
    if os.path.exists(voice_embedding_path):
        pipeline.load_target_voice(voice_embedding_path)
    else:
        print(f"音色文件不存在: {voice_embedding_path}")
        print("请先运行 demo_full_pipeline() 提取并保存音色")
        return

    # 批量合成
    texts = [
        "第一句话：今天天气真不错。",
        "第二句话：我们一起去散步吧。",
        "第三句话：晚上吃什么好呢？",
    ]

    for i, text in enumerate(texts):
        output_path = f"output_batch_{i+1}.wav"
        pipeline.synthesize(
            text=text,
            output_path=output_path,
            temperature=0.3
        )


def main():
    """主函数"""
    print("="*60)
    print("OpenVoice + ChatTTS 组合方案")
    print("="*60)
    print()
    print("这是推荐的最佳实践方案：")
    print("1. ChatTTS 提供高质量的中文语音合成")
    print("2. OpenVoice 提供音色克隆能力")
    print("3. 两者结合实现最佳效果")
    print()

    demo_full_pipeline()
    # demo_batch_synthesis()  # 需要先运行 demo_full_pipeline

    print("\n" + "="*60)
    print("演示完成！")
    print("="*60)


if __name__ == "__main__":
    main()
