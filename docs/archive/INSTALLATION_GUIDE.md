# 音色克隆 TTS 完整安装指南

本文档提供从零开始配置和使用音色克隆 TTS 系统的完整指南。

---

## 目录

1. [系统要求](#系统要求)
2. [基础环境配置](#基础环境配置)
3. [引擎安装](#引擎安装)
   - [XTTS-v2（推荐入门）](#xtts-v2推荐入门)
   - [OpenVoice](#openvoice)
   - [GPT-SoVITS（中文最佳）](#gpt-sovits中文最佳)
4. [使用方法](#使用方法)
5. [API 服务](#api-服务)
6. [常见问题](#常见问题)
7. [验证测试](#验证测试)

---

## 系统要求

### 硬件要求

| 引擎 | 最低显存 | 推荐显存 | CPU 模式 |
|------|---------|---------|----------|
| XTTS-v2 | 4GB | 6GB+ | 支持（较慢） |
| OpenVoice | 2GB | 4GB+ | 支持 |
| GPT-SoVITS | 4GB | 8GB+ | 支持（很慢） |

### 软件要求

- **Python**: 3.10（推荐）或 3.9
  - 注意：Python 3.11+ 与部分依赖不兼容
  - 注意：Python 3.14 与 PyTorch 不兼容
- **操作系统**: Windows 10/11 或 Linux
- **CUDA**: 11.7+ 或 11.8（GPU 加速）
- **Visual Studio Build Tools**（Windows，用于编译部分依赖）

---

## 基础环境配置

### 1. 安装 Python 3.10

**Windows:**
```powershell
# 从官网下载 Python 3.10
# https://www.python.org/downloads/release/python-31011/

# 安装时勾选 "Add Python to PATH"
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# 或使用 pyenv
pyenv install 3.10.11
pyenv local 3.10.11
```

### 2. 创建虚拟环境

```bash
# 创建项目目录
mkdir voice-clone-tts && cd voice-clone-tts

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux:
source venv/bin/activate
```

### 3. 安装 PyTorch

```bash
# CUDA 11.8 版本（推荐）
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# CPU 版本
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 4. 安装基础依赖

```bash
pip install numpy librosa soundfile fastapi uvicorn python-multipart requests
```

### 5. 安装 FFmpeg

**Windows:**
```bash
# 从 GitHub 下载
# https://github.com/BtbN/FFmpeg-Builds/releases
# 下载 ffmpeg-master-latest-win64-gpl.zip
# 解压并将 bin 目录添加到 PATH
```

**Linux:**
```bash
sudo apt install ffmpeg
```

---

## 引擎安装

### XTTS-v2（推荐入门）

XTTS-v2 是最容易安装和使用的引擎，适合快速开始。

#### 安装步骤

```bash
# 1. 安装 TTS 库（需要 Visual C++ Build Tools）
pip install TTS

# 如果安装失败，先安装 Visual C++ Build Tools：
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
# 选择 "使用 C++ 的桌面开发"

# 2. 安装 transformers（指定版本避免兼容问题）
pip install "transformers<4.50"
```

#### 离线模型配置

```bash
# XTTS-v2 模型约 2GB，首次运行会自动下载
# 如需离线使用，可手动下载：

# 使用 HuggingFace 镜像（中国地区）
export HF_ENDPOINT=https://hf-mirror.com

# 下载模型
python -c "
from TTS.api import TTS
import os
os.environ['COQUI_TOS_AGREED'] = '1'
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2')
"
```

#### 快速测试

```python
import os
os.environ['COQUI_TOS_AGREED'] = '1'

from TTS.api import TTS

# 加载模型
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

# 使用参考音频克隆
tts.tts_to_file(
    text="你好世界，这是音色克隆测试。",
    file_path="output.wav",
    speaker_wav="reference.wav",  # 你的参考音频
    language="zh-cn"
)
```

---

### OpenVoice

OpenVoice 专注于音色转换，可将任意语音转换为目标音色。

#### 安装步骤

```bash
# 1. 克隆 OpenVoice 仓库
git clone https://github.com/myshell-ai/OpenVoice.git
cd OpenVoice

# 2. 安装依赖
pip install -e .
pip install edge-tts whisper-timestamped

# 3. 下载模型
# 使用 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com

python -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from huggingface_hub import snapshot_download

# 下载 converter 模型
snapshot_download(
    repo_id='myshell-ai/OpenVoiceV2',
    local_dir='checkpoints_v2',
    allow_patterns=['converter/*', 'base_speakers/*']
)
"
```

#### 模型文件结构

```
checkpoints_v2/
├── converter/
│   ├── config.json
│   └── checkpoint.pth
└── base_speakers/
    └── ses/
        ├── en-us.pth
        ├── zh.pth
        └── ...
```

#### 快速测试

```python
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
import edge_tts
import asyncio

# 1. 加载模型
converter = ToneColorConverter('checkpoints_v2/converter/config.json', device='cpu')
converter.load_ckpt('checkpoints_v2/converter/checkpoint.pth')

# 2. 提取目标音色
target_se, _ = se_extractor.get_se(
    'reference.wav',  # 你的参考音频
    converter,
    vad=True  # 使用 VAD，不需要 whisper
)

# 3. 生成基础音频（使用 edge-tts）
async def generate_base():
    communicate = edge_tts.Communicate('Hello world!', 'en-US-AriaNeural')
    await communicate.save('base_audio.wav')

asyncio.run(generate_base())

# 4. 加载预训练说话人嵌入
src_se = torch.load('checkpoints_v2/base_speakers/ses/en-us.pth', map_location='cpu')

# 5. 转换音色
converter.convert(
    audio_src_path='base_audio.wav',
    src_se=src_se,
    tgt_se=target_se,
    output_path='output.wav'
)
```

---

### GPT-SoVITS（中文最佳）

GPT-SoVITS 是中文语音克隆效果最好的开源方案。

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS

# 2. 创建独立的 conda 环境（推荐）
conda create -n gpt-sovits python=3.10
conda activate gpt-sovits

# 3. 安装 PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 4. 安装依赖
pip install -r requirements.txt
```

#### 下载预训练模型

GPT-SoVITS 需要多个预训练模型，总计约 5-10GB：

```bash
# 模型下载地址
# https://huggingface.co/lj1995/GPT-SoVITS

# 模型文件结构
GPT-SoVITS/
├── GPT_weights_v2/
│   └── xxx.ckpt
├── SoVITS_weights_v2/
│   └── xxx.pth
└── pretrained_models/
    ├── chinese-roberta-wwm-ext-large/
    ├── chinese-hubert-base/
    └── ...
```

#### 启动 API 服务

```bash
cd GPT-SoVITS

# 启动 API 服务
python api_v2.py -a 127.0.0.1 -p 9880

# 或启动 WebUI
python webui.py
```

#### 使用 API

```python
import requests

# 合成语音
response = requests.post(
    "http://127.0.0.1:9880/tts",
    json={
        "text": "你好世界，这是测试。",
        "text_lang": "zh",
        "ref_audio_path": "reference.wav",
        "prompt_text": "参考音频对应的文本",
        "prompt_lang": "zh"
    }
)

# 保存音频
with open("output.wav", "wb") as f:
    f.write(response.content)
```

---

## 使用方法

### 使用 production 代码

本项目提供统一封装的 production 代码：

```bash
cd voice-clone-tts/production

# 提取音色
python main.py extract --engine xtts --audio reference.wav --voice-id my_voice

# 合成语音
python main.py synthesize --engine xtts --voice-id my_voice --text "你好世界" --output output.wav

# 快速克隆（一步完成）
python main.py quick --engine xtts --audio reference.wav --text "你好世界" --output output.wav

# 启动 HTTP 服务
python main.py serve --engine xtts --port 8000
```

### Python API

```python
# XTTS 示例
from xtts import XTTSCloner

cloner = XTTSCloner()
cloner.load_model()

# 提取音色
voice = cloner.extract_voice("reference.wav", voice_id="my_voice")

# 合成语音
cloner.synthesize("你好世界", voice, "output.wav", language="zh-cn")
```

```python
# OpenVoice 示例
from openvoice import OpenVoiceCloner

cloner = OpenVoiceCloner(model_path="checkpoints_v2/converter")
cloner.load_model()

# 提取音色
voice = cloner.extract_voice("reference.wav", voice_id="my_voice")

# 合成语音
cloner.synthesize("Hello world", voice, "output.wav", language="en")
```

---

## API 服务

### 启动服务

```bash
python main.py serve --engine xtts --host 0.0.0.0 --port 8000
```

### API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/extract_voice` | POST | 提取音色 |
| `/synthesize` | POST | 合成语音 |
| `/synthesize_direct` | POST | 直接克隆 |
| `/voices` | GET | 列出音色 |
| `/voices/{id}` | GET/DELETE | 获取/删除音色 |
| `/health` | GET | 健康检查 |

### API 示例

```bash
# 提取音色
curl -X POST http://localhost:8000/extract_voice \
  -F "audio=@reference.wav" \
  -F "voice_name=我的声音"

# 合成语音
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "voice_id": "xxx", "language": "zh"}' \
  --output output.wav
```

---

## 常见问题

### Q1: ModuleNotFoundError: No module named 'TTS'

**解决方案：**
```bash
# 需要 Visual C++ Build Tools
# 下载安装：https://visualstudio.microsoft.com/visual-cpp-build-tools/
pip install TTS
```

### Q2: CUDA 内存不足

**解决方案：**
```bash
# 使用 CPU 模式
python main.py serve --engine xtts --device cpu
```

### Q3: transformers 版本不兼容

**解决方案：**
```bash
pip install "transformers<4.50"
```

### Q4: HuggingFace 下载慢

**解决方案：**
```bash
# 使用镜像
export HF_ENDPOINT=https://hf-mirror.com

# 或使用代理
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
```

### Q5: cublas64_12.dll 找不到

**解决方案：**
这是 CUDA 12 的依赖。如果你使用 CUDA 11.8：
```bash
# 降级 ctranslate2
pip install ctranslate2==4.4.0
```

### Q6: OpenVoice 提示 "audio is too short"

**解决方案：**
- 参考音频建议 6-30 秒
- 使用 `vad=True` 时会自动切分
- 如果音频本身太短，尝试使用预训练的 speaker embedding

---

## 验证测试

### 测试 XTTS

```python
# test_xtts.py
import os
os.environ['COQUI_TOS_AGREED'] = '1'

from TTS.api import TTS

print("Loading XTTS model...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
print("Model loaded!")

# 测试合成
tts.tts_to_file(
    text="This is a test.",
    file_path="test_output.wav",
    speaker_wav="test_audio/sample_en.wav",
    language="en"
)

import os
if os.path.exists("test_output.wav"):
    size = os.path.getsize("test_output.wav")
    print(f"Success! Output size: {size} bytes")
else:
    print("Failed!")
```

### 测试 OpenVoice

```python
# test_openvoice.py
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter

print("Loading OpenVoice model...")
converter = ToneColorConverter('checkpoints_v2/converter/config.json', device='cpu')
converter.load_ckpt('checkpoints_v2/converter/checkpoint.pth')
print("Model loaded!")

# 提取音色
print("Extracting voice...")
target_se, _ = se_extractor.get_se('test_audio/sample_en.wav', converter, vad=True)
print(f"Voice embedding shape: {target_se.shape}")

# 转换音色
print("Converting voice...")
src_se = torch.load('checkpoints_v2/base_speakers/ses/en-us.pth', map_location='cpu')
converter.convert(
    audio_src_path='test_audio/base_audio.wav',
    src_se=src_se,
    tgt_se=target_se,
    output_path='test_output_openvoice.wav'
)

import os
if os.path.exists("test_output_openvoice.wav"):
    size = os.path.getsize("test_output_openvoice.wav")
    print(f"Success! Output size: {size} bytes")
else:
    print("Failed!")
```

---

## 引擎对比

| 特性 | XTTS-v2 | OpenVoice | GPT-SoVITS |
|------|---------|-----------|------------|
| 安装难度 | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 复杂 |
| 中文质量 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 英文质量 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 克隆相似度 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 显存需求 | 4GB | 2GB | 4-8GB |
| 推理速度 | 中等 | 快 | 慢 |
| 离线部署 | 支持 | 支持 | 支持 |

**推荐选择：**
- 快速开始 → XTTS-v2
- 中文首选 → GPT-SoVITS
- 音色转换 → OpenVoice

---

## 版本信息

- 文档版本: 1.0
- 更新日期: 2025-11-28
- 测试环境: Windows 10, Python 3.10, PyTorch 2.5.1, CUDA 11.8
