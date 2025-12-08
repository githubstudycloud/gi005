"""
NeMo MSDD API 使用演示
展示如何使用 NeMo MSDD 进行说话人分离
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("=" * 70)
print("NeMo MSDD Speaker Diarization API Demo")
print("=" * 70)

# 演示 1: 基本用法
print("\n[Demo 1] Basic Usage")
print("-" * 70)
code_demo_1 = '''
from voice_clone_tts.src.diarization import NeMoMSDDDiarizer

# 创建分离器
diarizer = NeMoMSDDDiarizer(
    device="cuda",  # 或 "cpu"
    output_dir="./outputs/diarization"
)

# 加载模型（首次运行会自动下载）
print("Loading models...")
diarizer.load_model()

# 执行说话人分离
print("Running diarization...")
result = diarizer.diarize(
    audio_path="meeting_recording.wav",
    num_speakers=None  # None = 自动检测
)

# 显示结果
print(f"\\n检测到 {result['num_speakers']} 个说话人")
print(f"共 {len(result['segments'])} 个片段\\n")

for i, seg in enumerate(result['segments'][:10], 1):
    print(f"{i:2d}. [{seg['start']:6.2f}s - {seg['end']:6.2f}s] "
          f"({seg['duration']:5.2f}s) {seg['speaker']}")
'''
print(code_demo_1)

# 演示 2: 指定说话人数量
print("\n[Demo 2] Specify Number of Speakers")
print("-" * 70)
code_demo_2 = '''
# 如果已知说话人数量，可以提高准确度
result = diarizer.diarize(
    audio_path="interview_2speakers.wav",
    num_speakers=2  # 明确指定 2 个说话人
)
'''
print(code_demo_2)

# 演示 3: 自定义配置
print("\n[Demo 3] Custom Configuration")
print("-" * 70)
code_demo_3 = '''
from omegaconf import OmegaConf

# 创建自定义配置
config = diarizer._create_config(
    manifest_path="temp.json",
    num_speakers=3
)

# 调整聚类阈值（解决同一人被分成多人的问题）
config.diarizer.clustering.parameters.max_rp_threshold = 0.20  # 默认 0.25

# 调整 MSDD 阈值（调整重叠说话检测灵敏度）
config.diarizer.msdd_model.parameters.sigmoid_threshold = [0.6, 1.0]  # 默认 [0.7, 1.0]

# 使用自定义配置加载模型
diarizer.load_model(config)
'''
print(code_demo_3)

# 演示 4: 批量处理
print("\n[Demo 4] Batch Processing")
print("-" * 70)
code_demo_4 = '''
import glob
from pathlib import Path

# 创建分离器并加载模型（只需一次）
diarizer = NeMoMSDDDiarizer(device="cuda")
diarizer.load_model()

# 批量处理目录中的所有音频
audio_files = glob.glob("audio_dir/*.wav")
results = []

for audio_file in audio_files:
    print(f"\\nProcessing: {audio_file}")

    result = diarizer.diarize(audio_file)
    results.append(result)

    print(f"  Detected {result['num_speakers']} speakers")
    print(f"  RTTM saved to: {result['rttm_path']}")

# 保存汇总结果
import json
with open("batch_results.json", "w") as f:
    json.dump(results, f, indent=2)
'''
print(code_demo_4)

# 演示 5: 与 ASR 集成
print("\n[Demo 5] Integration with ASR")
print("-" * 70)
code_demo_5 = '''
# 1. 说话人分离
diarizer = NeMoMSDDDiarizer()
diarizer.load_model()
diar_result = diarizer.diarize("conversation.wav")

# 2. 语音识别（使用你的 ASR 系统）
# transcription = your_asr_system.transcribe("conversation.wav")

# 3. 合并结果：为每个说话人片段添加转录文本
for seg in diar_result['segments']:
    speaker = seg['speaker']
    start = seg['start']
    end = seg['end']

    # 提取该时间段的转录文本（示例）
    # text = get_text_in_timerange(transcription, start, end)

    print(f"{speaker} [{start:.2f}s - {end:.2f}s]: {text}")

# 输出示例：
# SPEAKER_00 [0.00s - 2.50s]: 大家好，欢迎参加今天的会议
# SPEAKER_01 [2.50s - 4.30s]: 谢谢，很高兴见到大家
# SPEAKER_00 [4.30s - 7.50s]: 今天我们主要讨论三个议题
'''
print(code_demo_5)

# 演示 6: 输出格式化
print("\n[Demo 6] Output Formatting")
print("-" * 70)
code_demo_6 = '''
# 获取分离结果
result = diarizer.diarize("audio.wav")

# 方式 1: 简单格式
simple_output = diarizer.format_output(result, format_type="simple")
print(simple_output)

# 方式 2: 详细格式
detailed_output = diarizer.format_output(result, format_type="detailed")
print(detailed_output)

# 方式 3: JSON 格式（便于程序处理）
json_output = diarizer.format_output(result, format_type="json")
with open("result.json", "w") as f:
    f.write(json_output)
'''
print(code_demo_6)

# 演示 7: 场景化参数推荐
print("\n[Demo 7] Scenario-based Parameter Recommendations")
print("-" * 70)

scenarios = {
    "meeting": {
        "description": "会议记录（2-8人）",
        "config": {
            "num_speakers": None,
            "max_num_speakers": 8,
            "max_rp_threshold": 0.25,
            "sigmoid_threshold": [0.7, 1.0]
        }
    },
    "interview": {
        "description": "访谈节目（2-3人）",
        "config": {
            "num_speakers": 2,
            "max_num_speakers": 3,
            "max_rp_threshold": 0.30,
            "sigmoid_threshold": [0.7, 1.0]
        }
    },
    "call_center": {
        "description": "客服录音（2人）",
        "config": {
            "num_speakers": 2,
            "max_num_speakers": 2,
            "max_rp_threshold": 0.35,
            "sigmoid_threshold": [0.6, 1.0]
        }
    },
    "noisy": {
        "description": "嘈杂环境",
        "config": {
            "num_speakers": None,
            "max_num_speakers": 5,
            "max_rp_threshold": 0.20,
            "vad_onset": 0.9,
            "vad_offset": 0.7
        }
    }
}

for scenario, info in scenarios.items():
    print(f"\n场景: {info['description']}")
    print(f"  推荐配置:")
    for key, value in info['config'].items():
        print(f"    - {key}: {value}")

# 总结
print("\n" + "=" * 70)
print("Demo completed!")
print("=" * 70)
print("\nNext steps:")
print("  1. Install dependencies:")
print("     pip install torch torchaudio nemo_toolkit[asr]")
print("  2. Run actual test:")
print("     python examples/test_nemo_msdd.py audio.wav")
print("  3. Read documentation:")
print("     docs/NEMO-MSDD-SETUP.md")
print("=" * 70)
