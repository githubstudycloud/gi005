"""
NeMo MSDD Speaker Diarization 测试脚本

用法:
    python examples/test_nemo_msdd.py <audio_file> [options]

示例:
    # 自动检测说话人数量
    python examples/test_nemo_msdd.py test_audio.wav

    # 指定说话人数量
    python examples/test_nemo_msdd.py test_audio.wav --num-speakers 3

    # 使用 CPU
    python examples/test_nemo_msdd.py test_audio.wav --device cpu
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from diarization import NeMoMSDDDiarizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_nemo_msdd(
    audio_path: str,
    num_speakers: int = None,
    device: str = "cuda",
    output_dir: str = "./outputs/nemo_msdd_test"
):
    """
    测试 NeMo MSDD 说话人分离

    Args:
        audio_path: 音频文件路径
        num_speakers: 说话人数量（None 表示自动检测）
        device: 计算设备
        output_dir: 输出目录
    """
    print("=" * 70)
    print("NeMo MSDD Speaker Diarization Test")
    print("=" * 70)
    print(f"Audio file: {audio_path}")
    print(f"Device: {device}")
    print(f"Num speakers: {num_speakers if num_speakers else 'auto-detect'}")
    print(f"Output directory: {output_dir}")
    print("-" * 70)

    try:
        # 1. 创建分离器
        print("\n[Step 1/3] Initializing NeMo MSDD Diarizer...")
        diarizer = NeMoMSDDDiarizer(
            device=device,
            output_dir=output_dir
        )

        # 2. 加载模型
        print("[Step 2/3] Loading models (this may take a few minutes)...")
        print("  - VAD Model: vad_multilingual_marblenet")
        print("  - Speaker Embedding: titanet_large")
        print("  - MSDD Model: diar_msdd_telephonic")

        diarizer.load_model()

        # 3. 执行分离
        print("\n[Step 3/3] Running speaker diarization...")
        result = diarizer.diarize(
            audio_path=audio_path,
            num_speakers=num_speakers,
            oracle_vad=False
        )

        # 4. 显示结果
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        output = diarizer.format_output(result, format_type="detailed")
        print(output)

        # 5. 保存 JSON 结果
        json_output_path = Path(output_dir) / "result.json"
        json_output = diarizer.format_output(result, format_type="json")
        with open(json_output_path, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"\nJSON result saved to: {json_output_path}")

        print("\n" + "=" * 70)
        print("Test completed successfully!")
        print("=" * 70)

    except ImportError as e:
        print("\n" + "!" * 70)
        print("ERROR: NeMo toolkit not installed")
        print("!" * 70)
        print("\nPlease install NeMo with the following commands:\n")
        print("  # Install system dependencies (Ubuntu/Debian)")
        print("  sudo apt-get install sox libsndfile1 ffmpeg")
        print()
        print("  # Install NeMo toolkit")
        print("  pip install nemo_toolkit[asr]")
        print()
        print("  # Or install from source for latest version:")
        print("  pip install git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[asr]")
        print("\n" + "!" * 70)
        sys.exit(1)

    except FileNotFoundError as e:
        print(f"\nERROR: Audio file not found: {audio_path}")
        sys.exit(1)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test NeMo MSDD Speaker Diarization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect number of speakers
  python %(prog)s test_audio.wav

  # Specify number of speakers
  python %(prog)s test_audio.wav --num-speakers 3

  # Use CPU instead of GPU
  python %(prog)s test_audio.wav --device cpu

  # Custom output directory
  python %(prog)s test_audio.wav --output-dir ./my_results
        """
    )

    parser.add_argument(
        "audio_path",
        type=str,
        help="Path to audio file (WAV, MP3, FLAC, etc.)"
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        default=None,
        help="Number of speakers (default: auto-detect)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device to use (default: cuda)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./outputs/nemo_msdd_test",
        help="Output directory (default: ./outputs/nemo_msdd_test)"
    )

    args = parser.parse_args()

    # 检查音频文件是否存在
    if not Path(args.audio_path).exists():
        print(f"ERROR: Audio file not found: {args.audio_path}")
        sys.exit(1)

    # 运行测试
    test_nemo_msdd(
        audio_path=args.audio_path,
        num_speakers=args.num_speakers,
        device=args.device,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
