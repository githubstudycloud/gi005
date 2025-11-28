"""
Fish-Speech 语音克隆测试脚本
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice_cloner import (
    FishSpeechCloner,
    FishSpeechAPI,
    FishSpeechLocal,
    FISH_SPEECH_AVAILABLE
)


def test_local_clone():
    """测试本地克隆"""
    print("\n" + "="*50)
    print("测试1: 本地语音克隆")
    print("="*50)

    if not FISH_SPEECH_AVAILABLE:
        print("跳过: Fish-Speech 未安装")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    try:
        cloner = FishSpeechCloner()

        text = "这是一段测试语音，验证 Fish-Speech 的克隆效果。"
        output_path = "samples/output_local.wav"

        cloner.clone(
            text=text,
            reference_audio=reference_audio,
            output_path=output_path
        )

        print(f"✓ 本地克隆成功: {output_path}")

    except Exception as e:
        print(f"✗ 本地克隆失败: {e}")


def test_api_clone():
    """测试 API 克隆"""
    print("\n" + "="*50)
    print("测试2: API 语音克隆")
    print("="*50)

    # 检查 API Key
    api_key = os.environ.get('FISH_AUDIO_API_KEY')
    if not api_key:
        print("跳过: 未设置 FISH_AUDIO_API_KEY 环境变量")
        print("设置方法: export FISH_AUDIO_API_KEY=your-key")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    try:
        api = FishSpeechAPI(api_key=api_key)

        text = "这是通过 API 合成的语音。"
        output_path = "samples/output_api.wav"

        api.clone(
            text=text,
            reference_audio=reference_audio,
            output_path=output_path
        )

        print(f"✓ API 克隆成功: {output_path}")

    except Exception as e:
        print(f"✗ API 克隆失败: {e}")


def test_multilingual():
    """测试多语言合成"""
    print("\n" + "="*50)
    print("测试3: 多语言合成")
    print("="*50)

    if not FISH_SPEECH_AVAILABLE:
        print("跳过: Fish-Speech 未安装")
        return

    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    texts = {
        "zh": "你好，这是中文测试。",
        "en": "Hello, this is an English test.",
        "ja": "こんにちは、これは日本語テストです。"
    }

    try:
        cloner = FishSpeechCloner()

        os.makedirs("samples/multilang", exist_ok=True)

        for lang, text in texts.items():
            output_path = f"samples/multilang/output_{lang}.wav"
            try:
                cloner.clone(
                    text=text,
                    reference_audio=reference_audio,
                    output_path=output_path,
                    language=lang
                )
                print(f"✓ {lang}: {output_path}")
            except Exception as e:
                print(f"✗ {lang} 失败: {e}")

    except Exception as e:
        print(f"✗ 多语言测试失败: {e}")


def test_preset_voices():
    """测试预设音色"""
    print("\n" + "="*50)
    print("测试4: 预设音色")
    print("="*50)

    api_key = os.environ.get('FISH_AUDIO_API_KEY')
    if not api_key:
        print("跳过: 未设置 FISH_AUDIO_API_KEY")
        return

    try:
        api = FishSpeechAPI(api_key=api_key)

        # 获取预设音色列表
        voices = api.list_voices()
        print(f"可用预设音色: {len(voices)} 个")

        if voices:
            # 使用第一个预设音色
            voice = voices[0]
            print(f"使用音色: {voice.get('name', voice.get('id'))}")

            text = "这是使用预设音色合成的语音。"
            output_path = "samples/output_preset.wav"

            api.clone_with_preset(
                text=text,
                voice_id=voice['id'],
                output_path=output_path
            )

            print(f"✓ 预设音色合成成功: {output_path}")

    except Exception as e:
        print(f"✗ 预设音色测试失败: {e}")


def test_cross_lingual():
    """测试跨语言合成"""
    print("\n" + "="*50)
    print("测试5: 跨语言合成")
    print("="*50)

    if not FISH_SPEECH_AVAILABLE:
        print("跳过: Fish-Speech 未安装")
        return

    # 使用中文参考音频合成英文
    reference_audio = "samples/reference.wav"  # 假设是中文
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    try:
        cloner = FishSpeechCloner()

        # 用中文音色说英文
        text_en = "Hello, this is cross-lingual synthesis."
        output_path = "samples/output_cross_lingual.wav"

        cloner.clone(
            text=text_en,
            reference_audio=reference_audio,
            output_path=output_path,
            language="en"
        )

        print(f"✓ 跨语言合成成功: {output_path}")

    except Exception as e:
        print(f"✗ 跨语言合成失败: {e}")


def main():
    """运行所有测试"""
    print("="*60)
    print("Fish-Speech 语音克隆测试套件")
    print("="*60)

    print("\n准备工作:")
    print("1. 安装 Fish-Speech (本地推理)")
    print("2. 或设置 FISH_AUDIO_API_KEY 环境变量 (API)")
    print("3. 准备参考音频: samples/reference.wav (10-30秒)")

    os.makedirs("samples", exist_ok=True)

    test_local_clone()
    test_api_clone()
    test_multilingual()
    test_preset_voices()
    test_cross_lingual()

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
