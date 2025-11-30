# Voice Clone TTS 安装指南

本文档提供详细的安装步骤，即使是初学者也能轻松完成部署。

## 目录

1. [系统要求](#系统要求)
2. [快速安装](#快速安装)
3. [详细安装步骤](#详细安装步骤)
4. [模型文件安装](#模型文件安装)
5. [验证安装](#验证安装)
6. [常见问题](#常见问题)

---

## 系统要求

### 硬件要求

| 配置级别 | CPU | 内存 | 显卡 | 存储 |
|---------|-----|------|------|------|
| 最低配置 | 4核 | 8GB | 无 (CPU模式) | 10GB |
| 推荐配置 | 8核 | 16GB | NVIDIA 6GB+ | 20GB |
| 高性能 | 16核 | 32GB | NVIDIA 12GB+ | 50GB |

### 软件要求

- **操作系统**: Windows 10/11, Ubuntu 20.04+, macOS 12+
- **Python**: 3.10.x (推荐 3.10.11)
- **FFmpeg**: 5.0+ (音视频处理)
- **CUDA**: 11.8+ (GPU 加速，可选)

---

## 快速安装

适合有经验的用户，5分钟完成安装：

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/voice-clone-tts.git
cd voice-clone-tts

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 还原模型文件
cd packages/models/xtts_v2
cat xtts_v2.tar.part_* | tar -xvf -

# 5. 验证安装
python -c "from TTS.api import TTS; print('OK')"
```

---

## 详细安装步骤

### 步骤 1: 安装 Python

#### Windows

1. 下载 Python 安装程序
   - 官网: https://www.python.org/downloads/
   - 或使用本地包: `packages/tools/python/python-3.10.11-amd64.exe`

2. 运行安装程序，**务必勾选以下选项**:
   - [x] Add Python 3.10 to PATH
   - [x] Install pip

3. 验证安装:
   ```cmd
   python --version
   # 应显示: Python 3.10.x

   pip --version
   # 应显示: pip 23.x.x
   ```

#### Linux (Ubuntu/Debian)

```bash
# 安装 Python 3.10
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# 验证
python3.10 --version
```

#### macOS

```bash
# 使用 Homebrew
brew install python@3.10

# 验证
python3.10 --version
```

### 步骤 2: 安装 FFmpeg

#### Windows

**方式1: 使用项目自带的 FFmpeg**
```cmd
# FFmpeg 已在项目根目录
# 无需额外安装，直接使用即可
```

**方式2: 手动安装**
1. 下载: https://github.com/BtbN/FFmpeg-Builds/releases
2. 解压到 `C:\ffmpeg`
3. 添加 `C:\ffmpeg\bin` 到系统 PATH

#### Linux

```bash
sudo apt install ffmpeg
```

#### macOS

```bash
brew install ffmpeg
```

**验证:**
```bash
ffmpeg -version
```

### 步骤 3: 安装 CUDA (可选，GPU加速)

如果有 NVIDIA 显卡，安装 CUDA 可显著提升性能。

1. 检查显卡支持:
   ```cmd
   nvidia-smi
   ```

2. 下载 CUDA Toolkit 11.8:
   - https://developer.nvidia.com/cuda-11-8-0-download-archive

3. 安装 cuDNN:
   - https://developer.nvidia.com/cudnn

### 步骤 4: 创建虚拟环境

```bash
# 进入项目目录
cd voice-clone-tts

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate

# 确认激活成功（命令行前面会显示 (venv)）
```

### 步骤 5: 安装 Python 依赖

#### 在线安装 (推荐)

```bash
# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# GPU 版本 (CUDA 11.8)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 离线安装

```bash
# 使用本地 wheel 包
pip install --no-index --find-links=packages/dependencies/wheels -r requirements.txt
```

#### 镜像加速 (中国大陆)

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 模型文件安装

模型文件体积较大，以分卷压缩包形式提供。

### XTTS-v2 模型 (~2GB)

```bash
# 进入模型目录
cd packages/models/xtts_v2

# 合并并解压分卷
# Linux/macOS/Git Bash:
cat xtts_v2.tar.part_* | tar -xvf -

# Windows PowerShell:
Get-Content xtts_v2.tar.part_* -Raw | tar -xvf -

# 或使用 7-Zip:
# 选中所有 .part_* 文件 → 右键 → 7-Zip → 解压到当前文件夹
```

### OpenVoice 模型 (~130MB)

```bash
cd packages/models/openvoice
cat checkpoints_v2.tar.part_* | tar -xvf -
```

### Whisper 模型 (~1.5GB)

```bash
cd packages/models/whisper
cat whisper_models.tar.part_* | tar -xvf -
```

### 验证模型文件

```bash
# 检查 XTTS 模型
ls -la packages/models/xtts_v2/
# 应包含: config.json, model.pth, vocab.json

# 检查 OpenVoice 模型
ls -la packages/models/openvoice/checkpoints_v2/
# 应包含: converter/, base_speakers/
```

---

## 验证安装

### 基础验证

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 测试 Python 导入
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
"

# 测试 TTS 导入
python -c "
from TTS.api import TTS
print('TTS 导入成功')
"
```

### 完整测试

```bash
# 进入生产目录
cd voice-clone-tts/production

# 快速合成测试
python main.py quick \
    --engine xtts \
    --audio ../test_audio/sample.wav \
    --text "你好，这是语音克隆测试" \
    --output test_output.wav \
    --language zh

# 检查输出
ls -la test_output.wav
```

### HTTP 服务测试

```bash
# 启动服务器
python main.py serve --engine xtts --port 8000 &

# 等待启动
sleep 10

# 测试健康检查
curl http://localhost:8000/health

# 停止服务器
pkill -f "main.py serve"
```

---

## 常见问题

### Q1: pip 安装超时

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 120
```

### Q2: CUDA 不可用

```bash
# 检查 CUDA 版本
nvcc --version
nvidia-smi

# 确保安装了正确版本的 PyTorch
pip uninstall torch torchaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Q3: 模型加载失败

```bash
# 检查模型路径
python -c "
from pathlib import Path
model_path = Path('tts_model/xtts_v2')
print(f'模型目录: {model_path.absolute()}')
print(f'是否存在: {model_path.exists()}')
if model_path.exists():
    for f in model_path.iterdir():
        print(f'  - {f.name}')
"
```

### Q4: FFmpeg 找不到

```bash
# Windows: 将 ffmpeg.exe 复制到项目根目录
# 或添加到 PATH:
# 系统属性 → 高级 → 环境变量 → Path → 添加 ffmpeg 目录

# Linux:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg
```

### Q5: 内存不足

```bash
# 使用 CPU 模式 (内存占用更低)
python main.py serve --engine xtts --device cpu --port 8000

# 或减少并发数
python main.py serve --engine xtts --max-workers 1 --port 8000
```

---

## 下一步

安装完成后，请阅读:
- [使用指南](USAGE.md) - 学习如何使用
- [架构文档](ARCHITECTURE.md) - 了解系统设计
- [集成指南](INTEGRATION.md) - 集成到你的项目

---

## 获取帮助

- GitHub Issues: https://github.com/your-repo/voice-clone-tts/issues
- 文档: https://github.com/your-repo/voice-clone-tts/wiki
