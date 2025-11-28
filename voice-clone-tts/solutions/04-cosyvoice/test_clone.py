"""
CosyVoice 语音克隆测试脚本
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice_cloner import CosyVoiceCloner, COSYVOICE_AVAILABLE


def test_zero_shot():
    """测试零样本克隆"""
    print("\n" + "="*50)
    print("测试1: 零样本语音克隆")
    print("="*50)

    if not COSYVOICE_AVAILABLE:
        print("跳过: CosyVoice 未安装")
        return

    model_dir = "pretrained_models/CosyVoice-300M"
    if not os.path.exists(model_dir):
        print(f"跳过: 模型不存在 {model_dir}")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    try:
        cloner = CosyVoiceCloner(model_dir)

        text = "这是一段测试语音，验证零样本克隆效果。"
        reference_text = "这是参考音频中说的话。"

        output_path = "samples/output_zero_shot.wav"

        cloner.zero_shot_clone(
            text=text,
            reference_audio=reference_audio,
            reference_text=reference_text,
            output_path=output_path
        )

        print(f"✓ 零样本克隆成功: {output_path}")

    except Exception as e:
        print(f"✗ 零样本克隆失败: {e}")


def test_cross_lingual():
    """测试跨语言克隆"""
    print("\n" + "="*50)
    print("测试2: 跨语言克隆")
    print("="*50)

    if not COSYVOICE_AVAILABLE:
        print("跳过: CosyVoice 未安装")
        return

    model_dir = "pretrained_models/CosyVoice-300M"
    if not os.path.exists(model_dir):
        print(f"跳过: 模型不存在")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在")
        return

    try:
        cloner = CosyVoiceCloner(model_dir)

        # 用中文参考音频合成英文
        text_en = "Hello, this is a cross-lingual synthesis test."
        output_path = "samples/output_cross_lingual.wav"

        cloner.cross_lingual_clone(
            text=text_en,
            reference_audio=reference_audio,
            output_path=output_path
        )

        print(f"✓ 跨语言克隆成功: {output_path}")

    except Exception as e:
        print(f"✗ 跨语言克隆失败: {e}")


def test_sft():
    """测试 SFT 角色合成"""
    print("\n" + "="*50)
    print("测试3: SFT 角色合成")
    print("="*50)

    if not COSYVOICE_AVAILABLE:
        print("跳过: CosyVoice 未安装")
        return

    model_dir = "pretrained_models/CosyVoice-300M-SFT"
    if not os.path.exists(model_dir):
        print(f"跳过: SFT 模型不存在 {model_dir}")
        return

    try:
        cloner = CosyVoiceCloner(model_dir)

        # 列出可用角色
        speakers = cloner.list_sft_speakers()
        print(f"可用角色: {speakers}")

        if speakers:
            text = "这是使用预训练角色合成的语音。"
            output_path = "samples/output_sft.wav"

            cloner.sft_clone(
                text=text,
                speaker=speakers[0],
                output_path=output_path
            )

            print(f"✓ SFT 合成成功: {output_path}")
        else:
            print("没有可用的预训练角色")

    except Exception as e:
        print(f"✗ SFT 合成失败: {e}")


def test_instruct():
    """测试指令控制合成"""
    print("\n" + "="*50)
    print("测试4: 指令控制合成")
    print("="*50)

    if not COSYVOICE_AVAILABLE:
        print("跳过: CosyVoice 未安装")
        return

    model_dir = "pretrained_models/CosyVoice-300M-Instruct"
    if not os.path.exists(model_dir):
        print(f"跳过: Instruct 模型不存在 {model_dir}")
        return

    try:
        cloner = CosyVoiceCloner(model_dir)

        text = "今天真是美好的一天啊！"
        instructions = [
            ("开心的语气", "output_happy.wav"),
            ("悲伤的语气", "output_sad.wav"),
            ("愤怒的语气", "output_angry.wav"),
        ]

        for instruct, filename in instructions:
            output_path = f"samples/{filename}"
            try:
                cloner.instruct_clone(
                    text=text,
                    speaker="中文女",
                    instruct=instruct,
                    output_path=output_path
                )
                print(f"✓ {instruct}: {output_path}")
            except Exception as e:
                print(f"✗ {instruct} 失败: {e}")

    except Exception as e:
        print(f"✗ 指令控制初始化失败: {e}")


def test_stream():
    """测试流式合成"""
    print("\n" + "="*50)
    print("测试5: 流式合成")
    print("="*50)

    if not COSYVOICE_AVAILABLE:
        print("跳过: CosyVoice 未安装")
        return

    model_dir = "pretrained_models/CosyVoice-300M"
    if not os.path.exists(model_dir):
        print(f"跳过: 模型不存在")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在")
        return

    try:
        cloner = CosyVoiceCloner(model_dir)

        long_text = """
        流式合成适用于长文本场景。
        它可以边生成边播放，减少用户等待时间。
        这对于实时应用非常重要。
        """

        output_path = "samples/output_stream.wav"

        cloner.zero_shot_clone(
            text=long_text.strip(),
            reference_audio=reference_audio,
            reference_text="参考音频文本",
            output_path=output_path,
            stream=True
        )

        print(f"✓ 流式合成成功: {output_path}")

    except Exception as e:
        print(f"✗ 流式合成失败: {e}")


def main():
    """运行所有测试"""
    print("="*60)
    print("CosyVoice 语音克隆测试套件")
    print("="*60)

    print("\n准备工作:")
    print("1. 安装 CosyVoice")
    print("2. 下载模型到 pretrained_models/")
    print("3. 准备参考音频: samples/reference.wav (3-10秒)")

    os.makedirs("samples", exist_ok=True)

    test_zero_shot()
    test_cross_lingual()
    test_sft()
    test_instruct()
    test_stream()

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
