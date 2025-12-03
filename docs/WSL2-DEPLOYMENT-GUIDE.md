# Voice Clone TTS - WSL2 部署完整指南

> 本文档记录了在 Windows 11 + WSL2 + Ubuntu 22.04 环境下部署 Voice Clone TTS 系统的完整过程，包括遇到的问题及解决方案。

## 目录

1. [系统架构](#系统架构)
2. [环境要求](#环境要求)
3. [安装步骤](#安装步骤)
4. [遇到的问题与解决方案](#遇到的问题与解决方案)
5. [启动服务](#启动服务)
6. [测试与使用](#测试与使用)
7. [一键启动脚本](#一键启动脚本)

---

## 系统架构

```
                         ┌─────────────────────────────────────┐
                         │           Windows 11 Host            │
                         │                                      │
                         │   ┌─────────────────────────────┐   │
                         │   │     WSL2 (Ubuntu 22.04)     │   │
                         │   │                             │   │
    HTTP Request         │   │   ┌─────────────────────┐   │   │
         │               │   │   │      Gateway        │   │   │
         ▼               │   │   │      :8080          │   │   │
    ┌─────────┐          │   │   └──────────┬──────────┘   │   │
    │ Client  │◄─────────┼───┼──────────────┼──────────────┼───┤
    └─────────┘          │   │   ┌──────────┼──────────┐   │   │
                         │   │   │          │          │   │   │
                         │   │   ▼          ▼          ▼   │   │
                         │   │ ┌────┐    ┌────┐    ┌────┐  │   │
                         │   │ │XTTS│    │Open│    │GPT-│  │   │
                         │   │ │:8001│   │Voice│   │SoVITS│ │   │
                         │   │ │    │    │:8002│   │:8003│  │   │
                         │   │ └────┘    └────┘    └──┬─┘  │   │
                         │   │                        │    │   │
                         │   │                        ▼    │   │
                         │   │                   ┌────────┐│   │
                         │   │                   │GPT-SoVITS│   │
                         │   │                   │API :9880││   │
                         │   │                   └────────┘│   │
                         │   └─────────────────────────────┘   │
                         └─────────────────────────────────────┘
```

### 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| Gateway | 8080 | 统一入口，负载均衡，服务发现 |
| XTTS Worker | 8001 | Coqui XTTS-v2 引擎，支持多语言 |
| OpenVoice Worker | 8002 | MyShell OpenVoice 引擎，音色转换 |
| GPT-SoVITS Worker | 8003 | GPT-SoVITS 引擎代理 |
| GPT-SoVITS API | 9880 | GPT-SoVITS 独立后端服务 |

---

## 环境要求

### 硬件要求
- **CPU**: 多核处理器（推荐 8 核以上）
- **内存**: 32GB+ （模型加载需要大量内存）
- **存储**: 50GB+ 可用空间
- **GPU**: NVIDIA GPU（可选，当前使用 CPU 模式）

### 软件要求
- Windows 10/11 (版本 2004+)
- WSL2
- Ubuntu 22.04 LTS

### 重要说明
> ⚠️ **RTX 50 系列 (Blackwell) 暂不支持**
>
> RTX 5070/5080/5090 等 Blackwell 架构显卡 (sm_120) 目前不被 PyTorch 2.5 支持。
> 需要等待 PyTorch 2.6+ 版本。本指南使用 **CPU 模式** 运行所有服务。

---

## 安装步骤

### 第一步：安装 WSL2 和 Ubuntu 22.04

```powershell
# 在 Windows PowerShell (管理员) 中执行
wsl --install -d Ubuntu-22.04

# 设置默认用户（首次启动时设置）
# 用户名: user
# 密码: 自行设置
```

### 第二步：配置 Ubuntu 基础环境

```bash
# 进入 WSL
wsl -d Ubuntu-22.04

# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装基础依赖
sudo apt-get install -y \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    libportaudio2

# 配置 pip 镜像（国内加速）
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
```

### 第三步：安装 Python 依赖

```bash
# 设置环境变量（HuggingFace 镜像）
export HF_ENDPOINT=https://hf-mirror.com

# 安装基础科学计算库
pip3 install numpy pandas scipy matplotlib tqdm pyyaml requests

# 安装音频处理库
pip3 install librosa soundfile pydub

# 安装 PyTorch (CPU 版本，适用于不支持的 GPU)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 或者安装 CUDA 版本 (适用于支持的 GPU，如 RTX 40 系列)
# pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装 Voice Clone TTS 依赖
cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts
pip3 install -r requirements.txt

# 安装 TTS (Coqui TTS for XTTS)
pip3 install TTS
```

### 第四步：安装 OpenVoice 和 MeloTTS

```bash
# 安装 MeloTTS (OpenVoice 的依赖)
# 方法 1: 从 GitHub 安装
pip3 install git+https://github.com/myshell-ai/MeloTTS.git

# 方法 2: 如果 GitHub 访问慢，手动下载安装
# 下载 https://github.com/myshell-ai/MeloTTS/archive/refs/heads/main.zip
# unzip MeloTTS-main.zip && cd MeloTTS-main && pip3 install -e .

# 安装 OpenVoice
pip3 install openvoice-cli

# 下载 NLTK 数据（MeloTTS 需要）
python3 -c "
import nltk
nltk.download('cmudict')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
"
```

### 第五步：安装 GPT-SoVITS

```bash
# 进入 GPT-SoVITS 目录
cd /mnt/d/data/PycharmProjects/PythonProject1/packages/GPT-SoVITS

# 安装依赖
pip3 install -r requirements.txt

# 修复 peft 版本兼容性问题（重要！）
pip3 install peft==0.10.0
```

### 第六步：下载预训练模型

#### 6.1 XTTS 模型
XTTS 模型会在首次启动时自动下载，或使用脚本：

```bash
# 设置 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com
export COQUI_TOS_AGREED=1

# 模型会下载到 ~/.local/share/tts/
python3 -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')"
```

#### 6.2 OpenVoice 模型
```bash
# 下载 OpenVoice 检查点
cd /mnt/d/data/PycharmProjects/PythonProject1/packages/models/openvoice

# 从 HuggingFace 下载 (使用镜像)
# checkpoints_v2/converter/checkpoint.pth (~57MB)
# checkpoints_v2/converter/config.json
# checkpoints_v2/base_speakers/ses/zh.pth
# checkpoints_v2/base_speakers/ses/en-newest.pth
```

#### 6.3 GPT-SoVITS 模型
```python
# 使用下载脚本 (D:\wsl\download_gpt_sovits_models.py)
# 下载以下文件到 packages/GPT-SoVITS/GPT_SoVITS/pretrained_models/

# gsv-v2final-pretrained/
#   - s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt (~155MB)
#   - s2G2333k.pth (~106MB)
#   - s2D2333k.pth (~93MB)

# chinese-hubert-base/
#   - config.json
#   - preprocessor_config.json
#   - pytorch_model.bin (~188MB)

# chinese-roberta-wwm-ext-large/
#   - config.json
#   - tokenizer.json
#   - pytorch_model.bin (~651MB)
```

---

## 遇到的问题与解决方案

### 问题 1: RTX 5070 CUDA 不支持

**错误信息**:
```
RuntimeError: CUDA error: no kernel image is available for execution on the device
CUDA kernel errors might be asynchronously reported at some other API call
```

**原因**: RTX 50 系列 (Blackwell, sm_120) 未被 PyTorch 2.5 支持

**解决方案**: 使用 CPU 模式运行所有服务
```bash
# 安装 CPU 版本 PyTorch
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 启动 Worker 时指定 --device cpu
python3 -m src.main worker --engine xtts --device cpu
```

### 问题 2: peft 库与 transformers 不兼容

**错误信息**:
```
ModuleNotFoundError: No module named 'transformers.modeling_layers'
```

**原因**: peft 新版本 API 变更，与当前 transformers 版本不兼容

**解决方案**: 降级 peft 版本
```bash
pip3 install peft==0.10.0
```

### 问题 3: GPT-SoVITS API 启动参数错误

**错误信息**:
```
unrecognized arguments: -s ... -g ... --device cpu
```

**原因**: api_v2.py 使用配置文件而非命令行参数

**解决方案**: 使用 `-c` 参数指定配置文件
```bash
# 正确的启动方式
python3 api_v2.py -c GPT_SoVITS/configs/tts_infer_cpu.yaml -a 0.0.0.0 -p 9880
```

### 问题 4: GPT-SoVITS 默认使用 CUDA

**错误信息**: 启动后尝试使用 CUDA 导致崩溃

**解决方案**: 创建 CPU 专用配置文件

创建文件 `GPT_SoVITS/configs/tts_infer_cpu.yaml`:
```yaml
custom:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt
  version: v2
  vits_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth
```

### 问题 5: Worker 引擎名称格式错误

**错误信息**:
```
invalid choice: 'gpt_sovits' (choose from 'xtts', 'openvoice', 'gpt-sovits')
```

**解决方案**: 使用连字符 `gpt-sovits` 而非下划线

### 问题 6: HuggingFace 下载缓慢

**解决方案**: 使用国内镜像
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### 问题 7: MeloTTS NLTK 数据缺失

**错误信息**:
```
Resource cmudict not found.
```

**解决方案**:
```bash
python3 -c "
import nltk
nltk.download('cmudict')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
"
```

---

## 启动服务

### 手动启动（分步骤）

打开 5 个终端窗口，分别执行：

**终端 1: Gateway**
```bash
wsl -d Ubuntu-22.04 -u user -e bash -c '
cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts
python3 -m src.main gateway --port 8080
'
```

**终端 2: XTTS Worker**
```bash
wsl -d Ubuntu-22.04 -u user -e bash -c '
export HF_ENDPOINT=https://hf-mirror.com
cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts
python3 -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --device cpu --auto-load
'
```

**终端 3: OpenVoice Worker**
```bash
wsl -d Ubuntu-22.04 -u user -e bash -c '
export HF_ENDPOINT=https://hf-mirror.com
cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts
python3 -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080 --device cpu --auto-load
'
```

**终端 4: GPT-SoVITS API**
```bash
wsl -d Ubuntu-22.04 -u user -e bash -c '
export HF_ENDPOINT=https://hf-mirror.com
export PYTHONPATH=/mnt/d/data/PycharmProjects/PythonProject1/packages/GPT-SoVITS
cd /mnt/d/data/PycharmProjects/PythonProject1/packages/GPT-SoVITS
python3 api_v2.py -c GPT_SoVITS/configs/tts_infer_cpu.yaml -a 0.0.0.0 -p 9880
'
```

**终端 5: GPT-SoVITS Worker**
```bash
wsl -d Ubuntu-22.04 -u user -e bash -c '
export HF_ENDPOINT=https://hf-mirror.com
export GPT_SOVITS_API_URL=http://127.0.0.1:9880
cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts
python3 -m src.main worker --engine gpt-sovits --port 8003 --gateway http://localhost:8080 --device cpu --auto-load
'
```

---

## 测试与使用

### 健康检查

```bash
# 检查 Gateway 健康状态
curl http://localhost:8080/health

# 查看所有注册的 Worker 节点
curl http://localhost:8080/api/nodes | python -m json.tool

# 检查 GPT-SoVITS API
curl http://localhost:9880/
```

### TTS 合成测试

#### 使用 XTTS 引擎
```bash
curl -X POST http://localhost:8080/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是一个语音合成测试。",
    "engine": "xtts",
    "language": "zh"
  }' \
  --output test_xtts.wav
```

#### 使用 OpenVoice 引擎
```bash
curl -X POST http://localhost:8080/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a voice synthesis test.",
    "engine": "openvoice",
    "language": "en"
  }' \
  --output test_openvoice.wav
```

#### 使用 GPT-SoVITS 引擎
```bash
curl -X POST http://localhost:8080/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是 GPT-SoVITS 语音合成测试。",
    "engine": "gpt-sovits",
    "language": "zh"
  }' \
  --output test_gpt_sovits.wav
```

### 直接调用 GPT-SoVITS API

```bash
# 列出可用模型
curl http://localhost:9880/tts

# 合成语音 (需要提供参考音频)
curl -X POST "http://localhost:9880/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "text_lang": "zh",
    "ref_audio_path": "/path/to/reference.wav",
    "prompt_text": "参考文本",
    "prompt_lang": "zh"
  }' \
  --output output.wav
```

---

## 一键启动脚本

### Windows 批处理脚本

创建 `start-voice-clone-tts.bat`:

```batch
@echo off
echo Starting Voice Clone TTS Services...

REM 启动 Gateway
start "Gateway" cmd /k wsl -d Ubuntu-22.04 -u user -e bash -c "cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts && python3 -m src.main gateway --port 8080"

REM 等待 Gateway 启动
timeout /t 5

REM 启动 XTTS Worker
start "XTTS Worker" cmd /k wsl -d Ubuntu-22.04 -u user -e bash -c "export HF_ENDPOINT=https://hf-mirror.com && cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts && python3 -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --device cpu --auto-load"

REM 启动 OpenVoice Worker
start "OpenVoice Worker" cmd /k wsl -d Ubuntu-22.04 -u user -e bash -c "export HF_ENDPOINT=https://hf-mirror.com && cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts && python3 -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080 --device cpu --auto-load"

REM 启动 GPT-SoVITS API
start "GPT-SoVITS API" cmd /k wsl -d Ubuntu-22.04 -u user -e bash -c "export HF_ENDPOINT=https://hf-mirror.com && export PYTHONPATH=/mnt/d/data/PycharmProjects/PythonProject1/packages/GPT-SoVITS && cd /mnt/d/data/PycharmProjects/PythonProject1/packages/GPT-SoVITS && python3 api_v2.py -c GPT_SoVITS/configs/tts_infer_cpu.yaml -a 0.0.0.0 -p 9880"

REM 等待 GPT-SoVITS API 启动
timeout /t 10

REM 启动 GPT-SoVITS Worker
start "GPT-SoVITS Worker" cmd /k wsl -d Ubuntu-22.04 -u user -e bash -c "export HF_ENDPOINT=https://hf-mirror.com && export GPT_SOVITS_API_URL=http://127.0.0.1:9880 && cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts && python3 -m src.main worker --engine gpt-sovits --port 8003 --gateway http://localhost:8080 --device cpu --auto-load"

echo All services started!
echo Gateway: http://localhost:8080
echo XTTS Worker: http://localhost:8001
echo OpenVoice Worker: http://localhost:8002
echo GPT-SoVITS API: http://localhost:9880
echo GPT-SoVITS Worker: http://localhost:8003
pause
```

### Linux Shell 脚本 (在 WSL 内使用)

创建 `start-all.sh`:

```bash
#!/bin/bash

# 设置环境变量
export HF_ENDPOINT=https://hf-mirror.com
export PROJECT_DIR=/mnt/d/data/PycharmProjects/PythonProject1
export GPT_SOVITS_API_URL=http://127.0.0.1:9880

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Voice Clone TTS Services...${NC}"

# 启动 Gateway
echo "Starting Gateway on :8080..."
cd $PROJECT_DIR/voice-clone-tts
nohup python3 -m src.main gateway --port 8080 > /tmp/gateway.log 2>&1 &
sleep 3

# 启动 XTTS Worker
echo "Starting XTTS Worker on :8001..."
nohup python3 -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --device cpu --auto-load > /tmp/xtts.log 2>&1 &
sleep 2

# 启动 OpenVoice Worker
echo "Starting OpenVoice Worker on :8002..."
nohup python3 -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080 --device cpu --auto-load > /tmp/openvoice.log 2>&1 &
sleep 2

# 启动 GPT-SoVITS API
echo "Starting GPT-SoVITS API on :9880..."
cd $PROJECT_DIR/packages/GPT-SoVITS
export PYTHONPATH=$PROJECT_DIR/packages/GPT-SoVITS
nohup python3 api_v2.py -c GPT_SoVITS/configs/tts_infer_cpu.yaml -a 0.0.0.0 -p 9880 > /tmp/gpt_sovits_api.log 2>&1 &
sleep 10

# 启动 GPT-SoVITS Worker
echo "Starting GPT-SoVITS Worker on :8003..."
cd $PROJECT_DIR/voice-clone-tts
nohup python3 -m src.main worker --engine gpt-sovits --port 8003 --gateway http://localhost:8080 --device cpu --auto-load > /tmp/gpt_sovits_worker.log 2>&1 &

echo -e "${GREEN}All services started!${NC}"
echo ""
echo "Services:"
echo "  Gateway:           http://localhost:8080"
echo "  XTTS Worker:       http://localhost:8001"
echo "  OpenVoice Worker:  http://localhost:8002"
echo "  GPT-SoVITS API:    http://localhost:9880"
echo "  GPT-SoVITS Worker: http://localhost:8003"
echo ""
echo "Logs:"
echo "  Gateway:           /tmp/gateway.log"
echo "  XTTS:              /tmp/xtts.log"
echo "  OpenVoice:         /tmp/openvoice.log"
echo "  GPT-SoVITS API:    /tmp/gpt_sovits_api.log"
echo "  GPT-SoVITS Worker: /tmp/gpt_sovits_worker.log"
```

---

## 代码微调记录

### 1. 创建 GPT-SoVITS CPU 配置文件

**文件**: `packages/GPT-SoVITS/GPT_SoVITS/configs/tts_infer_cpu.yaml`

```yaml
custom:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt
  version: v2
  vits_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth
v1:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
  version: v1
  vits_weights_path: GPT_SoVITS/pretrained_models/s2G488k.pth
v2:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt
  version: v2
  vits_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth
```

**关键修改**:
- `device: cpu` - 强制使用 CPU
- `is_half: false` - 禁用半精度（CPU 不支持）

---

## 依赖软件清单

### 系统级依赖 (apt)
```
build-essential
python3
python3-pip
python3-venv
git
curl
wget
ffmpeg
libsndfile1
portaudio19-dev
libportaudio2
```

### Python 依赖
```
# 核心
torch (CPU 版本)
torchvision
torchaudio
numpy
pandas
scipy

# 音频处理
librosa
soundfile
pydub

# TTS 引擎
TTS (Coqui TTS)
melo (MeloTTS)
openvoice-cli

# GPT-SoVITS 特定
peft==0.10.0  # 必须指定版本
transformers
```

---

## 常见问题 FAQ

**Q: 服务启动后多久可以使用？**
A: Gateway 几秒内就绪，Worker 需要加载模型，XTTS 约 1-2 分钟，OpenVoice 约 30 秒，GPT-SoVITS 约 1 分钟。

**Q: 如何查看服务是否就绪？**
A: 访问 `http://localhost:8080/api/nodes`，查看各 Worker 的 `status` 是否为 `ready`。

**Q: CPU 模式性能如何？**
A: 比 GPU 慢 5-10 倍，但对于普通使用足够。建议使用多核 CPU。

**Q: 何时可以使用 GPU？**
A: 等待 PyTorch 2.6+ 支持 sm_120 (Blackwell) 架构，届时修改配置中的 `device: cuda` 即可。

---

## 版本信息

- **文档版本**: 1.0
- **更新日期**: 2024-12
- **测试环境**:
  - Windows 11 23H2
  - WSL2 (Ubuntu 22.04 LTS)
  - Python 3.10
  - PyTorch 2.5.1+cpu
  - NVIDIA RTX 5070 (CPU 模式)
