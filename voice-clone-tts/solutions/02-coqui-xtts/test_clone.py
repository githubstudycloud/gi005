"""
Coqui XTTS-v2 语音克隆测试脚本
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice_cloner import XTTSCloner, TTS_AVAILABLE


def test_basic_clone():
    """测试基本克隆功能"""
    print("\n" + "="*50)
    print("测试1: 基本语音克隆")
    print("="*50)

    if not TTS_AVAILABLE:
        print("跳过: Coqui TTS 未安装")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    try:
        cloner = XTTSCloner()

        text = "这是一段测试语音，用于验证 XTTS 语音克隆效果。"
        output_path = "samples/output_basic.wav"

        cloner.clone_and_speak(text, reference_audio, output_path, "zh-cn")

        print(f"✓ 基本克隆成功")
        print(f"  - 输出文件: {output_path}")

    except Exception as e:
        print(f"✗ 基本克隆失败: {e}")


def test_embedding_extraction():
    """测试嵌入提取"""
    print("\n" + "="*50)
    print("测试2: 说话人嵌入提取")
    print("="*50)

    if not TTS_AVAILABLE:
        print("跳过: Coqui TTS 未安装")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    try:
        cloner = XTTSCloner()

        # 提取嵌入
        speaker_emb, gpt_latent = cloner.extract_speaker_embedding(reference_audio)

        # 保存嵌入
        embedding_path = "samples/speaker_embedding.pt"
        cloner.save_speaker_embedding(speaker_emb, gpt_latent, embedding_path)

        print(f"✓ 嵌入提取成功")
        print(f"  - Speaker embedding: {speaker_emb.shape}")
        print(f"  - GPT latent: {gpt_latent.shape}")
        print(f"  - 保存路径: {embedding_path}")

    except Exception as e:
        print(f"✗ 嵌入提取失败: {e}")


def test_speak_with_embedding():
    """测试使用预存嵌入生成语音"""
    print("\n" + "="*50)
    print("测试3: 使用预存嵌入生成语音")
    print("="*50)

    if not TTS_AVAILABLE:
        print("跳过: Coqui TTS 未安装")
        return

    embedding_path = "samples/speaker_embedding.pt"
    if not os.path.exists(embedding_path):
        print(f"跳过: 嵌入文件不存在 {embedding_path}")
        print("请先运行测试2提取嵌入")
        return

    try:
        cloner = XTTSCloner()

        # 加载嵌入
        speaker_emb, gpt_latent = cloner.load_speaker_embedding(embedding_path)

        # 生成语音
        text = "这是使用预保存的说话人嵌入生成的语音。"
        output_path = "samples/output_from_embedding.wav"

        cloner.speak_with_embedding(
            text, speaker_emb, gpt_latent, output_path, "zh-cn"
        )

        print(f"✓ 预存嵌入生成成功")
        print(f"  - 输出文件: {output_path}")

    except Exception as e:
        print(f"✗ 预存嵌入生成失败: {e}")


def test_multi_language():
    """测试多语言克隆"""
    print("\n" + "="*50)
    print("测试4: 多语言克隆")
    print("="*50)

    if not TTS_AVAILABLE:
        print("跳过: Coqui TTS 未安装")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    try:
        cloner = XTTSCloner()

        texts = {
            "zh-cn": "你好，这是中文语音。",
            "en": "Hello, this is English speech.",
            "ja": "こんにちは、これは日本語の音声です。",
        }

        outputs = cloner.clone_multi_language(
            texts, reference_audio, "samples/multilang"
        )

        print(f"✓ 多语言克隆成功")
        for output in outputs:
            print(f"  - {output}")

    except Exception as e:
        print(f"✗ 多语言克隆失败: {e}")


def test_long_text():
    """测试长文本"""
    print("\n" + "="*50)
    print("测试5: 长文本合成")
    print("="*50)

    if not TTS_AVAILABLE:
        print("跳过: Coqui TTS 未安装")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    try:
        cloner = XTTSCloner()

        long_text = """
        这是一段较长的测试文本，用于验证 XTTS 在处理长文本时的表现。
        语音合成技术近年来取得了显著进展，零样本语音克隆让我们只需几秒钟的参考音频，
        就能生成与目标说话人声音相似的语音。这对于有声书制作、视频配音等应用场景非常有价值。
        """

        output_path = "samples/output_long.wav"
        cloner.clone_and_speak(long_text.strip(), reference_audio, output_path, "zh-cn")

        print(f"✓ 长文本合成成功")
        print(f"  - 输出文件: {output_path}")

    except Exception as e:
        print(f"✗ 长文本合成失败: {e}")


def main():
    """运行所有测试"""
    print("="*60)
    print("Coqui XTTS-v2 语音克隆测试套件")
    print("="*60)

    print("\n准备工作:")
    print("1. 安装 TTS: pip install TTS")
    print("2. 准备参考音频: samples/reference.wav (6-30秒)")

    os.makedirs("samples", exist_ok=True)

    test_basic_clone()
    test_embedding_extraction()
    test_speak_with_embedding()
    test_multi_language()
    test_long_text()

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
