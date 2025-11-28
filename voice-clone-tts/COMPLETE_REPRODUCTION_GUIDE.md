# 音色克隆 TTS 完整复现指南

本文档提供从零开始复现整个项目的完整步骤。

---

## 目录

1. [环境要求](#一环境要求)
2. [下载代码和模型](#二下载代码和模型)
3. [还原模型文件](#三还原模型文件)
4. [安装依赖](#四安装依赖)
5. [验证安装](#五验证安装)
6. [使用示例](#六使用示例)
7. [常见问题](#七常见问题)

---

## 一、环境要求

### 1.1 硬件要求

| 配置 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 4 核 | 8 核+ |
| 内存 | 8GB | 16GB+ |
| 显存 | 4GB (CPU 模式可无) | 8GB+ NVIDIA GPU |
| 磁盘 | 20GB | 50GB+ |

### 1.2 软件要求

| 软件 | 版本 | 说明 |
|------|------|------|
| 操作系统 | Windows 10/11, Linux | macOS 未测试 |
| Python | 3.10.x | **必须是 3.10**，3.11+ 兼容性问题 |
| CUDA | 11.8 (可选) | GPU 加速需要 |
| Visual C++ Build Tools | 14.0+ | Windows 必需 |
| Git | 任意版本 | 下载代码 |
| FFmpeg | 任意版本 | 音频处理 |

---

## 二、下载代码和模型

### 2.1 克隆仓库

```bash
# 使用 Git 克隆（推荐）
git clone https://github.com/githubstudycloud/gi005.git
cd gi005

# 如果网络慢，可以使用代理
git clone --config http.proxy=http://your-proxy:port https://github.com/githubstudycloud/gi005.git
```

### 2.2 仓库结构

```
gi005/
├── voice-clone-tts/           # 主项目目录
│   ├── production/            # 生产环境代码
│   ├── COMPLETE_REPRODUCTION_GUIDE.md  # 本文档
│   ├── VERIFICATION_REPORT.md # 验证报告
│   └── PROJECT_SUMMARY.md     # 项目总结
│
├── tts_model/                 # XTTS-v2 模型
│   └── xtts_v2.tar.part_*    # 21 个分卷文件
│
├── offline_package/           # 离线部署包
│   ├── checkpoints_v2.tar.part_*  # OpenVoice 模型 (2 个分卷)
│   └── whisper_models.tar.part_*  # Whisper 模型 (16 个分卷)
│
├── OpenVoice/                 # OpenVoice 源码
├── GPT-SoVITS/               # GPT-SoVITS 源码（可选）
└── test_audio/               # 测试音频
```

---

## 三、还原模型文件

### 3.1 还原 XTTS-v2 模型

```bash
cd gi005/tts_model

# Linux/macOS/Git Bash
cat xtts_v2.tar.part_* | tar -xvf -

# Windows CMD
copy /b xtts_v2.tar.part_* xtts_v2.tar
tar -xvf xtts_v2.tar
del xtts_v2.tar
```

还原后目录结构：
```
tts_model/
└── xtts_v2/
    ├── config.json
    ├── model.pth
    ├── vocab.json
    ├── speakers_xtts.pth
    └── ...
```

### 3.2 还原 OpenVoice 模型

```bash
cd gi005/offline_package

# Linux/macOS/Git Bash
cat checkpoints_v2.tar.part_* | tar -xvf -
mv checkpoints_v2 ../

# Windows CMD
copy /b checkpoints_v2.tar.part_* checkpoints_v2.tar
tar -xvf checkpoints_v2.tar
move checkpoints_v2 ..\
del checkpoints_v2.tar
```

还原后目录结构：
```
checkpoints_v2/
├── converter/
│   ├── config.json
│   └── checkpoint.pth
└── base_speakers/
    └── ses/
        ├── en-us.pth
        └── zh.pth
```

### 3.3 还原 Whisper 模型（可选，OpenVoice VAD 需要）

```bash
cd gi005/offline_package

# Linux/macOS/Git Bash
cat whisper_models.tar.part_* | tar -xvf -
mv whisper_models ../

# Windows CMD
copy /b whisper_models.tar.part_* whisper_models.tar
tar -xvf whisper_models.tar
move whisper_models ..\
del whisper_models.tar
```

---

## 四、安装依赖

### 4.1 安装 Python 3.10

**Windows:**
1. 从 https://www.python.org/downloads/release/python-31011/ 下载
2. 安装时勾选 "Add Python to PATH"

**Linux:**
```bash
sudo apt install python3.10 python3.10-venv python3.10-dev
```

### 4.2 创建虚拟环境

```bash
cd gi005

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 4.3 安装 PyTorch

```bash
# GPU 版本 (CUDA 11.8)
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118

# CPU 版本
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
```

### 4.4 安装 TTS 库 (XTTS)

```bash
# 安装 TTS（可能需要几分钟）
pip install TTS==0.22.0

# 修复版本冲突
pip install "transformers<4.50"
```

### 4.5 安装 OpenVoice 依赖

```bash
# 进入 OpenVoice 目录安装
cd OpenVoice
pip install -e .
cd ..

# 安装额外依赖
pip install edge-tts
pip install ctranslate2==4.4.0  # 修复 CUDA 12 依赖问题
```

### 4.6 安装 FFmpeg

**Windows:**
1. 从 https://github.com/BtbN/FFmpeg-Builds/releases 下载
2. 解压到项目目录，确保 `ffmpeg.exe` 在 PATH 中

**Linux:**
```bash
sudo apt install ffmpeg
```

### 4.7 完整依赖列表

创建 `requirements.txt`:
```
torch==2.5.1
torchaudio==2.5.1
TTS==0.22.0
transformers==4.49.0
ctranslate2==4.4.0
faster-whisper==1.1.1
edge-tts==7.0.2
librosa==0.10.2
soundfile==0.13.1
numpy<2.0
pydub
```

---

## 五、验证安装

### 5.1 验证 XTTS-v2

创建 `test_xtts.py`:
```python
import os
os.environ['COQUI_TOS_AGREED'] = '1'

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

print("Loading XTTS model...")
config = XttsConfig()
config.load_json("tts_model/xtts_v2/config.json")

model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir="tts_model/xtts_v2/")
model.eval()

print("Extracting voice...")
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
    audio_path=["test_audio/sample_en.wav"]
)

print("Synthesizing...")
out = model.inference(
    text="Hello, this is a voice cloning test.",
    language="en",
    gpt_cond_latent=gpt_cond_latent,
    speaker_embedding=speaker_embedding
)

import soundfile as sf
sf.write("output_xtts.wav", out["wav"], 24000)
print(f"Output saved: output_xtts.wav ({os.path.getsize('output_xtts.wav')} bytes)")
print("XTTS test PASSED!")
```

运行：
```bash
python test_xtts.py
```

### 5.2 验证 OpenVoice

创建 `test_openvoice.py`:
```python
import sys
import os
sys.path.insert(0, 'OpenVoice')

from openvoice import se_extractor
from openvoice.api import ToneColorConverter
import torch

print("Loading OpenVoice model...")
converter = ToneColorConverter('checkpoints_v2/converter/config.json', device='cpu')
converter.load_ckpt('checkpoints_v2/converter/checkpoint.pth')

print("Extracting voice embedding...")
target_se, audio_name = se_extractor.get_se(
    'test_audio/sample_en.wav',
    converter,
    vad=True  # 使用 silero VAD，不需要 whisper
)
print(f"Target SE shape: {target_se.shape}")

print("Generating base audio with edge-tts...")
import edge_tts
import asyncio

async def generate_base():
    communicate = edge_tts.Communicate('Hello world, this is a voice cloning test.', 'en-US-AriaNeural')
    await communicate.save('base_audio.wav')

asyncio.run(generate_base())

print("Loading source embedding...")
src_se = torch.load('checkpoints_v2/base_speakers/ses/en-us.pth')

print("Converting voice...")
converter.convert(
    audio_src_path='base_audio.wav',
    src_se=src_se,
    tgt_se=target_se,
    output_path='output_openvoice.wav'
)

print(f"Output saved: output_openvoice.wav ({os.path.getsize('output_openvoice.wav')} bytes)")
print("OpenVoice test PASSED!")
```

运行：
```bash
python test_openvoice.py
```

---

## 六、使用示例

### 6.1 XTTS 快速使用

```python
import os
os.environ['COQUI_TOS_AGREED'] = '1'

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import soundfile as sf

# 加载模型
config = XttsConfig()
config.load_json("tts_model/xtts_v2/config.json")
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir="tts_model/xtts_v2/")
model.eval()

# 提取音色
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
    audio_path=["your_reference_audio.wav"]  # 3-10秒清晰语音
)

# 合成语音
result = model.inference(
    text="要合成的文本内容",
    language="zh",  # 支持: en, zh, ja, ko, fr, de, es, it, pt, pl, ru, nl, tr
    gpt_cond_latent=gpt_cond_latent,
    speaker_embedding=speaker_embedding
)

# 保存
sf.write("output.wav", result["wav"], 24000)
```

### 6.2 OpenVoice 快速使用

```python
import sys
sys.path.insert(0, 'OpenVoice')

from openvoice import se_extractor
from openvoice.api import ToneColorConverter
import torch
import edge_tts
import asyncio

# 加载模型
converter = ToneColorConverter('checkpoints_v2/converter/config.json', device='cpu')
converter.load_ckpt('checkpoints_v2/converter/checkpoint.pth')

# 提取目标音色
target_se, _ = se_extractor.get_se('your_reference_audio.wav', converter, vad=True)

# 生成基础音频
async def generate():
    tts = edge_tts.Communicate('要合成的文本', 'zh-CN-XiaoxiaoNeural')
    await tts.save('base.wav')
asyncio.run(generate())

# 转换音色
src_se = torch.load('checkpoints_v2/base_speakers/ses/zh.pth')  # 或 en-us.pth
converter.convert(
    audio_src_path='base.wav',
    src_se=src_se,
    tgt_se=target_se,
    output_path='output.wav'
)
```

---

## 七、常见问题

### Q1: Python 版本错误

**问题**: `pip install torch` 失败，找不到 wheel

**解决**: 必须使用 Python 3.10，不支持 3.11+
```bash
python --version  # 确认是 3.10.x
```

### Q2: transformers 导入错误

**问题**: `ImportError: cannot import name 'BeamSearchScorer'`

**解决**:
```bash
pip install "transformers<4.50"
```

### Q3: cublas64_12.dll 找不到

**问题**: `RuntimeError: Library cublas64_12.dll is not found`

**解决**:
```bash
pip install ctranslate2==4.4.0
```

### Q4: XTTS 许可确认阻塞

**问题**: 程序卡在许可确认

**解决**: 在代码开头添加：
```python
import os
os.environ['COQUI_TOS_AGREED'] = '1'
```

### Q5: HuggingFace 下载超时

**问题**: 模型下载失败

**解决**: 使用镜像
```bash
export HF_ENDPOINT=https://hf-mirror.com
# 或在 Windows 上
set HF_ENDPOINT=https://hf-mirror.com
```

### Q6: OpenVoice "audio too short"

**问题**: 音频太短错误

**解决**: 使用预训练的 base speaker SE，而不是从短音频提取
```python
src_se = torch.load('checkpoints_v2/base_speakers/ses/en-us.pth')
```

### Q7: Visual C++ 编译错误

**问题**: Windows 上安装 TTS 失败

**解决**: 安装 Visual Studio Build Tools
1. 下载: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. 安装时选择 "C++ 桌面开发"

---

## 八、环境变量参考

```bash
# Windows 批处理
set COQUI_TOS_AGREED=1
set HF_ENDPOINT=https://hf-mirror.com
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set HTTP_PROXY=http://your-proxy:port
set HTTPS_PROXY=http://your-proxy:port

# Linux/macOS
export COQUI_TOS_AGREED=1
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_SYMLINKS_WARNING=1
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
```

---

## 九、已验证的依赖版本

```
Python==3.10.11
torch==2.5.1+cu118
torchaudio==2.5.1+cu118
TTS==0.22.0
transformers==4.49.0
ctranslate2==4.4.0
faster-whisper==1.1.1
edge-tts==7.0.2
librosa==0.10.2
soundfile==0.13.1
numpy==1.26.4
pydub==0.25.1
```

---

## 版本信息

- 文档版本: 1.0
- 创建日期: 2025-11-28
- 验证环境: Windows 10, Python 3.10.11, PyTorch 2.5.1+cu118
- 仓库地址: https://github.com/githubstudycloud/gi005
