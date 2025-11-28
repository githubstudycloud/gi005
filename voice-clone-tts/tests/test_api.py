"""
API 测试
"""
import os
import sys
import pytest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "production"))


class TestHealthEndpoint:
    """测试健康检查端点"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient

        # 设置测试环境变量
        os.environ["VOICE_ENGINE"] = "xtts"
        os.environ["VOICES_DIR"] = "./test_voices"

        # 注意：这里跳过模型加载以加快测试速度
        # 实际测试需要先加载模型
        try:
            from server import app
            return TestClient(app)
        except Exception:
            pytest.skip("无法加载服务器，可能缺少模型")

    def test_health_check(self, client):
        """测试健康检查"""
        if client is None:
            pytest.skip("客户端未创建")

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "engine" in data


class TestConfigLoading:
    """测试配置加载"""

    def test_load_yaml_config(self):
        """测试加载 YAML 配置"""
        import yaml

        config_path = Path(__file__).parent.parent / "config.yaml"
        if not config_path.exists():
            pytest.skip("配置文件不存在")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        assert "server" in config
        assert "engine" in config
        assert "paths" in config
        assert "logging" in config

        # 验证默认值
        assert config["server"]["port"] == 8000
        assert config["engine"]["default"] == "xtts"

    def test_config_structure(self):
        """测试配置结构"""
        import yaml

        config_path = Path(__file__).parent.parent / "config.yaml"
        if not config_path.exists():
            pytest.skip("配置文件不存在")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 检查引擎配置
        assert "xtts" in config["engine"]
        assert "openvoice" in config["engine"]
        assert "gpt_sovits" in config["engine"]

        # 检查路径配置
        assert "voices_dir" in config["paths"]
        assert "output_dir" in config["paths"]


class TestVoiceEmbedding:
    """测试音色嵌入类"""

    def test_create_voice_embedding(self):
        """测试创建音色嵌入"""
        from common.base import VoiceEmbedding

        voice = VoiceEmbedding(
            voice_id="test_voice",
            name="Test Voice",
            engine="xtts"
        )

        assert voice.voice_id == "test_voice"
        assert voice.name == "Test Voice"
        assert voice.engine == "xtts"

    def test_voice_embedding_to_dict(self):
        """测试音色嵌入转字典"""
        from common.base import VoiceEmbedding

        voice = VoiceEmbedding(
            voice_id="test_voice",
            name="Test Voice",
            engine="xtts"
        )

        data = voice.to_dict()
        assert isinstance(data, dict)
        assert data["voice_id"] == "test_voice"
        assert data["name"] == "Test Voice"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
