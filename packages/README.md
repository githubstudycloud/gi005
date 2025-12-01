# Voice Clone TTS - 组件包目录

本目录包含项目运行所需的所有组件包，按类型分类存放。**支持完全离线部署**。

## 离线包清单

| 组件 | 分卷数 | 大小 | 说明 |
|------|--------|------|------|
| XTTS-v2 模型 | 21 | ~2 GB | 多语言语音合成 |
| OpenVoice 模型 | 2 | ~126 MB | 音色克隆 |
| Whisper 模型 | 16 | ~1.5 GB | 语音识别 |
| **GPT-SoVITS 模型** | **100** | **~4.9 GB** | 中文语音合成 (新增) |
| FFmpeg | 6 | ~551 MB | 音频处理工具 |
| Python 安装包 | 1 | ~28 MB | Python 3.10 |
| OpenVoice 源码 | 2 | ~3.5 MB | 源代码 |
| GPT-SoVITS 源码 | 2 | ~2.7 MB | 源代码 |
| **总计** | **150** | **~9.2 GB** | |

## 目录结构

```
packages/
├── models/                      # 模型文件
│   ├── xtts_v2/                # XTTS-v2 模型
│   │   ├── xtts_v2_full.pkg.part_*  # 分卷包 (21个, 约2GB)
│   │   └── extracted/          # 解压后的模型文件
│   ├── openvoice/              # OpenVoice 模型
│   │   ├── checkpoints_v2.pkg.part_*  # 分卷包 (2个, 约126MB)
│   │   └── extracted/
│   ├── whisper/                # Whisper 模型
│   │   ├── whisper_models.pkg.part_*  # 分卷包 (16个, 约1.5GB)
│   │   └── extracted/
│   └── gpt_sovits/             # GPT-SoVITS 预训练模型 (新增)
│       ├── pretrained_models.pkg.part_*  # 分卷包 (88个, 约4.35GB)
│       ├── g2pw_model.pkg.part_*  # 分卷包 (12个, 约562MB)
│       └── README.md
├── tools/                      # 工具软件
│   ├── ffmpeg.pkg.part_*       # FFmpeg 分卷包 (6个, 约551MB)
│   ├── python.pkg.part_*       # Python 安装程序 (~28MB)
│   └── extracted/
├── repos/                      # 外部仓库源码
│   ├── openvoice_src.pkg.part_*   # OpenVoice 源码 (2个)
│   ├── gpt_sovits_src.pkg.part_*  # GPT-SoVITS 源码 (2个)
│   └── README.md
└── README.md                   # 本文件
```

## 完整离线部署指南

### Windows 环境

```powershell
# 1. 还原 XTTS-v2 模型
cd packages\models\xtts_v2
Get-Content xtts_v2_full.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content xtts_v2.tar -Encoding Byte
tar -xvf xtts_v2.tar -C extracted\

# 2. 还原 OpenVoice 模型
cd ..\openvoice
Get-Content checkpoints_v2.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content checkpoints.tar -Encoding Byte
tar -xvf checkpoints.tar -C extracted\

# 3. 还原 Whisper 模型
cd ..\whisper
Get-Content whisper_models.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content whisper.tar -Encoding Byte
tar -xvf whisper.tar -C extracted\

# 4. 还原 GPT-SoVITS 预训练模型
cd ..\gpt_sovits
Get-Content pretrained_models.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content pretrained_models.zip -Encoding Byte
Get-Content g2pw_model.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content g2pw_model.zip -Encoding Byte
# 解压到 repos/GPT-SoVITS 目录
Expand-Archive -Path pretrained_models.zip -DestinationPath ..\..\repos\GPT-SoVITS\GPT_SoVITS\ -Force
Expand-Archive -Path g2pw_model.zip -DestinationPath ..\..\repos\GPT-SoVITS\GPT_SoVITS\text\ -Force

# 5. 还原工具
cd ..\..\tools
Get-Content ffmpeg.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content ffmpeg.tar -Encoding Byte
tar -xvf ffmpeg.tar -C extracted\

# 6. 还原外部仓库源码
cd ..\repos
Get-Content openvoice_src.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content openvoice_src.tar -Encoding Byte
tar -xvf openvoice_src.tar
Get-Content gpt_sovits_src.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content gpt_sovits_src.tar -Encoding Byte
tar -xvf gpt_sovits_src.tar
```

### Linux/macOS 环境

```bash
# 1. 还原 XTTS-v2 模型
cd packages/models/xtts_v2
cat xtts_v2_full.pkg.part_* > xtts_v2.tar && tar -xvf xtts_v2.tar -C extracted/

# 2. 还原 OpenVoice 模型
cd ../openvoice
cat checkpoints_v2.pkg.part_* > checkpoints.tar && tar -xvf checkpoints.tar -C extracted/

# 3. 还原 Whisper 模型
cd ../whisper
cat whisper_models.pkg.part_* > whisper.tar && tar -xvf whisper.tar -C extracted/

# 4. 还原 GPT-SoVITS 预训练模型
cd ../gpt_sovits
cat pretrained_models.pkg.part_* > pretrained_models.zip
cat g2pw_model.pkg.part_* > g2pw_model.zip
unzip pretrained_models.zip -d ../../repos/GPT-SoVITS/GPT_SoVITS/
unzip g2pw_model.zip -d ../../repos/GPT-SoVITS/GPT_SoVITS/text/

# 5. 还原工具
cd ../../tools
cat ffmpeg.pkg.part_* > ffmpeg.tar && tar -xvf ffmpeg.tar -C extracted/

# 6. 还原外部仓库源码
cd ../repos
cat openvoice_src.pkg.part_* > openvoice_src.tar && tar -xvf openvoice_src.tar
cat gpt_sovits_src.pkg.part_* > gpt_sovits_src.tar && tar -xvf gpt_sovits_src.tar
```

## 引擎离线状态

| 引擎 | 离线就绪 | 所需组件 |
|------|---------|---------|
| **XTTS-v2** | ✅ | `models/xtts_v2/` |
| **OpenVoice** | ✅ | `models/openvoice/` + `repos/OpenVoice/` |
| **GPT-SoVITS** | ✅ | `models/gpt_sovits/` + `repos/GPT-SoVITS/` |

## 模型来源

| 模型 | 大小 | 来源 |
|------|------|------|
| XTTS-v2 | ~2GB | [Hugging Face](https://huggingface.co/coqui/XTTS-v2) |
| OpenVoice | ~126MB | [Hugging Face](https://huggingface.co/myshell-ai/OpenVoice) |
| Whisper | ~1.5GB | [Hugging Face](https://huggingface.co/openai/whisper-large-v3) |
| GPT-SoVITS | ~4.9GB | [Hugging Face](https://huggingface.co/lj1995/GPT-SoVITS) |

## 代码路径配置

```python
# 模型路径
XTTS_MODEL_PATH = "packages/models/xtts_v2/extracted"
OPENVOICE_MODEL_PATH = "packages/models/openvoice/extracted"
WHISPER_MODEL_PATH = "packages/models/whisper/extracted"
GPT_SOVITS_PATH = "packages/repos/GPT-SoVITS"

# 工具路径
FFMPEG_PATH = "packages/tools/extracted/ffmpeg.exe"
```

## 注意事项

1. `extracted/` 目录中的文件已在 `.gitignore` 中，不会被提交到仓库
2. 所有分卷包 (`*.pkg.part_*`) 会被提交，用于完整性恢复
3. 首次使用需要手动执行还原命令
4. 解压后可删除 `.tar` 和 `.zip` 临时文件以节省空间
5. **Windows 用户**: 使用 PowerShell 执行命令，确保 `tar` 命令可用
