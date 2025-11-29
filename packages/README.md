# Voice Clone TTS - 组件包目录

本目录包含项目运行所需的所有组件包，按类型分类存放。

## 目录结构

```
packages/
├── models/           # 模型文件 (大文件，需手动下载或解压)
│   ├── xtts_v2/     # XTTS-v2 模型 (~2GB)
│   ├── openvoice/   # OpenVoice 模型 (~130MB)
│   └── whisper/     # Whisper 模型 (~1.5GB)
├── tools/           # 工具软件 (Windows 可执行文件)
│   ├── ffmpeg/      # FFmpeg 音视频处理
│   └── python/      # Python 安装程序
└── dependencies/    # Python 依赖包离线安装
    └── wheels/      # pip wheel 文件
```

## 使用说明

### 1. 模型文件

模型文件体积较大，以分卷压缩包形式提供。请按以下步骤还原：

**Windows (PowerShell):**
```powershell
# 进入模型目录
cd packages/models/xtts_v2

# 合并分卷并解压
cat xtts_v2.tar.part_* | tar -xvf -
```

**Linux/macOS:**
```bash
cd packages/models/xtts_v2
cat xtts_v2.tar.part_* | tar -xvf -
```

### 2. 工具软件

- **FFmpeg**: 音视频处理必需
- **Python 3.10**: 推荐版本

### 3. 离线依赖

如果无法访问 PyPI，可使用离线 wheel 包安装：

```bash
pip install --no-index --find-links=packages/dependencies/wheels -r requirements.txt
```

## 下载链接

如果分卷包不完整，可从以下地址下载完整模型：

| 模型 | 大小 | 下载地址 |
|------|------|----------|
| XTTS-v2 | ~2GB | [Hugging Face](https://huggingface.co/coqui/XTTS-v2) |
| OpenVoice | ~130MB | [Hugging Face](https://huggingface.co/myshell-ai/OpenVoice) |
| Whisper | ~1.5GB | [Hugging Face](https://huggingface.co/openai/whisper-large-v3) |

## 镜像加速

中国大陆用户可使用镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```
