"""Pytest configuration and fixtures for Voice Clone TTS."""

import os
import sys
import pytest
from pathlib import Path

# Add source path to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "voice-clone-tts" / "src"
sys.path.insert(0, str(SRC_PATH))

# Set environment variables
os.environ["COQUI_TOS_AGREED"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


@pytest.fixture(scope="session")
def project_root():
    """Return project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def src_path():
    """Return source code directory."""
    return SRC_PATH


@pytest.fixture(scope="session")
def test_audio_path(project_root):
    """Return test audio directory."""
    return project_root / "test_audio"


@pytest.fixture(scope="session")
def sample_audio_en(test_audio_path):
    """Return English sample audio file path."""
    audio_path = test_audio_path / "sample_en.wav"
    if not audio_path.exists():
        pytest.skip("Sample audio file not found: sample_en.wav")
    return str(audio_path)


@pytest.fixture(scope="session")
def sample_audio_zh(test_audio_path):
    """Return Chinese sample audio file path."""
    audio_path = test_audio_path / "sample_zh.wav"
    if not audio_path.exists():
        pytest.skip("Sample audio file not found: sample_zh.wav")
    return str(audio_path)


@pytest.fixture(scope="session")
def voices_dir(project_root):
    """Return voices directory."""
    voices_path = project_root / "voice-clone-tts" / "voices"
    voices_path.mkdir(exist_ok=True)
    return voices_path


@pytest.fixture
def temp_output_dir(tmp_path):
    """Return temporary output directory."""
    return tmp_path


@pytest.fixture(scope="session")
def packages_path(project_root):
    """Return packages directory."""
    return project_root / "packages"


@pytest.fixture(scope="session")
def xtts_model_path(packages_path):
    """Return XTTS model path."""
    return packages_path / "models" / "xtts_v2" / "extracted"


@pytest.fixture(scope="session")
def openvoice_model_path(packages_path):
    """Return OpenVoice model path."""
    return packages_path / "models" / "openvoice" / "extracted"


# Gateway fixtures
@pytest.fixture(scope="module")
def gateway_app():
    """Create and return Gateway FastAPI app."""
    try:
        from gateway.app import create_gateway
        from common.models import SystemConfig

        config = SystemConfig()
        gateway = create_gateway(host="127.0.0.1", port=8080, config=config)
        return gateway.app
    except ImportError as e:
        pytest.skip(f"Gateway module not available: {e}")


@pytest.fixture(scope="module")
def gateway_client(gateway_app):
    """Create test client for gateway."""
    from fastapi.testclient import TestClient
    return TestClient(gateway_app)


# Worker fixtures
@pytest.fixture(scope="module")
def xtts_worker():
    """Create and return XTTS worker instance (not loaded)."""
    try:
        from workers.xtts_worker import XTTSWorker
        worker = XTTSWorker(
            host="127.0.0.1",
            port=8001,
            device="cpu",
        )
        return worker
    except ImportError as e:
        pytest.skip(f"XTTS worker module not available: {e}")


@pytest.fixture(scope="module")
def loaded_xtts_worker(xtts_worker, xtts_model_path):
    """Return XTTS worker with model loaded."""
    if not xtts_model_path.exists():
        pytest.skip(f"XTTS model not found at {xtts_model_path}")

    import asyncio
    try:
        # Use new_event_loop() for Python 3.10+ compatibility
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(xtts_worker.start())
            loop.run_until_complete(xtts_worker.activate())
            yield xtts_worker
        finally:
            # Cleanup: stop the worker
            loop.run_until_complete(xtts_worker.stop())
            loop.close()
    except Exception as e:
        pytest.skip(f"Failed to load XTTS model: {e}")
