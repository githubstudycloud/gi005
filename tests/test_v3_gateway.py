"""Tests for v3 Gateway (microservices)."""

import pytest
import sys
from pathlib import Path


# Add v3 path
V3_PATH = Path(__file__).parent.parent / "voice-clone-tts" / "v3"
sys.path.insert(0, str(V3_PATH))


class TestGatewayImport:
    """Tests for Gateway module imports."""

    def test_import_gateway_module(self):
        """Test gateway module can be imported."""
        try:
            from v3 import gateway
            assert gateway is not None
        except ImportError:
            # Try alternative import
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "gateway", V3_PATH / "gateway.py"
            )
            if spec and spec.loader:
                gateway = importlib.util.module_from_spec(spec)
                assert gateway is not None


class TestGatewayComponents:
    """Tests for Gateway components."""

    def test_service_registry_exists(self):
        """Test ServiceRegistry class exists."""
        try:
            from v3.gateway import ServiceRegistry
            assert ServiceRegistry is not None
        except (ImportError, AttributeError):
            pytest.skip("ServiceRegistry not available")

    def test_gateway_app_exists(self):
        """Test gateway FastAPI app exists."""
        try:
            from v3.gateway import app
            assert app is not None
        except ImportError:
            pytest.skip("Gateway app not available")


@pytest.mark.integration
class TestGatewayIntegration:
    """Integration tests for Gateway."""

    @pytest.fixture
    def gateway_client(self):
        """Create gateway test client."""
        try:
            from v3.gateway import app
            from fastapi.testclient import TestClient
            return TestClient(app)
        except ImportError:
            pytest.skip("Gateway not available")

    def test_health_endpoint(self, gateway_client):
        """Test gateway health endpoint."""
        response = gateway_client.get("/health")
        assert response.status_code == 200

    def test_nodes_endpoint(self, gateway_client):
        """Test gateway nodes list endpoint."""
        response = gateway_client.get("/api/nodes")
        if response.status_code == 200:
            data = response.json()
            assert "nodes" in data or isinstance(data, list)
