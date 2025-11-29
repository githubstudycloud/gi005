# Python 依赖包

本目录包含 Python 依赖包的离线安装文件。

## 离线安装

当无法访问 PyPI 时，可使用本地 wheel 包安装：

```bash
pip install --no-index --find-links=./wheels -r requirements.txt
```

## 生成 wheel 包

```bash
# 下载依赖到 wheels 目录
pip download -d ./wheels -r requirements.txt

# 下载 GPU 版本 (CUDA 11.8)
pip download -d ./wheels torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 主要依赖

### 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| torch | 2.0+ | 深度学习框架 |
| torchaudio | 2.0+ | 音频处理 |
| TTS | 0.22+ | Coqui TTS |
| fastapi | 0.100+ | HTTP API |
| uvicorn | 0.22+ | ASGI 服务器 |

### XTTS 依赖

```
TTS>=0.22.0
torch>=2.0.0
torchaudio>=2.0.0
transformers>=4.30.0
```

### OpenVoice 依赖

```
melo
openvoice
librosa
soundfile
```

## 环境配置

### Conda (推荐)

```bash
conda env create -f environment.yml
conda activate voice-clone
```

### Pip

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

## 镜像加速

```bash
# 清华镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>

# 阿里云镜像
pip install -i https://mirrors.aliyun.com/pypi/simple <package>
```
