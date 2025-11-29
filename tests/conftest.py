"""Pytest configuration and fixtures."""

import os
import sys
import pytest
from pathlib import Path

# Add production path to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
PRODUCTION_PATH = PROJECT_ROOT / "voice-clone-tts" / "production"
sys.path.insert(0, str(PRODUCTION_PATH))

# Set environment variables
os.environ["COQUI_TOS_AGREED"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


@pytest.fixture(scope="session")
def project_root():
    """Return project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def production_path():
    """Return production code directory."""
    return PRODUCTION_PATH


@pytest.fixture(scope="session")
def test_audio_path(project_root):
    """Return test audio directory."""
    return project_root / "test_audio"


@pytest.fixture(scope="session")
def sample_audio(test_audio_path):
    """Return sample audio file path."""
    audio_path = test_audio_path / "sample_en.wav"
    if not audio_path.exists():
        pytest.skip("Sample audio file not found")
    return str(audio_path)


@pytest.fixture(scope="session")
def voices_dir(project_root):
    """Return voices directory."""
    voices_path = project_root / "voices"
    voices_path.mkdir(exist_ok=True)
    return voices_path


@pytest.fixture
def temp_output_dir(tmp_path):
    """Return temporary output directory."""
    return tmp_path


@pytest.fixture(scope="module")
def xtts_cloner():
    """Create and return XTTS cloner instance."""
    try:
        from xtts import XTTSCloner
        cloner = XTTSCloner(device="cpu")
        return cloner
    except ImportError:
        pytest.skip("XTTS module not available")


@pytest.fixture(scope="module")
def loaded_xtts_cloner(xtts_cloner):
    """Return XTTS cloner with model loaded."""
    try:
        xtts_cloner.load_model()
        return xtts_cloner
    except Exception as e:
        pytest.skip(f"Failed to load XTTS model: {e}")
