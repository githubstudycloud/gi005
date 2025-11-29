# Voice Clone TTS 集成指南

本文档介绍如何将 Voice Clone TTS 集成到你的项目中。

## 目录

1. [Python 集成](#python-集成)
2. [HTTP API 集成](#http-api-集成)
3. [Docker 部署](#docker-部署)
4. [最佳实践](#最佳实践)

---

## Python 集成

### 安装

```bash
pip install voice-clone-tts
# 或从源码安装
pip install -e ./voice-clone-tts
```

### 基础使用

```python
from voice_clone_tts import VoiceCloner

# 创建克隆器
cloner = VoiceCloner(engine="xtts", device="cuda")

# 提取音色
voice = cloner.extract(
    audio="reference.wav",
    voice_id="speaker1"
)

# 合成语音
audio = cloner.synthesize(
    text="你好，世界！",
    voice_id="speaker1",
    language="zh"
)

# 保存音频
audio.save("output.wav")
```

### 异步使用

```python
import asyncio
from voice_clone_tts import AsyncVoiceCloner

async def main():
    cloner = AsyncVoiceCloner(engine="xtts")
    await cloner.load()

    # 并行合成多个文本
    texts = ["第一句", "第二句", "第三句"]
    tasks = [
        cloner.synthesize(text, voice_id="speaker1", language="zh")
        for text in texts
    ]
    audios = await asyncio.gather(*tasks)

    for i, audio in enumerate(audios):
        audio.save(f"output_{i}.wav")

asyncio.run(main())
```

### 流式合成

```python
from voice_clone_tts import VoiceCloner

cloner = VoiceCloner(engine="xtts")

# 流式获取音频块
for chunk in cloner.synthesize_stream(
    text="这是一段很长的文本...",
    voice_id="speaker1",
    language="zh"
):
    # 实时播放或处理
    play_audio(chunk)
```

---

## HTTP API 集成

### 启动服务

```bash
python -m voice_clone_tts serve --port 8000
```

### REST 客户端示例

#### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# 提取音色
with open("reference.wav", "rb") as f:
    resp = requests.post(
        f"{BASE_URL}/extract_voice",
        files={"audio": f},
        data={"voice_id": "speaker1"}
    )
    print(resp.json())

# 合成语音
resp = requests.post(
    f"{BASE_URL}/synthesize",
    json={
        "text": "你好世界",
        "voice_id": "speaker1",
        "language": "zh"
    }
)
with open("output.wav", "wb") as f:
    f.write(resp.content)
```

#### JavaScript (fetch)

```javascript
// 提取音色
const formData = new FormData();
formData.append('audio', audioFile);
formData.append('voice_id', 'speaker1');

const extractResp = await fetch('http://localhost:8000/extract_voice', {
    method: 'POST',
    body: formData
});
const result = await extractResp.json();

// 合成语音
const synthResp = await fetch('http://localhost:8000/synthesize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text: '你好世界',
        voice_id: 'speaker1',
        language: 'zh'
    })
});
const audioBlob = await synthResp.blob();
```

#### cURL

```bash
# 提取音色
curl -X POST http://localhost:8000/extract_voice \
    -F "audio=@reference.wav" \
    -F "voice_id=speaker1"

# 合成语音
curl -X POST http://localhost:8000/synthesize \
    -H "Content-Type: application/json" \
    -d '{"text":"你好世界","voice_id":"speaker1","language":"zh"}' \
    --output output.wav
```

### WebSocket 实时状态

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
        case 'system_status':
            updateDashboard(data.data);
            break;
        case 'node_online':
            addNode(data.data);
            break;
        case 'node_offline':
            removeNode(data.data.node_id);
            break;
    }
};

// 请求状态更新
ws.send(JSON.stringify({ type: 'get_status' }));
```

---

## Docker 部署

### 单服务部署

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["python", "main.py", "serve", "--engine", "xtts", "--port", "8000"]
```

```bash
# 构建镜像
docker build -t voice-clone-tts .

# 运行容器
docker run -p 8000:8000 -v ./models:/app/models voice-clone-tts
```

### Docker Compose 微服务

```yaml
# docker-compose.yml
version: '3.8'

services:
  gateway:
    build: .
    command: python -m v3.main gateway --port 8080
    ports:
      - "8080:8080"
    networks:
      - tts-net

  xtts-worker-1:
    build: .
    command: python -m v3.main worker --engine xtts --port 8001 --gateway http://gateway:8080
    volumes:
      - ./models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - tts-net

  xtts-worker-2:
    build: .
    command: python -m v3.main worker --engine xtts --port 8002 --gateway http://gateway:8080
    volumes:
      - ./models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - tts-net

networks:
  tts-net:
    driver: bridge
```

```bash
docker-compose up -d
```

---

## 最佳实践

### 1. 音色管理

```python
from voice_clone_tts import VoiceManager

manager = VoiceManager("./voices")

# 列出所有音色
voices = manager.list()
for voice in voices:
    print(f"{voice.voice_id}: {voice.name} ({voice.engine})")

# 导出音色
manager.export("speaker1", "speaker1_backup.zip")

# 导入音色
manager.import_voice("speaker1_backup.zip", "speaker1_restored")
```

### 2. 错误处理

```python
from voice_clone_tts import VoiceCloner
from voice_clone_tts.exceptions import (
    ModelNotLoadedError,
    VoiceNotFoundError,
    SynthesisError
)

cloner = VoiceCloner(engine="xtts")

try:
    audio = cloner.synthesize(
        text="测试",
        voice_id="unknown",
        language="zh"
    )
except VoiceNotFoundError:
    print("音色不存在")
except ModelNotLoadedError:
    print("模型未加载")
    cloner.load_model()
except SynthesisError as e:
    print(f"合成失败: {e}")
```

### 3. 性能优化

```python
from voice_clone_tts import VoiceCloner

# 预加载模型
cloner = VoiceCloner(engine="xtts", device="cuda")
cloner.load_model()

# 预热 (首次合成较慢)
cloner.warmup()

# 批量处理
texts = ["文本1", "文本2", "文本3"]
audios = cloner.batch_synthesize(
    texts=texts,
    voice_id="speaker1",
    language="zh",
    batch_size=4
)
```

### 4. 资源清理

```python
from voice_clone_tts import VoiceCloner

cloner = VoiceCloner(engine="xtts")
cloner.load_model()

try:
    # 使用克隆器
    audio = cloner.synthesize(...)
finally:
    # 释放资源
    cloner.unload_model()
```

或使用上下文管理器:

```python
from voice_clone_tts import VoiceCloner

with VoiceCloner(engine="xtts") as cloner:
    audio = cloner.synthesize(...)
# 自动释放资源
```

### 5. 日志配置

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 调整模块日志级别
logging.getLogger('voice_clone_tts').setLevel(logging.DEBUG)
logging.getLogger('TTS').setLevel(logging.WARNING)
```

---

## 常见集成场景

### 聊天机器人集成

```python
from voice_clone_tts import VoiceCloner
import io

cloner = VoiceCloner(engine="xtts")

def text_to_speech(text: str, voice_id: str = "default") -> bytes:
    """将文本转换为语音"""
    audio = cloner.synthesize(
        text=text,
        voice_id=voice_id,
        language="zh"
    )
    buffer = io.BytesIO()
    audio.save(buffer, format="wav")
    return buffer.getvalue()

# 在聊天机器人中使用
def handle_message(message):
    response_text = generate_response(message)
    audio_data = text_to_speech(response_text)
    return {
        "text": response_text,
        "audio": audio_data
    }
```

### Web 应用集成

```python
from fastapi import FastAPI, UploadFile
from voice_clone_tts import VoiceCloner

app = FastAPI()
cloner = VoiceCloner(engine="xtts")

@app.post("/api/clone")
async def clone_voice(audio: UploadFile, voice_name: str):
    audio_data = await audio.read()
    voice = cloner.extract_from_bytes(
        audio_data,
        voice_id=generate_id(),
        voice_name=voice_name
    )
    return {"voice_id": voice.voice_id}

@app.post("/api/tts")
async def text_to_speech(text: str, voice_id: str):
    audio = cloner.synthesize(text, voice_id, language="zh")
    return StreamingResponse(
        audio.to_bytes(),
        media_type="audio/wav"
    )
```

---

## 下一步

- [API 参考](api/README.md) - 完整 API 文档
- [部署指南](DEPLOYMENT.md) - 生产环境部署
- [故障排除](TROUBLESHOOTING.md) - 常见问题解决
