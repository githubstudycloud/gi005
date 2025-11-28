#!/usr/bin/env python
"""
音色克隆命令行工具和 main 入口

使用示例:

1. 提取音色:
   python main.py extract --engine xtts --audio reference.wav --voice-id my_voice

2. 合成语音:
   python main.py synthesize --engine xtts --voice-id my_voice --text "你好世界" --output output.wav

3. 列出音色:
   python main.py list --voices-dir ./voices

4. 启动 HTTP 服务:
   python main.py serve --engine xtts --port 8000
"""

import os
import sys
import argparse
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def get_cloner(engine: str, **kwargs):
    """获取克隆器实例"""
    if engine == "xtts":
        from xtts import XTTSCloner
        cloner = XTTSCloner(device=kwargs.get("device"))

    elif engine == "openvoice":
        from openvoice import OpenVoiceCloner
        cloner = OpenVoiceCloner(
            model_path=kwargs.get("model_path"),
            device=kwargs.get("device")
        )

    elif engine == "gpt-sovits":
        # 需要包装导入
        sys.path.insert(0, str(Path(__file__).parent / "gpt-sovits"))
        from cloner import GPTSoVITSCloner
        cloner = GPTSoVITSCloner(
            api_host=kwargs.get("api_host", "127.0.0.1"),
            api_port=kwargs.get("api_port", 9880)
        )

    else:
        raise ValueError(f"不支持的引擎: {engine}")

    cloner.load_model()
    return cloner


def cmd_extract(args):
    """提取音色命令"""
    print(f"提取音色: {args.audio}")
    print(f"引擎: {args.engine}")

    cloner = get_cloner(
        args.engine,
        model_path=args.model_path,
        device=args.device,
        api_host=args.api_host,
        api_port=args.api_port
    )

    voice = cloner.extract_voice(
        audio_path=args.audio,
        voice_id=args.voice_id,
        voice_name=args.voice_name,
        save_dir=args.voices_dir
    )

    print(f"\n音色已保存:")
    print(f"  ID: {voice.voice_id}")
    print(f"  名称: {voice.name}")
    print(f"  路径: {Path(args.voices_dir) / voice.voice_id}")


def cmd_synthesize(args):
    """合成语音命令"""
    print(f"合成语音: {args.text[:30]}...")
    print(f"音色: {args.voice_id}")
    print(f"引擎: {args.engine}")

    cloner = get_cloner(
        args.engine,
        model_path=args.model_path,
        device=args.device,
        api_host=args.api_host,
        api_port=args.api_port
    )

    voice_dir = Path(args.voices_dir) / args.voice_id

    if not voice_dir.exists():
        print(f"错误: 音色不存在 {args.voice_id}")
        sys.exit(1)

    output_path = cloner.synthesize(
        text=args.text,
        voice=str(voice_dir),
        output_path=args.output,
        language=args.language
    )

    print(f"\n合成完成: {output_path}")


def cmd_list(args):
    """列出音色命令"""
    from common.base import VoiceEmbedding

    voices_dir = Path(args.voices_dir)

    if not voices_dir.exists():
        print("音色目录不存在")
        return

    voices = []
    for voice_path in voices_dir.iterdir():
        if voice_path.is_dir():
            meta_path = voice_path / "voice.json"
            if meta_path.exists():
                try:
                    voice = VoiceEmbedding.load_meta(meta_path)
                    voices.append(voice)
                except Exception:
                    pass

    if not voices:
        print("没有已保存的音色")
        return

    print(f"已保存的音色 ({len(voices)} 个):\n")
    for v in voices:
        print(f"  ID: {v.voice_id}")
        print(f"    名称: {v.name}")
        print(f"    引擎: {v.engine}")
        print()


def cmd_serve(args):
    """启动 HTTP 服务"""
    import uvicorn

    # 设置环境变量
    os.environ["VOICE_ENGINE"] = args.engine
    os.environ["VOICE_HOST"] = args.host
    os.environ["VOICE_PORT"] = str(args.port)
    os.environ["VOICES_DIR"] = args.voices_dir
    if args.model_path:
        os.environ["MODEL_PATH"] = args.model_path
    if args.device:
        os.environ["DEVICE"] = args.device

    print(f"启动 HTTP 服务")
    print(f"  引擎: {args.engine}")
    print(f"  地址: http://{args.host}:{args.port}")

    from server import app
    uvicorn.run(app, host=args.host, port=args.port)


def cmd_quick(args):
    """快速克隆（提取+合成一步完成）"""
    print(f"快速克隆")
    print(f"  参考音频: {args.audio}")
    print(f"  文本: {args.text[:30]}...")
    print(f"  引擎: {args.engine}")

    cloner = get_cloner(
        args.engine,
        model_path=args.model_path,
        device=args.device,
        api_host=args.api_host,
        api_port=args.api_port
    )

    # XTTS 支持直接克隆
    if args.engine == "xtts" and hasattr(cloner, 'synthesize_simple'):
        output_path = cloner.synthesize_simple(
            text=args.text,
            reference_audio=args.audio,
            output_path=args.output,
            language=args.language
        )
    else:
        # 其他引擎：先提取再合成
        import tempfile
        temp_dir = tempfile.mkdtemp()

        voice = cloner.extract_voice(args.audio, save_dir=temp_dir)
        output_path = cloner.synthesize(
            text=args.text,
            voice=voice,
            output_path=args.output,
            language=args.language
        )

        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)

    print(f"\n克隆完成: {output_path}")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="音色克隆工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 公共参数
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--engine", type=str, default="xtts",
                               choices=["xtts", "openvoice", "gpt-sovits"],
                               help="TTS 引擎")
    common_parser.add_argument("--voices-dir", type=str, default="./voices",
                               help="音色存储目录")
    common_parser.add_argument("--model-path", type=str, default="",
                               help="模型路径")
    common_parser.add_argument("--device", type=str, default="",
                               help="计算设备")
    common_parser.add_argument("--api-host", type=str, default="127.0.0.1",
                               help="GPT-SoVITS API 地址")
    common_parser.add_argument("--api-port", type=int, default=9880,
                               help="GPT-SoVITS API 端口")

    # extract 命令
    extract_parser = subparsers.add_parser(
        "extract", parents=[common_parser],
        help="从音频提取音色"
    )
    extract_parser.add_argument("--audio", "-a", type=str, required=True,
                                help="参考音频路径")
    extract_parser.add_argument("--voice-id", "-i", type=str, default="",
                                help="音色ID")
    extract_parser.add_argument("--voice-name", "-n", type=str, default="",
                                help="音色名称")
    extract_parser.set_defaults(func=cmd_extract)

    # synthesize 命令
    synth_parser = subparsers.add_parser(
        "synthesize", parents=[common_parser],
        help="使用音色合成语音"
    )
    synth_parser.add_argument("--voice-id", "-i", type=str, required=True,
                              help="音色ID")
    synth_parser.add_argument("--text", "-t", type=str, required=True,
                              help="合成文本")
    synth_parser.add_argument("--output", "-o", type=str, default="output.wav",
                              help="输出文件")
    synth_parser.add_argument("--language", "-l", type=str, default="zh",
                              help="语言代码")
    synth_parser.set_defaults(func=cmd_synthesize)

    # list 命令
    list_parser = subparsers.add_parser(
        "list", parents=[common_parser],
        help="列出已保存的音色"
    )
    list_parser.set_defaults(func=cmd_list)

    # serve 命令
    serve_parser = subparsers.add_parser(
        "serve", parents=[common_parser],
        help="启动 HTTP 服务"
    )
    serve_parser.add_argument("--host", type=str, default="0.0.0.0",
                              help="服务地址")
    serve_parser.add_argument("--port", type=int, default=8000,
                              help="服务端口")
    serve_parser.set_defaults(func=cmd_serve)

    # quick 命令
    quick_parser = subparsers.add_parser(
        "quick", parents=[common_parser],
        help="快速克隆（一步完成）"
    )
    quick_parser.add_argument("--audio", "-a", type=str, required=True,
                              help="参考音频")
    quick_parser.add_argument("--text", "-t", type=str, required=True,
                              help="合成文本")
    quick_parser.add_argument("--output", "-o", type=str, default="output.wav",
                              help="输出文件")
    quick_parser.add_argument("--language", "-l", type=str, default="zh",
                              help="语言")
    quick_parser.set_defaults(func=cmd_quick)

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行命令
    args.func(args)


if __name__ == "__main__":
    main()
