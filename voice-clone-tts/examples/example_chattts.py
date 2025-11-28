"""
方案一示例：使用 ChatTTS 进行语音合成

ChatTTS 是一个高质量的中英文 TTS 模型，特别适合对话场景。
注意：ChatTTS 本身不支持从音频提取音色，但支持使用预定义的音色嵌入。

安装步骤：
pip install chattts
"""

import os
import torch
import numpy as np

# 检查是否安装了 ChatTTS
try:
    import ChatTTS
except ImportError:
    print("请先安装 ChatTTS:")
    print("  pip install chattts")
    exit(1)


class ChatTTSGenerator:
    """ChatTTS 语音生成器"""

    def __init__(self, device: str = None, compile_model: bool = False):
        """
        初始化 ChatTTS

        Args:
            device: 计算设备
            compile_model: 是否编译模型（加速但需要更多时间初始化）
        """
        self.device = device
        self.chat = ChatTTS.Chat()

        print("正在加载 ChatTTS 模型...")
        self.chat.load(compile=compile_model)
        print("模型加载完成")

    def sample_speaker(self) -> str:
        """
        随机采样一个说话人音色

        Returns:
            说话人嵌入字符串
        """
        spk_emb = self.chat.sample_random_speaker()
        return spk_emb

    def save_speaker(self, spk_emb, save_path: str):
        """
        保存说话人嵌入到文件

        Args:
            spk_emb: 说话人嵌入（字符串或tensor）
            save_path: 保存路径
        """
        if isinstance(spk_emb, str):
            with open(save_path, 'w') as f:
                f.write(spk_emb)
        else:
            torch.save(spk_emb, save_path)
        print(f"说话人嵌入已保存到: {save_path}")

    def load_speaker(self, load_path: str):
        """
        从文件加载说话人嵌入

        Args:
            load_path: 文件路径（.pt 或 .txt）

        Returns:
            说话人嵌入
        """
        if load_path.endswith('.pt'):
            spk_emb = torch.load(load_path, map_location='cpu')
        else:
            with open(load_path, 'r') as f:
                spk_emb = f.read()
        print(f"已加载说话人嵌入: {load_path}")
        return spk_emb

    def generate(self,
                 text: str | list[str],
                 speaker_embedding = None,
                 temperature: float = 0.3,
                 top_p: float = 0.7,
                 top_k: int = 20,
                 use_refine: bool = True) -> list[np.ndarray]:
        """
        生成语音

        Args:
            text: 要合成的文本（字符串或列表）
            speaker_embedding: 说话人嵌入（可选）
            temperature: 温度参数，越低越稳定
            top_p: nucleus sampling 参数
            top_k: top-k sampling 参数
            use_refine: 是否使用口语化优化

        Returns:
            音频数组列表
        """
        # 确保输入是列表
        if isinstance(text, str):
            text = [text]

        # 设置推理参数
        params_infer_code = ChatTTS.Chat.InferCodeParams(
            temperature=temperature,
            top_P=top_p,
            top_K=top_k,
        )

        # 如果提供了说话人嵌入
        if speaker_embedding is not None:
            params_infer_code.spk_emb = speaker_embedding

        # 设置文本优化参数（口语化）
        params_refine_text = None
        if use_refine:
            params_refine_text = ChatTTS.Chat.RefineTextParams(
                prompt='[oral_2][laugh_0][break_6]',  # 控制口语化程度
            )

        print(f"正在生成语音，共 {len(text)} 段...")

        # 生成语音
        wavs = self.chat.infer(
            text,
            params_refine_text=params_refine_text,
            params_infer_code=params_infer_code,
        )

        print("语音生成完成")
        return wavs

    def save_audio(self,
                   audio: np.ndarray,
                   save_path: str,
                   sample_rate: int = 24000):
        """
        保存音频到文件

        Args:
            audio: 音频数组
            save_path: 保存路径
            sample_rate: 采样率
        """
        try:
            import torchaudio
            # 确保音频是正确的形状
            if audio.ndim == 1:
                audio = audio.reshape(1, -1)
            audio_tensor = torch.from_numpy(audio).float()
            torchaudio.save(save_path, audio_tensor, sample_rate)
        except ImportError:
            # 使用 scipy 作为备选
            from scipy.io import wavfile
            if audio.ndim > 1:
                audio = audio.flatten()
            # 转换为 int16
            audio_int16 = (audio * 32767).astype(np.int16)
            wavfile.write(save_path, sample_rate, audio_int16)

        print(f"音频已保存到: {save_path}")


def demo_basic_generation():
    """基础语音生成示例"""
    print("\n=== 基础语音生成示例 ===\n")

    generator = ChatTTSGenerator()

    # 生成语音
    text = "你好，欢迎使用 ChatTTS 语音合成系统。这是一段测试语音。"
    wavs = generator.generate(text)

    # 保存音频
    if wavs and len(wavs) > 0:
        generator.save_audio(wavs[0], "output_basic.wav")


def demo_speaker_sampling():
    """说话人采样和复用示例"""
    print("\n=== 说话人采样示例 ===\n")

    generator = ChatTTSGenerator()

    # 采样多个说话人，选择满意的
    print("采样 5 个不同的说话人音色...")
    speakers = []
    for i in range(5):
        spk = generator.sample_speaker()
        speakers.append(spk)
        print(f"  说话人 {i+1}: {spk[:50]}...")  # 只显示前50个字符

    # 使用第一个说话人生成语音
    text = "这是使用采样音色生成的语音。"
    wavs = generator.generate(text, speaker_embedding=speakers[0])

    if wavs and len(wavs) > 0:
        # 保存音频
        generator.save_audio(wavs[0], "output_sampled_speaker.wav")

        # 保存说话人嵌入以便复用
        generator.save_speaker(speakers[0], "speaker_0.txt")


def demo_load_speaker():
    """加载预保存的说话人示例"""
    print("\n=== 加载预保存说话人示例 ===\n")

    generator = ChatTTSGenerator()

    # 检查是否有保存的说话人文件
    speaker_file = "speaker_0.txt"

    if os.path.exists(speaker_file):
        # 加载说话人
        spk = generator.load_speaker(speaker_file)

        # 使用加载的说话人生成语音
        text = "这是使用预保存音色生成的语音，音色应该保持一致。"
        wavs = generator.generate(text, speaker_embedding=spk)

        if wavs and len(wavs) > 0:
            generator.save_audio(wavs[0], "output_loaded_speaker.wav")
    else:
        print(f"说话人文件不存在: {speaker_file}")
        print("请先运行 demo_speaker_sampling() 生成说话人文件")


def demo_prosody_control():
    """韵律控制示例"""
    print("\n=== 韵律控制示例 ===\n")

    generator = ChatTTSGenerator()

    # 使用特殊标记控制韵律
    # [uv_break] - 停顿
    # [laugh] - 笑声
    # [oral] - 口语化程度

    text_with_control = """
    你好啊[uv_break]今天天气真不错[laugh]
    我们一起出去玩吧[uv_break]怎么样？
    """

    wavs = generator.generate(
        text_with_control,
        temperature=0.5,  # 稍高的温度增加变化
        use_refine=False  # 不使用自动口语化，使用手动控制
    )

    if wavs and len(wavs) > 0:
        generator.save_audio(wavs[0], "output_prosody.wav")


def main():
    """主函数"""
    print("=" * 60)
    print("ChatTTS 语音合成示例")
    print("=" * 60)

    # 运行各个示例
    demo_basic_generation()
    demo_speaker_sampling()
    demo_load_speaker()
    demo_prosody_control()

    print("\n" + "=" * 60)
    print("所有示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
