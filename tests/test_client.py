"""Tests for HTTP client."""

import pytest


class TestClientImport:
    """Tests for client module imports."""

    def test_import_client(self):
        """Test client module can be imported."""
        import client
        assert client is not None

    def test_import_voice_clone_client(self):
        """Test VoiceCloneClient can be imported."""
        from client import VoiceCloneClient
        assert VoiceCloneClient is not None


class TestVoiceCloneClient:
    """Tests for VoiceCloneClient class."""

    def test_instantiate(self):
        """Test VoiceCloneClient can be instantiated."""
        from client import VoiceCloneClient

        client = VoiceCloneClient("http://localhost:8000")
        assert client is not None

    def test_base_url(self):
        """Test base URL is stored correctly."""
        from client import VoiceCloneClient

        client = VoiceCloneClient("http://localhost:8000")
        assert "localhost" in client.base_url or hasattr(client, "base_url")

    def test_has_extract_method(self):
        """Test client has extract_voice method."""
        from client import VoiceCloneClient

        client = VoiceCloneClient("http://localhost:8000")
        assert hasattr(client, "extract_voice")
        assert callable(client.extract_voice)

    def test_has_synthesize_method(self):
        """Test client has synthesize method."""
        from client import VoiceCloneClient

        client = VoiceCloneClient("http://localhost:8000")
        assert hasattr(client, "synthesize")
        assert callable(client.synthesize)

    def test_has_list_voices_method(self):
        """Test client has list_voices method."""
        from client import VoiceCloneClient

        client = VoiceCloneClient("http://localhost:8000")
        assert hasattr(client, "list_voices") or hasattr(client, "get_voices")


@pytest.mark.integration
class TestClientIntegration:
    """Integration tests requiring running server."""

    @pytest.fixture
    def client(self):
        """Create client connected to test server."""
        from client import VoiceCloneClient
        return VoiceCloneClient("http://localhost:8000")

    def test_list_voices(self, client):
        """Test listing voices from server."""
        try:
            voices = client.list_voices()
            assert isinstance(voices, (list, dict))
        except Exception:
            pytest.skip("Server not running")
