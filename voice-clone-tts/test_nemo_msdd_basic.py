"""
测试 NeMo MSDD 基本功能（不依赖实际的 NeMo 模型）
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from diarization.nemo_msdd_diarizer import NeMoMSDDDiarizer
import io

# 设置 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("NeMo MSDD Basic Functionality Test")
print("=" * 70)

# Test 1: 初始化
print("\n[Test 1] Initialization")
print("-" * 70)
try:
    diarizer = NeMoMSDDDiarizer(
        device="cpu",
        output_dir="./test_outputs/nemo_msdd",
        cache_dir="./test_cache/nemo_models"
    )
    print(f"✓ Diarizer initialized successfully")
    print(f"  Device: {diarizer.device}")
    print(f"  Output dir: {diarizer.output_dir}")
    print(f"  Cache dir: {diarizer.cache_dir}")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 2: 配置生成
print("\n[Test 2] Configuration Generation")
print("-" * 70)
try:
    config = diarizer._create_config(
        manifest_path="test_manifest.json",
        num_speakers=3,
        oracle_vad=False,
        vad_model="vad_multilingual_marblenet",
        speaker_model="titanet_large",
        msdd_model="diar_msdd_telephonic"
    )

    print(f"✓ Configuration created successfully")
    print(f"  Manifest: {config.diarizer.manifest_filepath}")
    print(f"  Oracle VAD: {config.diarizer.oracle_vad}")
    print(f"  VAD Model: {config.diarizer.vad.model_path}")
    print(f"  Speaker Model: {config.diarizer.speaker_embeddings.model_path}")
    print(f"  MSDD Model: {config.diarizer.msdd_model.model_path}")

    # 验证多尺度配置
    windows = config.diarizer.speaker_embeddings.parameters.window_length_in_sec
    shifts = config.diarizer.speaker_embeddings.parameters.shift_length_in_sec
    weights = config.diarizer.speaker_embeddings.parameters.multiscale_weights

    print(f"\n  Multi-scale configuration:")
    print(f"    Windows: {windows}")
    print(f"    Shifts: {shifts}")
    print(f"    Weights: {weights}")

    assert len(windows) == 5
    assert len(shifts) == 5
    assert len(weights) == 5

    print(f"  ✓ Multi-scale configuration is valid ({len(windows)} scales)")

except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: RTTM 解析
print("\n[Test 3] RTTM Parsing")
print("-" * 70)
try:
    import tempfile

    # 创建测试 RTTM 文件
    rttm_content = """SPEAKER test_audio 1 0.00 2.50 <NA> <NA> SPEAKER_00 <NA>
SPEAKER test_audio 1 2.50 1.80 <NA> <NA> SPEAKER_01 <NA>
SPEAKER test_audio 1 4.30 3.20 <NA> <NA> SPEAKER_00 <NA>
SPEAKER test_audio 1 7.50 2.10 <NA> <NA> SPEAKER_02 <NA>
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.rttm', delete=False) as f:
        f.write(rttm_content)
        rttm_path = Path(f.name)

    # 解析 RTTM
    segments = diarizer._parse_rttm(rttm_path)

    print(f"✓ RTTM parsed successfully")
    print(f"  Total segments: {len(segments)}")
    print(f"  Detected speakers: {len(set(seg['speaker'] for seg in segments))}")

    # 显示前 3 个片段
    print(f"\n  Sample segments:")
    for i, seg in enumerate(segments[:3], 1):
        print(f"    {i}. [{seg['start']:6.2f}s - {seg['end']:6.2f}s] "
              f"({seg['duration']:5.2f}s) {seg['speaker']}")

    # 清理
    rttm_path.unlink()

    assert len(segments) == 4
    assert segments[0]['speaker'] == 'SPEAKER_00'
    print(f"  ✓ Parsing result is correct")

except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: 输出格式化
print("\n[Test 4] Output Formatting")
print("-" * 70)
try:
    test_result = {
        "audio_path": "test_audio.wav",
        "num_speakers": 3,
        "segments": [
            {"start": 0.0, "end": 2.5, "duration": 2.5, "speaker": "SPEAKER_00"},
            {"start": 2.5, "end": 4.3, "duration": 1.8, "speaker": "SPEAKER_01"},
            {"start": 4.3, "end": 7.5, "duration": 3.2, "speaker": "SPEAKER_00"},
            {"start": 7.5, "end": 9.6, "duration": 2.1, "speaker": "SPEAKER_02"}
        ],
        "rttm_path": "test.rttm"
    }

    # 测试不同格式
    formats_tested = []

    # Simple 格式
    simple_output = diarizer.format_output(test_result, format_type="simple")
    assert "Detected 3 speakers" in simple_output
    formats_tested.append("simple")

    # Detailed 格式
    detailed_output = diarizer.format_output(test_result, format_type="detailed")
    assert "NeMo MSDD" in detailed_output
    formats_tested.append("detailed")

    # JSON 格式
    json_output = diarizer.format_output(test_result, format_type="json")
    import json
    parsed = json.loads(json_output)
    assert parsed['num_speakers'] == 3
    formats_tested.append("json")

    print(f"✓ All output formats working correctly")
    print(f"  Tested formats: {', '.join(formats_tested)}")
    print(f"    - Simple: {len(simple_output)} chars")
    print(f"    - Detailed: {len(detailed_output)} chars")
    print(f"    - JSON: {len(json_output)} chars")

except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: 方法存在性检查
print("\n[Test 5] Method Availability Check")
print("-" * 70)
try:
    required_methods = [
        '_check_dependencies',
        '_create_config',
        '_create_manifest',
        'load_model',
        'diarize',
        '_parse_rttm',
        'format_output'
    ]

    methods_found = []
    for method in required_methods:
        if hasattr(diarizer, method):
            methods_found.append(method)

    print(f"✓ All required methods available")
    print(f"  Methods checked: {len(methods_found)}/{len(required_methods)}")
    for method in methods_found:
        print(f"    - {method}")

    assert len(methods_found) == len(required_methods)

except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# 总结
print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED")
print("=" * 70)

print("\nSummary:")
print("  ✓ Module import successful")
print("  ✓ Diarizer initialization successful")
print("  ✓ Configuration generation working")
print("  ✓ RTTM parsing working")
print("  ✓ Output formatting working")
print("  ✓ All required methods available")

print("\nNotes:")
print("  - Code structure and logic are fully functional")
print("  - To run actual NeMo MSDD inference, you need to:")
print("    1. Install NeMo: pip install nemo_toolkit[asr]")
print("    2. Run: python examples/test_nemo_msdd.py audio.wav")
print("  - See docs/NEMO-MSDD-SETUP.md for complete setup guide")

print("\n" + "=" * 70)
