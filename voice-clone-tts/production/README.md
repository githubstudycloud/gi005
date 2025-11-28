# 音色克隆生产环境

从音频提取音色，使用提取的音色合成语音的生产级实现。

## 功能特点

- ✅ **音色提取**: 从参考音频提取音色特征并保存
- ✅ **语音合成**: 使用保存的音色生成任意文本的语音
- ✅ **HTTP API**: RESTful 接口，易于集成
- ✅ **命令行工具**: 快速测试和使用
- ✅ **多引擎支持**: XTTS、OpenVoice、GPT-SoVITS
- ✅ **跨平台**: 支持 Windows 和 Linux

## 目录结构

```
production/
├── README.md              # 本文档
├── requirements.txt       # Python 依赖
├── environment.yml        # Conda 环境配置
├── main.py               # 命令行入口
├── server.py             # HTTP API 服务
├── client.py             # Python 客户端（工具类）
├── common/               # 通用模块
│   ├── base.py          # 基类定义
│   └── utils.py         # 工具函数
├── xtts/                 # XTTS-v2 引擎
│   ├── cloner.py
│   └── requirements.txt
├── openvoice/            # OpenVoice 引擎
│   ├── cloner.py
│   └── requirements.txt
└── gpt-sovits/           # GPT-SoVITS 引擎
    ├── cloner.py
    └── requirements.txt
```

## 快速开始

### 1. 安装环境

**方式一: Conda（推荐）**

```bash
# 创建环境
conda env create -f environment.yml
conda activate voice-clone

# GPU 支持 (CUDA 11.8)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**方式二: pip**

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 选择引擎

| 引擎 | 安装难度 | 中文质量 | 推荐场景 |
|------|---------|---------|---------|
| **XTTS** | ⭐ 最简单 | ⭐⭐⭐ | 快速部署 |
| **OpenVoice** | ⭐⭐ 中等 | ⭐⭐⭐⭐ | 音色转换 |
| **GPT-SoVITS** | ⭐⭐⭐ 需要服务 | ⭐⭐⭐⭐⭐ | 中文首选 |

### 3. 命令行使用

```bash
# 提取音色
python main.py extract --engine xtts --audio reference.wav --voice-id my_voice

# 合成语音
python main.py synthesize --engine xtts --voice-id my_voice --text "你好世界" --output output.wav

# 快速克隆（一步完成）
python main.py quick --engine xtts --audio reference.wav --text "你好世界" --output output.wav

# 启动 HTTP 服务
python main.py serve --engine xtts --port 8000
```

### 4. HTTP API 使用

启动服务:
```bash
python server.py --engine xtts --port 8000
```

API 调用:
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

### 5. Python 集成

```python
from client import VoiceCloneClient, VoiceCloneService

# 方式一: 使用客户端
client = VoiceCloneClient("http://localhost:8000")
voice = client.extract_voice("reference.wav", voice_name="测试")
client.synthesize_to_file("你好世界", voice["voice_id"], "output.wav")

# 方式二: 使用服务封装
service = VoiceCloneService("http://localhost:8000")
service.clone_voice("你好世界", "reference.wav", "output.wav")
```

---

## 各引擎详细配置

### XTTS-v2（推荐快速部署）

**安装:**
```bash
pip install TTS
```

**使用:**
```bash
python main.py serve --engine xtts --port 8000
```

**特点:**
- 安装简单，一行 pip
- 支持 17 种语言
- 只需 6 秒参考音频

### OpenVoice

**安装:**
```bash
# 克隆仓库
git clone https://github.com/myshell-ai/OpenVoice.git
cd OpenVoice && pip install -e .

# 下载模型
# https://huggingface.co/myshell-ai/OpenVoiceV2
# 解压到 checkpoints_v2/

# 安装基础 TTS
pip install edge-tts
```

**使用:**
```bash
python main.py serve --engine openvoice --model-path checkpoints_v2/converter --port 8000
```

**特点:**
- 音色与内容分离
- 可将任意语音转换为目标音色

### GPT-SoVITS（中文最佳）

**安装:**
```bash
# 克隆仓库
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS && pip install -r requirements.txt

# 下载模型
# https://huggingface.co/lj1995/GPT-SoVITS
```

**启动 GPT-SoVITS 服务:**
```bash
cd GPT-SoVITS
python api_v2.py -a 127.0.0.1 -p 9880
```

**使用本项目:**
```bash
python main.py serve --engine gpt-sovits --port 8000
```

**注意:** GPT-SoVITS 提取音色时需要提供参考文本！

---

## API 接口文档

### POST /extract_voice

从音频提取音色

**请求:**
- `audio`: 音频文件 (multipart/form-data)
- `voice_id`: 音色ID（可选）
- `voice_name`: 音色名称（可选）
- `reference_text`: 参考文本（GPT-SoVITS 需要）

**响应:**
```json
{
  "success": true,
  "voice_id": "abc123",
  "name": "我的声音",
  "engine": "xtts"
}
```

### POST /synthesize

使用音色合成语音

**请求:**
```json
{
  "text": "你好世界",
  "voice_id": "abc123",
  "language": "zh"
}
```

**响应:** 音频文件 (audio/wav)

### GET /voices

列出所有音色

### DELETE /voices/{voice_id}

删除音色

---

## 常见问题

### Q: 模型下载很慢？

使用镜像:
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### Q: CUDA 内存不足？

使用 CPU 或减小批量:
```bash
python main.py serve --engine xtts --device cpu
```

### Q: 中文效果不好？

推荐使用 GPT-SoVITS 引擎，中文效果最佳。

---

## License

MIT License
