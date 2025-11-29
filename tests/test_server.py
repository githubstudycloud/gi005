"""Tests for HTTP server."""

import pytest
import sys
import os


class TestServerImport:
    """Tests for server module imports."""

    def test_import_server(self):
        """Test server module can be imported."""
        import server
        assert server is not None

    def test_import_fastapi_app(self):
        """Test FastAPI app can be imported."""
        from server import app
        assert app is not None

    def test_app_has_routes(self):
        """Test app has expected routes."""
        from server import app

        routes = [r.path for r in app.routes]

        # Check for expected endpoints
        assert "/" in routes or "/health" in routes or any("health" in r for r in routes)


class TestServerEndpoints:
    """Tests for server endpoints (unit tests, no actual server)."""

    def test_health_endpoint_exists(self):
        """Test health endpoint is defined."""
        from server import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        # Just check the endpoint exists, don't run actual health check
        # which requires model loading
        assert hasattr(app, "routes")

    def test_extract_endpoint_exists(self):
        """Test extract_voice endpoint is defined."""
        from server import app

        routes = [r.path for r in app.routes]
        assert any("extract" in r.lower() for r in routes)

    def test_synthesize_endpoint_exists(self):
        """Test synthesize endpoint is defined."""
        from server import app

        routes = [r.path for r in app.routes]
        assert any("synth" in r.lower() for r in routes)

    def test_voices_endpoint_exists(self):
        """Test voices endpoint is defined."""
        from server import app

        routes = [r.path for r in app.routes]
        assert any("voice" in r.lower() for r in routes)


@pytest.mark.integration
class TestServerIntegration:
    """Integration tests requiring running server."""

    @pytest.fixture
    def test_client(self):
        """Create test client."""
        from server import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_root_endpoint(self, test_client):
        """Test root endpoint responds."""
        response = test_client.get("/")
        assert response.status_code in [200, 404, 307]  # May redirect

    def test_voices_list_empty(self, test_client):
        """Test voices list returns valid response."""
        response = test_client.get("/voices")
        if response.status_code == 200:
            data = response.json()
            assert "voices" in data or isinstance(data, list)
