# NeMo MSDD 说话人分离示例

本目录包含 NeMo MSDD 说话人分离的测试示例。

## 文件说明

- `test_nemo_msdd.py` - NeMo MSDD 测试脚本

## 安装

### 自动安装（推荐）

**Linux/WSL2:**
```bash
cd voice-clone-tts
chmod +x scripts/install_nemo_msdd.sh
./scripts/install_nemo_msdd.sh
```

**Windows:**
```cmd
cd voice-clone-tts
scripts\install_nemo_msdd.bat
```

### 手动安装

```bash
# 1. 安装系统依赖（Ubuntu/WSL2）
sudo apt-get install sox libsndfile1 ffmpeg

# 2. 安装 Python 依赖
pip install Cython
pip install nemo_toolkit[asr]

# 或使用项目依赖文件
pip install -r requirements-nemo-msdd.txt
```

## 快速开始

### 1. 准备测试音频

使用任意包含多个说话人的音频文件（WAV, MP3, FLAC 等格式）。

示例音频要求：
- 采样率：建议 16kHz 或更高
- 声道：单声道或立体声
- 时长：建议 10 秒以上，以便观察效果

### 2. 运行测试

```bash
cd voice-clone-tts

# 基本用法（自动检测说话人数）
python examples/test_nemo_msdd.py path/to/audio.wav

# 指定说话人数量
python examples/test_nemo_msdd.py audio.wav --num-speakers 3

# 使用 CPU
python examples/test_nemo_msdd.py audio.wav --device cpu

# 自定义输出目录
python examples/test_nemo_msdd.py audio.wav --output-dir ./my_results
```

### 3. 查看结果

运行后会生成以下输出：

```
outputs/nemo_msdd_test/
├── input_manifest.json          # 输入清单
├── pred_rttms/                  # RTTM 输出
│   └── audio.rttm
└── result.json                  # JSON 格式结果
```

## 输出示例

### 终端输出

```
======================================================================
NeMo MSDD Speaker Diarization Results
======================================================================
Audio: test_audio.wav
Detected speakers: 3
Total segments: 45
RTTM file: outputs/nemo_msdd_test/pred_rttms/test_audio.rttm
----------------------------------------------------------------------
  1. [  0.00s -   2.50s] ( 2.50s) | Speaker: SPEAKER_00
  2. [  2.50s -   4.30s] ( 1.80s) | Speaker: SPEAKER_01
  3. [  4.30s -   7.50s] ( 3.20s) | Speaker: SPEAKER_00
  ...
```

### JSON 输出

```json
{
  "audio_path": "test_audio.wav",
  "num_speakers": 3,
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "duration": 2.5,
      "speaker": "SPEAKER_00"
    },
    {
      "start": 2.5,
      "end": 4.3,
      "duration": 1.8,
      "speaker": "SPEAKER_01"
    }
  ],
  "rttm_path": "outputs/nemo_msdd_test/pred_rttms/test_audio.rttm"
}
```

## Python API 使用

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from diarization import NeMoMSDDDiarizer

# 创建分离器
diarizer = NeMoMSDDDiarizer(
    device="cuda",  # 或 "cpu"
    output_dir="./outputs/diarization"
)

# 加载模型（首次运行会下载模型）
print("Loading models...")
diarizer.load_model()

# 执行说话人分离
print("Running diarization...")
result = diarizer.diarize(
    audio_path="test_audio.wav",
    num_speakers=None  # None=自动检测，或指定如 3
)

# 显示结果
print(f"\n检测到 {result['num_speakers']} 个说话人")
print(f"共 {len(result['segments'])} 个片段\n")

for i, seg in enumerate(result['segments'][:10], 1):  # 显示前 10 个
    print(f"{i:2d}. [{seg['start']:6.2f}s - {seg['end']:6.2f}s] "
          f"({seg['duration']:5.2f}s) {seg['speaker']}")

# 保存为 JSON
import json
with open("result.json", "w") as f:
    json.dump(result, f, indent=2)
```

## 常见问题

### Q: 首次运行很慢？

A: 首次运行时 NeMo 会下载以下模型（约 140MB）：
- vad_multilingual_marblenet (~20MB)
- titanet_large (~90MB)
- diar_msdd_telephonic (~30MB)

模型会缓存到 `~/.cache/torch/NeMo/`，后续运行会快很多。

**国内用户加速**：
```bash
export HF_ENDPOINT=https://hf-mirror.com
python examples/test_nemo_msdd.py audio.wav
```

### Q: CUDA out of memory？

A: 使用 CPU 或减少音频长度：
```bash
# 使用 CPU
python examples/test_nemo_msdd.py audio.wav --device cpu

# 或分段处理长音频（手动切分）
```

### Q: 分离结果不准确？

A: 可以尝试以下调优：

1. **指定说话人数量**（如果已知）：
```bash
python examples/test_nemo_msdd.py audio.wav --num-speakers 3
```

2. **使用 Python API 调整参数**：
```python
from omegaconf import OmegaConf

# 创建自定义配置
config = diarizer._create_config(
    manifest_path="temp.json",
    num_speakers=3
)

# 调整聚类阈值
config.diarizer.clustering.parameters.max_rp_threshold = 0.20  # 默认 0.25

# 调整 MSDD 阈值
config.diarizer.msdd_model.parameters.sigmoid_threshold = [0.6, 1.0]  # 默认 [0.7, 1.0]

diarizer.load_model(config)
```

3. **预处理音频**（增强音质）：
- 去噪
- 重采样到 16kHz
- 转换为单声道

### Q: 支持的音频格式？

A: 支持所有 torchaudio 支持的格式：
- WAV
- MP3
- FLAC
- OGG
- M4A

建议使用 WAV（16kHz，单声道）以获得最佳效果。

## 性能参考

在 NVIDIA RTX 3090 上的测试：

| 音频时长 | 处理时间 (GPU) | 处理时间 (CPU) |
|----------|----------------|----------------|
| 1 分钟   | ~10 秒         | ~2 分钟        |
| 5 分钟   | ~30 秒         | ~8 分钟        |
| 30 分钟  | ~3 分钟        | ~45 分钟       |

*注: 首次运行包含模型下载和初始化时间*

## 更多文档

- **完整安装指南**: `../docs/NEMO-MSDD-SETUP.md`
- **v3 方案文档**: `../docs/SPEAKER-DIARIZATION-V3-SOLUTION.md`
- **NeMo 官方文档**: https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/intro.html

## 许可证

本示例代码基于 NeMo 开源项目，遵循 Apache 2.0 许可证。
