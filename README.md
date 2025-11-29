# Voice Clone TTS

> A unified voice cloning text-to-speech system supporting multiple engines with HTTP API and CLI interfaces.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## Features

- **Multi-Engine Support**: XTTS-v2, OpenVoice, GPT-SoVITS
- **Voice Cloning**: Extract voice characteristics from 5-30 seconds audio
- **Multi-Language**: Chinese, English, Japanese, Korean, and more
- **Multiple Interfaces**: CLI, HTTP API, Python SDK
- **Microservices Ready**: Gateway + Worker distributed architecture (v3)
- **Production Ready**: Docker support, load balancing, health checks

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-repo/voice-clone-tts.git
cd voice-clone-tts
```

### 2. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# GPU support (optional, CUDA 11.8)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 3. Restore Model Files

```bash
# XTTS-v2 model (~2GB)
cd tts_model
cat xtts_v2.tar.part_* | tar -xvf -
cd ..
```

### 4. Quick Test

```bash
cd voice-clone-tts/production

# One-step clone + synthesize
python main.py quick \
    --engine xtts \
    --audio reference.wav \
    --text "Hello, this is a voice clone test" \
    --output output.wav \
    --language en
```

---

## Usage

### CLI Commands

| Command | Description |
|---------|-------------|
| `extract` | Extract voice from reference audio |
| `synthesize` | Synthesize speech with saved voice |
| `quick` | One-step extract + synthesize |
| `serve` | Start HTTP API server |
| `list` | List all saved voices |

```bash
# Extract voice
python main.py extract --engine xtts --audio ref.wav --voice-id my_voice

# Synthesize
python main.py synthesize --engine xtts --voice-id my_voice --text "Hello" --output out.wav

# Start server
python main.py serve --engine xtts --port 8000
```

### HTTP API

```bash
# Health check
curl http://localhost:8000/health

# Extract voice
curl -X POST http://localhost:8000/extract_voice \
    -F "audio=@reference.wav" \
    -F "voice_id=my_voice"

# Synthesize
curl -X POST http://localhost:8000/synthesize \
    -H "Content-Type: application/json" \
    -d '{"text":"Hello","voice_id":"my_voice","language":"en"}' \
    --output output.wav
```

### Python SDK

```python
from xtts import XTTSCloner

cloner = XTTSCloner(device="cuda")
cloner.load_model()

# Extract and synthesize
voice = cloner.extract_voice("reference.wav", voice_id="my_voice")
cloner.synthesize("Hello world", voice, "output.wav", language="en")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐│
│  │   CLI   │  │HTTP API │  │Python SDK│ │  WebSocket     ││
│  └────┬────┘  └────┬────┘  └────┬────┘  └───────┬─────────┘│
└───────┼────────────┼────────────┼───────────────┼───────────┘
        │            │            │               │
        ▼            ▼            ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Gateway (v3)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │Load Balancer│  │Service Disc │  │ Request Router      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ XTTS Worker   │    │OpenVoice Wkr │    │GPT-SoVITS Wkr│
│   :8001       │    │   :8002       │    │   :8003       │
└───────────────┘    └───────────────┘    └───────────────┘
```

### Core Components

| Component | Location | Description |
|-----------|----------|-------------|
| `VoiceClonerBase` | `common/base.py` | Abstract base class for all engines |
| `XTTSCloner` | `xtts/cloner.py` | XTTS-v2 implementation |
| `OpenVoiceCloner` | `openvoice/cloner.py` | OpenVoice implementation |
| `GPTSoVITSCloner` | `gpt-sovits/cloner.py` | GPT-SoVITS implementation |
| `Gateway` | `v3/gateway.py` | API gateway and load balancer |
| `Worker` | `v3/worker.py` | TTS worker node |

---

## Engine Comparison

| Feature | XTTS-v2 | OpenVoice | GPT-SoVITS |
|---------|---------|-----------|------------|
| Languages | 17+ | Chinese, English | Chinese, English, Japanese |
| Voice Quality | High | Very High | Excellent (Chinese) |
| Clone Speed | Fast | Medium | Slow |
| Setup Difficulty | Easy | Medium | Complex |
| GPU Memory | 4GB+ | 4GB+ | 8GB+ |
| Reference Audio | 3-10s | 5-30s | 3-10s |

---

## Project Structure

```
voice-clone-tts/
├── voice-clone-tts/
│   └── production/         # Production code
│       ├── main.py         # CLI entry point
│       ├── server.py       # HTTP server
│       ├── client.py       # Python client
│       ├── common/         # Shared components
│       ├── xtts/           # XTTS-v2 engine
│       ├── openvoice/      # OpenVoice engine
│       └── gpt-sovits/     # GPT-SoVITS engine
│   └── v3/                 # Microservices (v3)
│       ├── gateway.py      # API gateway
│       └── worker.py       # Worker node
├── packages/               # Installable packages
│   ├── models/             # Model files (split archives)
│   ├── tools/              # External tools (FFmpeg)
│   └── dependencies/       # Offline pip packages
├── docs/                   # Documentation
│   ├── INSTALL.md          # Installation guide
│   ├── USAGE.md            # Usage guide
│   ├── ARCHITECTURE.md     # Architecture design
│   └── INTEGRATION.md      # Integration guide
├── tts_model/              # Active model directory
├── voices/                 # Saved voice embeddings
└── test_audio/             # Test audio files
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [INSTALL.md](docs/INSTALL.md) | Step-by-step installation guide |
| [USAGE.md](docs/USAGE.md) | CLI, API, and SDK usage |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and diagrams |
| [INTEGRATION.md](docs/INTEGRATION.md) | Integration guide for your projects |
| [CLAUDE.md](CLAUDE.md) | AI assistant instructions |

---

## Requirements

### Hardware

| Level | CPU | RAM | GPU | Storage |
|-------|-----|-----|-----|---------|
| Minimum | 4 cores | 8GB | None (CPU mode) | 10GB |
| Recommended | 8 cores | 16GB | NVIDIA 6GB+ | 20GB |
| Production | 16 cores | 32GB | NVIDIA 12GB+ | 50GB |

### Software

- Python 3.10+
- FFmpeg 5.0+
- CUDA 11.8+ (optional, for GPU)

---

## API Reference

### Extract Voice

```
POST /extract_voice
Content-Type: multipart/form-data

Parameters:
  - audio: Audio file (WAV, MP3, FLAC)
  - voice_id: Unique voice identifier
  - voice_name: Display name (optional)

Response: {"success": true, "voice_id": "xxx"}
```

### Synthesize Speech

```
POST /synthesize
Content-Type: application/json

Body:
  {
    "text": "Text to synthesize",
    "voice_id": "saved_voice_id",
    "language": "zh"  // zh, en, ja, ko, etc.
  }

Response: audio/wav binary
```

### List Voices

```
GET /voices

Response:
  {
    "voices": [
      {"voice_id": "xxx", "name": "...", "engine": "xtts", "created_at": "..."}
    ]
  }
```

---

## Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py", "serve", "--engine", "xtts", "--port", "8000"]
```

```bash
docker build -t voice-clone-tts .
docker run -p 8000:8000 -v ./models:/app/models voice-clone-tts
```

---

## Contributing

Contributions are welcome! Please read our contributing guidelines first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Coqui TTS](https://github.com/coqui-ai/TTS) - XTTS-v2 model
- [OpenVoice](https://github.com/myshell-ai/OpenVoice) - Voice conversion
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - Chinese TTS

---

## Changelog

### v3.1.0 (Latest)
- Added streaming synthesis support
- Added batch processing
- Added audio preprocessing utilities
- Added OpenAPI documentation
- Improved project structure for open source

### v3.0.0
- Microservices architecture (Gateway + Workers)
- Service discovery and load balancing
- WebSocket real-time status

### v2.0.0
- Multi-engine support (XTTS, OpenVoice, GPT-SoVITS)
- HTTP API server
- Voice management system

---

## Support

- GitHub Issues: Report bugs or request features
- Documentation: Check the [docs](docs/) folder
- Examples: See [test_audio](test_audio/) for sample files
