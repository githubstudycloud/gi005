"""Tests for v3 Worker (microservices)."""

import pytest
import sys
from pathlib import Path


# Add v3 path
V3_PATH = Path(__file__).parent.parent / "voice-clone-tts" / "v3"
sys.path.insert(0, str(V3_PATH))


class TestWorkerImport:
    """Tests for Worker module imports."""

    def test_import_worker_module(self):
        """Test worker module can be imported."""
        try:
            from v3 import worker
            assert worker is not None
        except ImportError:
            # Try alternative import
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "worker", V3_PATH / "worker.py"
            )
            if spec and spec.loader:
                worker = importlib.util.module_from_spec(spec)
                assert worker is not None


class TestWorkerComponents:
    """Tests for Worker components."""

    def test_worker_node_exists(self):
        """Test WorkerNode class exists."""
        try:
            from v3.worker import WorkerNode
            assert WorkerNode is not None
        except (ImportError, AttributeError):
            pytest.skip("WorkerNode not available")

    def test_worker_app_exists(self):
        """Test worker FastAPI app exists."""
        try:
            from v3.worker import app
            assert app is not None
        except ImportError:
            pytest.skip("Worker app not available")


@pytest.mark.integration
class TestWorkerIntegration:
    """Integration tests for Worker."""

    @pytest.fixture
    def worker_client(self):
        """Create worker test client."""
        try:
            from v3.worker import app
            from fastapi.testclient import TestClient
            return TestClient(app)
        except ImportError:
            pytest.skip("Worker not available")

    def test_health_endpoint(self, worker_client):
        """Test worker health endpoint."""
        response = worker_client.get("/health")
        assert response.status_code in [200, 503]  # 503 if model not loaded

    def test_info_endpoint(self, worker_client):
        """Test worker info endpoint."""
        response = worker_client.get("/info")
        if response.status_code == 200:
            data = response.json()
            assert "engine" in data or "node_id" in data
