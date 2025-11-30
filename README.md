# Voice Clone TTS

> Enterprise-grade voice cloning microservices system supporting multiple TTS engines.

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Features

- **Microservices Architecture**: Gateway + Worker distributed deployment
- **Multi-Engine Support**: XTTS-v2, OpenVoice, GPT-SoVITS
- **Voice Cloning**: Extract voice from 5-30 seconds reference audio
- **Multi-Language**: Chinese, English, Japanese, Korean, and more
- **Production Ready**: Docker, load balancing, health checks, WebSocket

---

## Quick Start

### Standalone Mode (Development)

```bash
cd voice-clone-tts

# Install dependencies
pip install -r requirements.txt

# Start standalone server (Gateway + XTTS Worker)
python -m src.main standalone --engine xtts --port 8080
```

Access:
- Status: http://localhost:8080/status
- Admin: http://localhost:8080/admin
- API Test: http://localhost:8080/playground

### Distributed Mode (Production)

```bash
# Terminal 1: Start Gateway
python -m src.main gateway --port 8080

# Terminal 2: Start XTTS Worker
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load

# Terminal 3: Start OpenVoice Worker (optional)
python -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `gateway` | Start API gateway |
| `worker` | Start TTS worker node |
| `standalone` | Start gateway + single worker |

```bash
# Gateway
python -m src.main gateway --port 8080

# Worker
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080

# Standalone
python -m src.main standalone --engine xtts --port 8080
```

---

## HTTP API

```bash
# Health check
curl http://localhost:8080/health

# Extract voice
curl -X POST http://localhost:8080/api/extract_voice \
    -F "audio=@reference.wav" \
    -F "voice_name=my_voice"

# Synthesize
curl -X POST http://localhost:8080/api/synthesize \
    -H "Content-Type: application/json" \
    -d '{"text":"Hello","voice_id":"my_voice","language":"en"}' \
    --output output.wav

# List voices
curl http://localhost:8080/api/voices
```

---

## Architecture

```
Client -> Gateway (:8080) -> Workers (:8001-8003)
              |
    +---------+---------+
    v         v         v
  XTTS    OpenVoice  GPT-SoVITS
 :8001     :8002       :8003
```

---

## Project Structure

```
voice-clone-tts/
├── voice-clone-tts/
│   └── src/                  # Source code
│       ├── main.py           # CLI entry point
│       ├── common/           # Shared modules
│       │   ├── models.py     # Pydantic models
│       │   ├── paths.py      # Path configuration
│       │   ├── exceptions.py # Custom exceptions
│       │   └── logging.py    # Logging setup
│       ├── gateway/          # API Gateway
│       │   ├── app.py        # FastAPI application
│       │   ├── registry.py   # Service discovery
│       │   ├── limiter.py    # Rate limiting
│       │   └── websocket.py  # WebSocket handler
│       └── workers/          # TTS Workers
│           ├── base_worker.py
│           ├── xtts_worker.py
│           ├── openvoice_worker.py
│           └── gpt_sovits_worker.py
├── packages/
│   └── models/               # Model files (split archives)
│       ├── xtts_v2/          # XTTS-v2 model
│       └── openvoice/        # OpenVoice checkpoints
├── docs/                     # Documentation
│   ├── 00-索引.md            # Index
│   ├── 01-快速开始.md        # Quick start
│   ├── 02-安装部署.md        # Installation
│   ├── 03-使用指南.md        # Usage guide
│   ├── 04-架构设计.md        # Architecture
│   ├── 05-API参考.md         # API reference
│   ├── 06-常见问题.md        # FAQ
│   └── 07-更新日志.md        # Changelog
├── tests/                    # Test files
└── voices/                   # Voice embeddings
```

---

## Model Setup

```bash
# Restore XTTS-v2 model (~2GB)
cd packages/models/xtts_v2
cat xtts_v2_full.pkg.part_* > xtts_v2.tar
tar -xvf xtts_v2.tar -C extracted/

# Restore OpenVoice checkpoints
cd packages/models/openvoice
cat checkpoints_v2.pkg.part_* > checkpoints.tar
tar -xvf checkpoints.tar -C extracted/
```

---

## Docker Deployment

```bash
# Build image
cd voice-clone-tts
docker build -t voice-clone-tts:3.2.0 .

# Run with docker-compose
docker-compose up -d gateway xtts-worker

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Engine Comparison

| Engine | Voice Quality | Chinese | Setup | Reference Audio |
|--------|--------------|---------|-------|-----------------|
| **XTTS-v2** | High | Good | Easy | 6s |
| **OpenVoice** | Very High | Great | Medium | 3-10s |
| **GPT-SoVITS** | Excellent | Best | Complex | 5s |

---

## Requirements

- Python 3.10.x
- CUDA 11.8+ (for GPU)
- FFmpeg 5.0+
- 16GB+ RAM (recommended)
- NVIDIA GPU 6GB+ (recommended)

---

## Documentation

| Document | Description |
|----------|-------------|
| [00-索引](docs/00-索引.md) | Documentation index |
| [01-快速开始](docs/01-快速开始.md) | 5-minute quickstart |
| [02-安装部署](docs/02-安装部署.md) | Installation guide |
| [03-使用指南](docs/03-使用指南.md) | Usage guide |
| [04-架构设计](docs/04-架构设计.md) | Architecture |
| [05-API参考](docs/05-API参考.md) | API reference |
| [06-常见问题](docs/06-常见问题.md) | FAQ |
| [CLAUDE.md](CLAUDE.md) | AI assistant guide |

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Coqui TTS](https://github.com/coqui-ai/TTS) - XTTS-v2 model
- [OpenVoice](https://github.com/myshell-ai/OpenVoice) - Voice conversion
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - Chinese TTS
