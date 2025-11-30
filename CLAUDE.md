# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice Clone TTS v3.1 - Enterprise-grade voice cloning microservices system supporting multiple engines (XTTS-v2, OpenVoice, GPT-SoVITS).

## Architecture

```
Client → Gateway (:8080) → Workers (:8001-8003)
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
  XTTS    OpenVoice  GPT-SoVITS
 :8001     :8002       :8003
```

**Key patterns:**
- Service Registry: Workers auto-register with gateway via `/api/nodes/register`, send heartbeats every 10s to `/api/nodes/{node_id}/heartbeat`
- Worker Lifecycle: `start()` → `activate()` (load model) → `READY` state → `stop()` with graceful drain
- Load Balancing: Round-robin distribution across workers with `status=READY`
- All endpoints are async (FastAPI with `lifespan` context manager)

**Core modules in `voice-clone-tts/src/`:**
- `main.py` - CLI entry (gateway/worker/standalone modes)
- `gateway/app.py` - FastAPI routes, request routing
- `gateway/registry.py` - Service discovery, health tracking (dead_threshold: 30s)
- `gateway/limiter.py` - Rate limiting (global/IP/concurrent)
- `workers/base_worker.py` - Abstract worker class with lifecycle (`load_model`, `unload_model`, `synthesize`, `extract_voice`)
- `workers/xtts_worker.py`, `openvoice_worker.py`, `gpt_sovits_worker.py` - Engine implementations
- `common/models.py` - Pydantic models (SynthesizeRequest, NodeInfo, WorkerStatus enum, etc.)
- `common/paths.py` - Centralized path configuration (all paths relative to project root)

## Build & Run

```bash
# Install dependencies
pip install -r voice-clone-tts/requirements.txt

# GPU support (CUDA 11.8)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Restore models (from split archives)
cd packages/models/xtts_v2
cat xtts_v2_full.pkg.part_* > xtts_v2.tar && tar -xvf xtts_v2.tar -C extracted/
```

**Run modes:**
```bash
cd voice-clone-tts

# Standalone (dev/test)
python -m src.main standalone --engine xtts --port 8080

# Distributed (production)
python -m src.main gateway --port 8080
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load

# Docker
docker-compose up -d gateway xtts-worker
```

## Testing

```bash
# Run all tests
pytest -v

# Run single test file
pytest tests/test_gateway.py -v

# Run specific test
pytest tests/test_gateway.py::test_health_endpoint -v

# With coverage
pytest --cov=voice-clone-tts/src
```

**Key fixtures** (in `tests/conftest.py`):
- `gateway_app`, `gateway_client` - FastAPI test client for gateway
- `xtts_worker`, `loaded_xtts_worker` - Worker instances (loaded version requires model files)
- `sample_audio_en`, `sample_audio_zh` - Test audio files (skipped if missing)
- `xtts_model_path`, `openvoice_model_path` - Model directory paths

## Linting

```bash
# Format code
black voice-clone-tts/src tests/

# Sort imports
isort voice-clone-tts/src tests/

# Type check
mypy voice-clone-tts/src
```

## Configuration

Main config file: `voice-clone-tts/config.yaml` - Contains gateway settings (port, rate limits), worker configs per engine, audio settings, and logging config. Environment variables override config file values.

## Key Paths

Models are stored as split archives in `packages/models/`:
- XTTS-v2: `packages/models/xtts_v2/extracted/` (~2GB)
- OpenVoice: `packages/models/openvoice/extracted/` (~126MB)
- Whisper: `packages/models/whisper/extracted/` (~1.5GB)

All paths defined in `voice-clone-tts/src/common/paths.py` are relative to project root. Use `verify_model_paths()` to check model availability.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DEVICE` | cuda | Compute device (cuda/cpu) |
| `GATEWAY_PORT` | 8080 | Gateway port |
| `LOG_LEVEL` | INFO | Logging verbosity |
| `GPT_SOVITS_API_URL` | http://127.0.0.1:9880 | GPT-SoVITS backend |
| `HF_ENDPOINT` | (default) | HuggingFace mirror (use https://hf-mirror.com in China) |
