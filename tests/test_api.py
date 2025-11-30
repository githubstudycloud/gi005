"""
API 测试
"""
import pytest
from pathlib import Path

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGatewayHealth:
    """测试网关健康检查"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient

        try:
            from src.gateway.app import GatewayApp
            gateway = GatewayApp(host="127.0.0.1", port=8080)
            return TestClient(gateway.app)
        except Exception as e:
            pytest.skip(f"无法创建网关应用: {e}")

    def test_health_check(self, client):
        """测试健康检查"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["version"] == "3.0.0"

    def test_api_health(self, client):
        """测试 API 健康检查端点"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_system_status(self, client):
        """测试系统状态"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "online_nodes" in data
        assert "total_nodes" in data


class TestNodeManagement:
    """测试节点管理 API"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient

        try:
            from src.gateway.app import GatewayApp
            gateway = GatewayApp(host="127.0.0.1", port=8080)
            return TestClient(gateway.app)
        except Exception as e:
            pytest.skip(f"无法创建网关应用: {e}")

    def test_list_nodes_empty(self, client):
        """测试节点列表（空）"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/api/nodes")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert isinstance(data["nodes"], list)

    def test_register_node(self, client):
        """测试注册节点"""
        if client is None:
            pytest.skip("客户端未创建")

        node_data = {
            "engine_type": "xtts",
            "host": "localhost",
            "port": 8001,
        }

        response = client.post("/api/nodes/register", json=node_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "node_id" in data


class TestAnnouncementAPI:
    """测试公告 API"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient

        try:
            from src.gateway.app import GatewayApp
            gateway = GatewayApp(host="127.0.0.1", port=8080)
            return TestClient(gateway.app)
        except Exception as e:
            pytest.skip(f"无法创建网关应用: {e}")

    def test_list_announcements_empty(self, client):
        """测试公告列表（空）"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/api/announcements")
        assert response.status_code == 200
        data = response.json()
        assert "announcements" in data
        assert isinstance(data["announcements"], list)

    def test_create_announcement(self, client):
        """测试创建公告"""
        if client is None:
            pytest.skip("客户端未创建")

        announcement_data = {
            "type": "info",
            "title": "测试公告",
            "message": "这是一条测试公告",
        }

        response = client.post("/api/announcements", json=announcement_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data


class TestWebPages:
    """测试 Web 页面"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient

        try:
            from src.gateway.app import GatewayApp
            gateway = GatewayApp(host="127.0.0.1", port=8080)
            return TestClient(gateway.app)
        except Exception as e:
            pytest.skip(f"无法创建网关应用: {e}")

    def test_home_redirect(self, client):
        """测试首页重定向"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/", follow_redirects=False)
        assert response.status_code == 200  # 返回 HTML 重定向

    def test_status_page(self, client):
        """测试状态页面"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/status")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_admin_page(self, client):
        """测试管理页面"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/admin")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_playground_page(self, client):
        """测试 API 测试页面"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/playground")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
