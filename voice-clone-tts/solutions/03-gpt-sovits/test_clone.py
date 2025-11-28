"""
GPT-SoVITS 语音克隆测试脚本
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice_cloner import GPTSoVITSClient


def test_basic_synthesis():
    """测试基本合成"""
    print("\n" + "="*50)
    print("测试1: 基本语音合成")
    print("="*50)

    try:
        client = GPTSoVITSClient()
    except Exception as e:
        print(f"跳过: 无法连接服务 - {e}")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    try:
        text = "这是一段测试语音，验证 GPT-SoVITS 的合成效果。"
        output_path = "samples/output_basic.wav"

        client.synthesize(
            text=text,
            reference_audio=reference_audio,
            language="zh",
            output_path=output_path
        )

        print(f"✓ 基本合成成功: {output_path}")

    except Exception as e:
        print(f"✗ 基本合成失败: {e}")


def test_with_reference_text():
    """测试带参考文本的合成"""
    print("\n" + "="*50)
    print("测试2: 带参考文本合成")
    print("="*50)

    try:
        client = GPTSoVITSClient()
    except Exception as e:
        print(f"跳过: 无法连接服务 - {e}")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在")
        return

    try:
        text = "提供参考文本可以帮助模型更好地理解说话风格。"
        reference_text = "这是参考音频中说的内容。"  # 应与实际参考音频匹配

        output_path = "samples/output_with_ref_text.wav"

        client.synthesize(
            text=text,
            reference_audio=reference_audio,
            reference_text=reference_text,
            language="zh",
            output_path=output_path
        )

        print(f"✓ 带参考文本合成成功: {output_path}")

    except Exception as e:
        print(f"✗ 合成失败: {e}")


def test_speed_control():
    """测试语速控制"""
    print("\n" + "="*50)
    print("测试3: 语速控制")
    print("="*50)

    try:
        client = GPTSoVITSClient()
    except Exception as e:
        print(f"跳过: 无法连接服务 - {e}")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在")
        return

    text = "这段语音用于测试不同语速的效果。"
    speeds = [0.8, 1.0, 1.2]

    for speed in speeds:
        try:
            output_path = f"samples/output_speed_{speed}.wav"
            client.synthesize(
                text=text,
                reference_audio=reference_audio,
                language="zh",
                output_path=output_path,
                speed=speed
            )
            print(f"✓ 语速 {speed}x: {output_path}")
        except Exception as e:
            print(f"✗ 语速 {speed}x 失败: {e}")


def test_multilingual():
    """测试多语言合成"""
    print("\n" + "="*50)
    print("测试4: 多语言合成")
    print("="*50)

    try:
        client = GPTSoVITSClient()
    except Exception as e:
        print(f"跳过: 无法连接服务 - {e}")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在")
        return

    texts = {
        "zh": "这是中文语音合成测试。",
        "en": "This is an English speech synthesis test.",
        "ja": "これは日本語音声合成テストです。"
    }

    os.makedirs("samples/multilang", exist_ok=True)

    for lang, text in texts.items():
        try:
            output_path = f"samples/multilang/output_{lang}.wav"
            client.synthesize(
                text=text,
                reference_audio=reference_audio,
                language=lang,
                output_path=output_path
            )
            print(f"✓ {lang}: {output_path}")
        except Exception as e:
            print(f"✗ {lang} 失败: {e}")


def test_long_text():
    """测试长文本合成"""
    print("\n" + "="*50)
    print("测试5: 长文本合成")
    print("="*50)

    try:
        client = GPTSoVITSClient()
    except Exception as e:
        print(f"跳过: 无法连接服务 - {e}")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在")
        return

    long_text = """
    GPT-SoVITS 是一个强大的少样本语音克隆工具。
    它结合了 GPT 的语言理解能力和 SoVITS 的语音合成能力。
    只需要一分钟的训练数据就可以微调出高质量的个人音色模型。
    在零样本模式下，五秒钟的参考音频就足以进行语音合成。
    这使得 GPT-SoVITS 在个人使用和商业应用中都非常有价值。
    """.strip()

    try:
        output_path = "samples/output_long.wav"
        client.synthesize_stream(
            text=long_text,
            reference_audio=reference_audio,
            language="zh",
            output_path=output_path
        )
        print(f"✓ 长文本合成成功: {output_path}")
    except Exception as e:
        print(f"✗ 长文本合成失败: {e}")


def main():
    """运行所有测试"""
    print("="*60)
    print("GPT-SoVITS 语音克隆测试套件")
    print("="*60)

    print("\n准备工作:")
    print("1. 安装 GPT-SoVITS")
    print("2. 启动 API: python api_v2.py -a 127.0.0.1 -p 9880")
    print("3. 准备参考音频: samples/reference.wav (3-10秒)")

    os.makedirs("samples", exist_ok=True)

    test_basic_synthesis()
    test_with_reference_text()
    test_speed_control()
    test_multilingual()
    test_long_text()

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
