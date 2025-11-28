# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice cloning TTS system supporting multiple engines (XTTS-v2, OpenVoice, GPT-SoVITS) with HTTP API and CLI interfaces.

## Common Commands

### Environment Setup

```bash
# Conda (recommended)
conda env create -f voice-clone-tts/production/environment.yml
conda activate voice-clone

# Or pip
pip install -r voice-clone-tts/production/requirements.txt

# GPU support (CUDA 11.8)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### CLI Usage

```bash
cd voice-clone-tts/production

# Extract voice from audio
python main.py extract --engine xtts --audio reference.wav --voice-id my_voice

# Synthesize speech
python main.py synthesize --engine xtts --voice-id my_voice --text "你好" --output output.wav

# Quick clone (extract + synthesize in one step)
python main.py quick --engine xtts --audio reference.wav --text "你好" --output output.wav

# Start HTTP server
python main.py serve --engine xtts --port 8000

# List saved voices
python main.py list --voices-dir ./voices
```

### Model Setup

XTTS-v2 model files are stored as split archives in `tts_model/`. To restore:

```bash
cd tts_model
cat xtts_v2.tar.part_* | tar -xvf -
```

## Architecture

### Core Components

- **[voice-clone-tts/production/](voice-clone-tts/production/)** - Production-ready implementation
  - `main.py` - CLI entry point with subcommands (extract, synthesize, serve, quick, list)
  - `server.py` - FastAPI HTTP server
  - `client.py` - Python client library
  - `common/base.py` - `VoiceClonerBase` abstract class and `VoiceEmbedding` dataclass

### Engine Abstraction

All engines inherit from `VoiceClonerBase` and implement:
- `load_model()` - Initialize the TTS model
- `extract_voice(audio_path, voice_id, ...)` - Extract voice embedding from reference audio
- `synthesize(text, voice, output_path, language)` - Generate speech with cloned voice

Engine implementations:
- `xtts/cloner.py` - XTTS-v2 (easiest setup, multi-language)
- `openvoice/cloner.py` - OpenVoice (voice conversion approach)
- `gpt-sovits/cloner.py` - GPT-SoVITS (best Chinese quality, requires separate API server)

### Voice Storage

Extracted voices are saved to `./voices/{voice_id}/`:
- `voice.json` - Metadata (VoiceEmbedding serialized)
- Engine-specific embedding files (.pt, .npy, etc.)

## HTTP API Endpoints

- `POST /extract_voice` - Upload audio, returns voice_id
- `POST /synthesize` - Text + voice_id, returns audio/wav
- `GET /voices` - List all voices
- `DELETE /voices/{voice_id}` - Remove voice

## Network Configuration

This project uses proxy `http://192.168.0.98:8800` for external access. Git is configured with:
- HTTP/HTTPS proxy in local git config
- SSH proxy via `~/.ssh/config` for GitHub

## Model Download Acceleration

```bash
export HF_ENDPOINT=https://hf-mirror.com
```
