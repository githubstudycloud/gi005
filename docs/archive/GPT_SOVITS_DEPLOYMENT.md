# GPT-SoVITS 部署指南

本文档说明如何部署和使用 GPT-SoVITS 服务。

## 概述

GPT-SoVITS 是一个高质量中文语音克隆引擎，由于其依赖与主项目存在冲突，需要独立部署。

## 环境要求

- Python 3.10.x
- CUDA 11.8+ (GPU 推荐)
- 约 8GB 磁盘空间（模型文件）
- 约 8GB 显存（GPU 模式）

## 安装步骤

### 1. 创建独立 Python 环境

```bash
# 使用 venv
python -m venv gpt-sovits-venv
gpt-sovits-venv\Scripts\activate  # Windows
source gpt-sovits-venv/bin/activate  # Linux/Mac

# 或使用 conda
conda create -n gpt-sovits python=3.10
conda activate gpt-sovits
```

### 2. 安装依赖

```bash
cd GPT-SoVITS
pip install -r requirements.txt

# GPU 支持
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 3. 模型文件

模型文件位于 `GPT-SoVITS/GPT_SoVITS/pretrained_models/`，包括：

| 目录 | 文件 | 大小 | 用途 |
|------|------|------|------|
| 根目录 | s2Gv3.pth | 734MB | v3 生成器 |
| 根目录 | s2D488k.pth, s2G488k.pth | 192MB | 基础模型 |
| gsv-v4-pretrained | s2Gv4.pth, vocoder.pth | 790MB | v4 模型 |
| v2Pro | s2Gv2Pro*.pth, s2Dv2Pro*.pth | 588MB | v2Pro 模型 |
| chinese-roberta | pytorch_model.bin | 622MB | 中文语言模型 |
| chinese-hubert | pytorch_model.bin | 181MB | 音频特征提取 |

如需重新下载：

```bash
# 使用 HuggingFace 镜像加速
export HF_ENDPOINT=https://hf-mirror.com

# 或使用代理
curl -x http://your-proxy:port -L -o s2Gv3.pth \
  "https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/s2Gv3.pth"
```

## 启动服务

### API 服务器模式

```bash
cd GPT-SoVITS

# 启动 API 服务器 (默认端口 9880)
python api_v2.py -a 0.0.0.0 -p 9880

# 或指定 GPU
CUDA_VISIBLE_DEVICES=0 python api_v2.py -a 0.0.0.0 -p 9880
```

### 检查服务状态

```bash
curl http://127.0.0.1:9880/
```

## API 接口

### 语音合成

```bash
curl -G "http://127.0.0.1:9880/tts" \
  --data-urlencode "text=你好，这是语音合成测试" \
  --data-urlencode "text_lang=zh" \
  --data-urlencode "ref_audio_path=/path/to/reference.wav" \
  --data-urlencode "prompt_lang=zh" \
  --data-urlencode "prompt_text=参考音频的文本内容" \
  --output output.wav
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | ✅ | 要合成的文本 |
| text_lang | string | ✅ | 文本语言 (zh/en/ja/ko 等) |
| ref_audio_path | string | ✅ | 参考音频路径 |
| prompt_lang | string | ✅ | 参考音频的语言 |
| prompt_text | string | ❌ | 参考音频的文本内容 |

## 与主服务集成

主 voice-clone-tts 服务可以通过 HTTP 转发请求到 GPT-SoVITS API：

```python
# voice-clone-tts/production/gpt-sovits/cloner.py
import requests

class GPTSoVITSCloner:
    def __init__(self, api_url="http://127.0.0.1:9880"):
        self.api_url = api_url

    def synthesize(self, text, reference_audio, language="zh"):
        response = requests.get(
            f"{self.api_url}/tts",
            params={
                "text": text,
                "text_lang": language,
                "ref_audio_path": reference_audio,
                "prompt_lang": language
            }
        )
        return response.content
```

## 常见问题

### 1. CUDA 内存不足

```bash
# 使用 CPU 模式
python api_v2.py -a 0.0.0.0 -p 9880 --device cpu

# 或减小批处理大小
# 修改配置文件中的 batch_size
```

### 2. 模型加载失败

检查模型文件完整性：

```bash
ls -lh GPT_SoVITS/pretrained_models/*.pth
ls -lh GPT_SoVITS/pretrained_models/*/*.pth
```

### 3. 依赖冲突

GPT-SoVITS 使用以下特定版本：
- numpy<2.0
- transformers>=4.43,<=4.50
- pytorch-lightning>=2.4

这些与 XTTS/OpenVoice 的依赖冲突，因此需要独立环境。

## 性能优化

### GPU 模式

- 显存需求：约 6-8GB
- 首次加载：约 30 秒
- 合成速度：约 10-20 倍实时

### CPU 模式

- 内存需求：约 8GB
- 首次加载：约 60 秒
- 合成速度：约 0.5-1 倍实时

## 服务管理脚本

创建 `start_gpt_sovits.bat` (Windows):

```batch
@echo off
call gpt-sovits-venv\Scripts\activate
cd GPT-SoVITS
python api_v2.py -a 0.0.0.0 -p 9880
```

创建 `start_gpt_sovits.sh` (Linux/Mac):

```bash
#!/bin/bash
source gpt-sovits-venv/bin/activate
cd GPT-SoVITS
python api_v2.py -a 0.0.0.0 -p 9880
```

---

## 版本信息

- 文档版本: 1.0
- 更新日期: 2025-11-29
- GPT-SoVITS 版本: 最新 main 分支
