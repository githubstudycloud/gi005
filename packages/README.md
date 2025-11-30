# Voice Clone TTS - 组件包目录

本目录包含项目运行所需的所有组件包，按类型分类存放。

## 目录结构

```
packages/
├── models/                      # 模型文件
│   ├── xtts_v2/                # XTTS-v2 模型
│   │   ├── xtts_v2_full.pkg.part_*  # 分卷包 (21个, 约2GB)
│   │   ├── extracted/          # 解压后的模型文件 (已在 .gitignore)
│   │   └── README.md
│   ├── openvoice/              # OpenVoice 模型
│   │   ├── checkpoints_v2.pkg.part_*  # 分卷包 (2个, 约126MB)
│   │   ├── extracted/          # 解压后的模型文件
│   │   │   ├── converter/
│   │   │   └── base_speakers/
│   │   └── README.md
│   └── whisper/                # Whisper 模型
│       ├── whisper_models.pkg.part_*  # 分卷包 (16个, 约1.5GB)
│       ├── extracted/          # 解压后的模型文件
│       └── README.md
├── tools/                      # 工具软件
│   ├── ffmpeg.pkg.part_*       # FFmpeg 分卷包 (6个, 约551MB)
│   ├── python.pkg.part_*       # Python 安装程序 (~28MB)
│   ├── extracted/              # 解压后的可执行文件
│   │   ├── ffmpeg.exe
│   │   ├── ffplay.exe
│   │   └── ffprobe.exe
│   └── README.md
├── dependencies/               # Python 依赖包
│   └── README.md
├── repos/                      # 开源项目仓库 (已在 .gitignore)
│   └── README.md               # 克隆说明
└── README.md                   # 本文件
```

## 快速开始

### 1. 还原模型文件

每个模型目录都包含分卷包 (`*.pkg.part_*`)，需要合并后解压：

```bash
# 还原 XTTS-v2 模型
cd packages/models/xtts_v2
cat xtts_v2_full.pkg.part_* > xtts_v2.tar
tar -xvf xtts_v2.tar -C extracted/
rm xtts_v2.tar

# 还原 OpenVoice 模型
cd packages/models/openvoice
cat checkpoints_v2.pkg.part_* > checkpoints.tar
tar -xvf checkpoints.tar -C extracted/
rm checkpoints.tar

# 还原 Whisper 模型
cd packages/models/whisper
cat whisper_models.pkg.part_* > whisper.tar
tar -xvf whisper.tar -C extracted/
rm whisper.tar
```

### 2. 还原工具软件

```bash
cd packages/tools
cat ffmpeg.pkg.part_* > ffmpeg.tar
tar -xvf ffmpeg.tar -C extracted/
rm ffmpeg.tar
```

### 3. 开源项目

如果需要 GPT-SoVITS 引擎，需要克隆对应仓库：

```bash
cd packages/repos
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
```

## 模型来源

| 模型 | 大小 | 来源 |
|------|------|------|
| XTTS-v2 | ~2GB | [Hugging Face](https://huggingface.co/coqui/XTTS-v2) |
| OpenVoice | ~126MB | [Hugging Face](https://huggingface.co/myshell-ai/OpenVoice) |
| Whisper | ~1.5GB | [Hugging Face](https://huggingface.co/openai/whisper-large-v3) |

## 代码路径配置

应用代码应从 `packages/` 目录读取模型和工具：

```python
# 模型路径
XTTS_MODEL_PATH = "packages/models/xtts_v2/extracted"
OPENVOICE_MODEL_PATH = "packages/models/openvoice/extracted"
WHISPER_MODEL_PATH = "packages/models/whisper/extracted"

# 工具路径
FFMPEG_PATH = "packages/tools/extracted/ffmpeg.exe"
```

## 镜像加速

中国大陆用户可使用 Hugging Face 镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

## 注意事项

1. `extracted/` 目录中的文件已在 `.gitignore` 中，不会被提交到仓库
2. 分卷包 (`*.pkg.part_*`) 会被提交，用于完整性恢复
3. 首次使用需要手动执行还原命令
4. 如果分卷包损坏，可从源地址重新下载
