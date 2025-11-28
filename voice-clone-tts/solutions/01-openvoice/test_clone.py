"""
OpenVoice 音色克隆测试脚本

测试流程:
1. 从参考音频提取音色
2. 使用第三方TTS生成基础语音
3. 将基础语音转换为目标音色
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from voice_cloner import OpenVoiceCloner, OPENVOICE_AVAILABLE


def create_test_audio_with_edge_tts(text: str, output_path: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    """
    使用 edge-tts 生成测试音频

    需要安装: pip install edge-tts
    """
    try:
        import edge_tts
        import asyncio

        async def generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

        asyncio.run(generate())
        print(f"[edge-tts] 生成测试音频: {output_path}")
        return True
    except ImportError:
        print("edge-tts 未安装，请运行: pip install edge-tts")
        return False


def create_test_audio_with_gtts(text: str, output_path: str):
    """
    使用 gTTS 生成测试音频

    需要安装: pip install gtts
    """
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='zh-cn')
        tts.save(output_path)
        print(f"[gTTS] 生成测试音频: {output_path}")
        return True
    except ImportError:
        print("gTTS 未安装，请运行: pip install gtts")
        return False


def test_extract_tone_color():
    """测试音色提取"""
    print("\n" + "="*50)
    print("测试1: 音色提取")
    print("="*50)

    if not OPENVOICE_AVAILABLE:
        print("跳过: OpenVoice 未安装")
        return None

    # 检查参考音频
    reference_audio = "samples/reference.wav"
    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        print("请准备一段参考音频（5-30秒，清晰的人声）")
        return None

    try:
        cloner = OpenVoiceCloner()
        tone_embedding = cloner.extract_tone_color(reference_audio)

        # 保存音色
        embedding_path = "samples/extracted_tone.pt"
        cloner.save_tone_color(tone_embedding, embedding_path)

        print(f"✓ 音色提取成功")
        print(f"  - Embedding shape: {tone_embedding.shape}")
        print(f"  - 保存路径: {embedding_path}")
        return tone_embedding

    except Exception as e:
        print(f"✗ 音色提取失败: {e}")
        return None


def test_voice_conversion(tone_embedding=None):
    """测试音色转换"""
    print("\n" + "="*50)
    print("测试2: 音色转换")
    print("="*50)

    if not OPENVOICE_AVAILABLE:
        print("跳过: OpenVoice 未安装")
        return

    # 生成源音频（用于测试）
    source_audio = "samples/source_tts.wav"
    os.makedirs("samples", exist_ok=True)

    if not os.path.exists(source_audio):
        print("生成测试源音频...")
        text = "这是一段测试语音，用于验证音色转换效果。"

        # 尝试使用 edge-tts 或 gtts
        if not create_test_audio_with_edge_tts(text, source_audio):
            if not create_test_audio_with_gtts(text, source_audio):
                print("无法生成测试音频，请手动准备: samples/source_tts.wav")
                return

    # 加载或提取音色
    if tone_embedding is None:
        embedding_path = "samples/extracted_tone.pt"
        if os.path.exists(embedding_path):
            cloner = OpenVoiceCloner()
            tone_embedding = cloner.load_tone_color(embedding_path)
        else:
            print("跳过: 没有可用的音色嵌入")
            print("请先运行测试1提取音色")
            return

    try:
        cloner = OpenVoiceCloner()
        output_path = "samples/output_converted.wav"

        cloner.convert_voice(
            source_audio_path=source_audio,
            target_tone_embedding=tone_embedding,
            output_path=output_path
        )

        print(f"✓ 音色转换成功")
        print(f"  - 输出文件: {output_path}")

    except Exception as e:
        print(f"✗ 音色转换失败: {e}")


def test_end_to_end():
    """端到端测试"""
    print("\n" + "="*50)
    print("测试3: 端到端音色克隆")
    print("="*50)

    if not OPENVOICE_AVAILABLE:
        print("跳过: OpenVoice 未安装")
        return

    reference_audio = "samples/reference.wav"
    source_audio = "samples/source_tts.wav"

    if not os.path.exists(reference_audio):
        print(f"跳过: 参考音频不存在 {reference_audio}")
        return

    if not os.path.exists(source_audio):
        print(f"跳过: 源音频不存在 {source_audio}")
        return

    try:
        cloner = OpenVoiceCloner()
        output_path = "samples/output_e2e.wav"

        cloner.clone_voice(
            reference_audio=reference_audio,
            source_audio=source_audio,
            output_path=output_path,
            save_embedding="samples/saved_tone.pt"
        )

        print(f"✓ 端到端克隆成功")
        print(f"  - 输出文件: {output_path}")
        print(f"  - 音色保存: samples/saved_tone.pt")

    except Exception as e:
        print(f"✗ 端到端克隆失败: {e}")


def test_batch_conversion():
    """批量转换测试"""
    print("\n" + "="*50)
    print("测试4: 批量音色转换")
    print("="*50)

    if not OPENVOICE_AVAILABLE:
        print("跳过: OpenVoice 未安装")
        return

    embedding_path = "samples/saved_tone.pt"
    if not os.path.exists(embedding_path):
        print("跳过: 音色嵌入不存在")
        return

    try:
        cloner = OpenVoiceCloner()
        tone_embedding = cloner.load_tone_color(embedding_path)

        # 生成多段测试音频
        texts = [
            "第一段：今天天气真不错。",
            "第二段：我们一起去散步吧。",
            "第三段：晚饭吃什么好呢？",
        ]

        os.makedirs("samples/batch", exist_ok=True)

        for i, text in enumerate(texts):
            source_path = f"samples/batch/source_{i+1}.wav"
            output_path = f"samples/batch/output_{i+1}.wav"

            # 生成源音频
            if not os.path.exists(source_path):
                if not create_test_audio_with_edge_tts(text, source_path):
                    create_test_audio_with_gtts(text, source_path)

            if os.path.exists(source_path):
                cloner.convert_voice(
                    source_audio_path=source_path,
                    target_tone_embedding=tone_embedding,
                    output_path=output_path
                )

        print(f"✓ 批量转换完成")
        print(f"  - 输出目录: samples/batch/")

    except Exception as e:
        print(f"✗ 批量转换失败: {e}")


def main():
    """运行所有测试"""
    print("="*60)
    print("OpenVoice 音色克隆测试套件")
    print("="*60)

    print("\n准备工作:")
    print("1. 安装 OpenVoice: git clone + pip install -e .")
    print("2. 下载模型: checkpoints_v2/converter/")
    print("3. 准备参考音频: samples/reference.wav")
    print("4. (可选) 安装 edge-tts: pip install edge-tts")

    # 运行测试
    tone_embedding = test_extract_tone_color()
    test_voice_conversion(tone_embedding)
    test_end_to_end()
    test_batch_conversion()

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
