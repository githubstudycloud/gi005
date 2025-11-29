"""Tests for XTTS engine."""

import pytest
import os
from pathlib import Path


class TestXTTSImport:
    """Tests for XTTS module imports."""

    def test_import_cloner(self):
        """Test XTTSCloner can be imported."""
        from xtts import XTTSCloner
        assert XTTSCloner is not None

    def test_import_from_xtts_cloner(self):
        """Test importing from xtts.cloner module."""
        from xtts.cloner import XTTSCloner
        assert XTTSCloner is not None


class TestXTTSCloner:
    """Tests for XTTSCloner class."""

    def test_instantiate(self, xtts_cloner):
        """Test XTTSCloner can be instantiated."""
        assert xtts_cloner is not None
        assert hasattr(xtts_cloner, "device")

    def test_default_device(self):
        """Test default device is cpu."""
        from xtts import XTTSCloner
        cloner = XTTSCloner()
        assert cloner.device in ["cpu", "cuda"]

    def test_explicit_device(self):
        """Test explicit device setting."""
        from xtts import XTTSCloner
        cloner = XTTSCloner(device="cpu")
        assert cloner.device == "cpu"

    def test_has_load_model_method(self, xtts_cloner):
        """Test XTTSCloner has load_model method."""
        assert hasattr(xtts_cloner, "load_model")
        assert callable(xtts_cloner.load_model)

    def test_has_extract_voice_method(self, xtts_cloner):
        """Test XTTSCloner has extract_voice method."""
        assert hasattr(xtts_cloner, "extract_voice")
        assert callable(xtts_cloner.extract_voice)

    def test_has_synthesize_method(self, xtts_cloner):
        """Test XTTSCloner has synthesize method."""
        assert hasattr(xtts_cloner, "synthesize")
        assert callable(xtts_cloner.synthesize)

    def test_has_synthesize_simple_method(self, xtts_cloner):
        """Test XTTSCloner has synthesize_simple method."""
        assert hasattr(xtts_cloner, "synthesize_simple")
        assert callable(xtts_cloner.synthesize_simple)


@pytest.mark.slow
class TestXTTSSynthesis:
    """Integration tests for XTTS synthesis (requires model)."""

    def test_load_model(self, loaded_xtts_cloner):
        """Test model loads successfully."""
        assert loaded_xtts_cloner is not None

    def test_synthesize_simple(self, loaded_xtts_cloner, sample_audio, temp_output_dir):
        """Test simple synthesis without saving voice."""
        output_path = temp_output_dir / "test_output.wav"

        result = loaded_xtts_cloner.synthesize_simple(
            text="Hello world",
            reference_audio=sample_audio,
            output_path=str(output_path),
            language="en"
        )

        assert result is not None
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_synthesize_chinese(self, loaded_xtts_cloner, sample_audio, temp_output_dir):
        """Test Chinese synthesis."""
        output_path = temp_output_dir / "test_chinese.wav"

        result = loaded_xtts_cloner.synthesize_simple(
            text="你好世界",
            reference_audio=sample_audio,
            output_path=str(output_path),
            language="zh"
        )

        assert result is not None
        assert os.path.exists(output_path)

    def test_extract_voice(self, loaded_xtts_cloner, sample_audio, voices_dir):
        """Test voice extraction."""
        voice = loaded_xtts_cloner.extract_voice(
            audio_path=sample_audio,
            voice_id="test_extract",
            voice_name="Test Extract Voice"
        )

        assert voice is not None
        assert voice.voice_id == "test_extract"
        assert voice.engine == "xtts"

    def test_synthesize_with_saved_voice(self, loaded_xtts_cloner, sample_audio, temp_output_dir, voices_dir):
        """Test synthesis with saved voice embedding."""
        # First extract voice
        voice = loaded_xtts_cloner.extract_voice(
            audio_path=sample_audio,
            voice_id="test_synth_voice",
            voice_name="Test Synthesis Voice"
        )

        # Then synthesize
        output_path = temp_output_dir / "test_with_voice.wav"
        result = loaded_xtts_cloner.synthesize(
            text="This is a test",
            voice=voice,
            output_path=str(output_path),
            language="en"
        )

        assert result is not None
        assert os.path.exists(output_path)
