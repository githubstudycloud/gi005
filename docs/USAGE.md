# Voice Clone TTS 使用指南

本文档介绍如何使用 Voice Clone TTS 进行语音克隆和合成。

## 目录

1. [快速开始](#快速开始)
2. [命令行使用](#命令行使用)
3. [HTTP API 使用](#http-api-使用)
4. [Python 库使用](#python-库使用)
5. [微服务模式](#微服务模式)
6. [高级功能](#高级功能)

---

## 快速开始

### 30 秒体验

```bash
# 激活环境
cd voice-clone-tts/production
source ../venv/bin/activate  # Linux/macOS
# ..\venv\Scripts\activate   # Windows

# 一键克隆 + 合成
python main.py quick \
    --engine xtts \
    --audio sample.wav \
    --text "你好，这是克隆后的声音" \
    --output output.wav \
    --language zh
```

---

## 命令行使用

### 可用命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `extract` | 提取音色 | 从音频中提取音色特征 |
| `synthesize` | 合成语音 | 使用保存的音色合成语音 |
| `quick` | 快速克隆 | 一步完成提取+合成 |
| `serve` | 启动服务 | 启动 HTTP API 服务器 |
| `list` | 列出音色 | 显示所有保存的音色 |

### extract - 提取音色

从参考音频中提取音色特征并保存：

```bash
python main.py extract \
    --engine xtts \
    --audio reference.wav \
    --voice-id my_voice \
    --voice-name "我的音色"
```

**参数说明:**
- `--engine`: 引擎类型 (xtts/openvoice/gpt-sovits)
- `--audio`: 参考音频文件路径
- `--voice-id`: 音色唯一标识
- `--voice-name`: 音色显示名称 (可选)

**参考音频要求:**
- 格式: WAV (推荐), MP3, FLAC
- 采样率: 16kHz 以上
- 时长: 5-30 秒
- 质量: 清晰、无噪音、单人说话

### synthesize - 合成语音

使用已保存的音色合成语音：

```bash
python main.py synthesize \
    --engine xtts \
    --voice-id my_voice \
    --text "这是要合成的文本" \
    --output output.wav \
    --language zh
```

**参数说明:**
- `--voice-id`: 之前提取的音色 ID
- `--text`: 要合成的文本
- `--output`: 输出音频路径
- `--language`: 语言代码 (zh/en/ja/ko等)

### quick - 快速克隆

一步完成音色提取和语音合成：

```bash
python main.py quick \
    --engine xtts \
    --audio reference.wav \
    --text "Hello, this is a voice clone test" \
    --output output.wav \
    --language en
```

### serve - 启动服务

启动 HTTP API 服务器：

```bash
python main.py serve \
    --engine xtts \
    --port 8000 \
    --host 0.0.0.0 \
    --device cuda
```

**参数说明:**
- `--port`: 监听端口 (默认 8000)
- `--host`: 监听地址 (默认 0.0.0.0)
- `--device`: 计算设备 (cuda/cpu)

### list - 列出音色

```bash
python main.py list --voices-dir ./voices
```

---

## HTTP API 使用

### 启动服务器

```bash
python main.py serve --engine xtts --port 8000
```

### API 端点

#### 健康检查

```bash
curl http://localhost:8000/health
```

响应:
```json
{
    "status": "healthy",
    "engine": "xtts",
    "version": "2.0.0"
}
```

#### 提取音色

```bash
curl -X POST http://localhost:8000/extract_voice \
    -F "audio=@reference.wav" \
    -F "voice_id=my_voice" \
    -F "voice_name=我的音色"
```

响应:
```json
{
    "success": true,
    "voice_id": "my_voice",
    "message": "Voice extracted successfully"
}
```

#### 合成语音

```bash
curl -X POST http://localhost:8000/synthesize \
    -H "Content-Type: application/json" \
    -d '{
        "text": "你好，这是语音合成测试",
        "voice_id": "my_voice",
        "language": "zh"
    }' \
    --output output.wav
```

#### 列出音色

```bash
curl http://localhost:8000/voices
```

响应:
```json
{
    "voices": [
        {
            "voice_id": "my_voice",
            "name": "我的音色",
            "engine": "xtts",
            "created_at": "2024-01-01T12:00:00"
        }
    ]
}
```

#### 删除音色

```bash
curl -X DELETE http://localhost:8000/voices/my_voice
```

---

## Python 库使用

### 基础使用

```python
from xtts import XTTSCloner

# 创建克隆器
cloner = XTTSCloner(device="cuda")

# 加载模型
cloner.load_model()

# 提取音色
voice = cloner.extract_voice(
    audio_path="reference.wav",
    voice_id="my_voice",
    voice_name="我的音色"
)
print(f"音色已保存: {voice.voice_id}")

# 合成语音
output = cloner.synthesize(
    text="你好，这是克隆后的声音",
    voice=voice,
    output_path="output.wav",
    language="zh"
)
print(f"音频已保存: {output}")
```

### 快速克隆 (无需保存音色)

```python
from xtts import XTTSCloner

cloner = XTTSCloner(device="cuda")
cloner.load_model()

# 一步完成
output = cloner.synthesize_simple(
    text="这是测试文本",
    reference_audio="reference.wav",
    output_path="output.wav",
    language="zh"
)
```

### 使用 HTTP 客户端

```python
from client import VoiceCloneClient

# 连接服务器
client = VoiceCloneClient("http://localhost:8000")

# 提取音色
result = client.extract_voice(
    audio_path="reference.wav",
    voice_id="my_voice"
)

# 合成语音
audio_data = client.synthesize(
    text="你好世界",
    voice_id="my_voice",
    language="zh"
)

# 保存音频
with open("output.wav", "wb") as f:
    f.write(audio_data)
```

---

## 微服务模式

v3.0 版本支持分布式微服务架构。

### 架构说明

```
客户端 → 网关(Gateway) → 工作节点(Worker)
                ↓
        服务注册中心
```

### 启动网关

```bash
cd voice-clone-tts

# 启动网关
python -m v3.main gateway --port 8080
```

### 启动工作节点

```bash
# 启动 XTTS 工作节点
python -m v3.main worker \
    --engine xtts \
    --port 8001 \
    --gateway http://localhost:8080 \
    --auto-load
```

### 通过网关调用

```bash
# 合成请求会自动路由到可用节点
curl -X POST http://localhost:8080/api/synthesize \
    -H "Content-Type: application/json" \
    -d '{
        "text": "你好",
        "voice_id": "my_voice",
        "language": "zh"
    }' \
    --output output.wav
```

### 查看节点状态

```bash
curl http://localhost:8080/api/nodes
```

---

## 高级功能

### 调整语速

```bash
python main.py synthesize \
    --engine xtts \
    --voice-id my_voice \
    --text "这段话会说得快一些" \
    --speed 1.2 \
    --output fast.wav
```

### 调整音调

```bash
python main.py synthesize \
    --engine xtts \
    --voice-id my_voice \
    --text "这段话音调会高一些" \
    --pitch 1.1 \
    --output high.wav
```

### 多语言支持

支持的语言代码:

| 代码 | 语言 |
|------|------|
| zh | 中文 |
| en | 英语 |
| ja | 日语 |
| ko | 韩语 |
| fr | 法语 |
| de | 德语 |
| es | 西班牙语 |
| it | 意大利语 |

### 批量处理

```python
from xtts import XTTSCloner

cloner = XTTSCloner(device="cuda")
cloner.load_model()

texts = [
    "第一句话",
    "第二句话",
    "第三句话",
]

for i, text in enumerate(texts):
    cloner.synthesize(
        text=text,
        voice=voice,
        output_path=f"output_{i}.wav",
        language="zh"
    )
```

---

## 最佳实践

### 参考音频选择

1. **时长**: 10-20 秒最佳
2. **质量**: 清晰、无背景音乐/噪音
3. **内容**: 自然说话，避免过于情绪化
4. **格式**: WAV 格式，16kHz 以上采样率

### 性能优化

1. **使用 GPU**: 性能提升 5-10 倍
2. **批量处理**: 减少模型加载开销
3. **预加载模型**: 服务模式下自动预加载

### 质量提升

1. 使用高质量参考音频
2. 保持文本语言与参考音频一致
3. 适当调整 speed 和 pitch

---

## 下一步

- [架构文档](ARCHITECTURE.md) - 了解系统设计
- [集成指南](INTEGRATION.md) - 集成到你的项目
- [API 参考](api/README.md) - 完整 API 文档
