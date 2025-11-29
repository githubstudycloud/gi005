"""Tests for base classes and data structures."""

import pytest
from dataclasses import asdict


class TestVoiceEmbedding:
    """Tests for VoiceEmbedding dataclass."""

    def test_import(self):
        """Test VoiceEmbedding can be imported."""
        from common.base import VoiceEmbedding
        assert VoiceEmbedding is not None

    def test_create_instance(self):
        """Test creating VoiceEmbedding instance."""
        from common.base import VoiceEmbedding

        voice = VoiceEmbedding(
            voice_id="test_voice",
            engine="xtts",
            embedding_path="/path/to/embedding"
        )

        assert voice.voice_id == "test_voice"
        assert voice.engine == "xtts"
        assert voice.embedding_path == "/path/to/embedding"
        assert voice.voice_name is None
        assert voice.metadata == {}

    def test_create_with_optional_fields(self):
        """Test creating VoiceEmbedding with optional fields."""
        from common.base import VoiceEmbedding

        voice = VoiceEmbedding(
            voice_id="test_voice",
            engine="openvoice",
            embedding_path="/path/to/embedding",
            voice_name="Test Voice",
            metadata={"language": "zh", "gender": "female"}
        )

        assert voice.voice_name == "Test Voice"
        assert voice.metadata["language"] == "zh"
        assert voice.metadata["gender"] == "female"

    def test_to_dict(self):
        """Test converting VoiceEmbedding to dict."""
        from common.base import VoiceEmbedding

        voice = VoiceEmbedding(
            voice_id="test",
            engine="xtts",
            embedding_path="/path"
        )

        data = asdict(voice)
        assert isinstance(data, dict)
        assert data["voice_id"] == "test"


class TestVoiceClonerBase:
    """Tests for VoiceClonerBase abstract class."""

    def test_import(self):
        """Test VoiceClonerBase can be imported."""
        from common.base import VoiceClonerBase
        assert VoiceClonerBase is not None

    def test_is_abstract(self):
        """Test VoiceClonerBase is abstract and cannot be instantiated."""
        from common.base import VoiceClonerBase

        with pytest.raises(TypeError):
            VoiceClonerBase()

    def test_has_required_methods(self):
        """Test VoiceClonerBase has required abstract methods."""
        from common.base import VoiceClonerBase
        import inspect

        # Check abstract methods exist
        methods = [m[0] for m in inspect.getmembers(VoiceClonerBase, predicate=inspect.isfunction)]

        assert "load_model" in methods or hasattr(VoiceClonerBase, "load_model")
        assert "extract_voice" in methods or hasattr(VoiceClonerBase, "extract_voice")
        assert "synthesize" in methods or hasattr(VoiceClonerBase, "synthesize")
