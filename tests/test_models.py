"""
模型测试
"""
import pytest
from pathlib import Path

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEngineType:
    """测试引擎类型枚举"""

    def test_engine_values(self):
        """测试引擎枚举值"""
        from src.common.models import EngineType

        assert EngineType.XTTS.value == "xtts"
        assert EngineType.OPENVOICE.value == "openvoice"
        assert EngineType.GPT_SOVITS.value == "gpt-sovits"

    def test_engine_string_comparison(self):
        """测试引擎字符串比较（使用 .value 显式比较）"""
        from src.common.models import EngineType

        # 使用 .value 进行显式比较（更安全的做法）
        assert EngineType.XTTS.value == "xtts"
        assert EngineType.OPENVOICE.value == "openvoice"
        assert EngineType.GPT_SOVITS.value == "gpt-sovits"


class TestWorkerStatus:
    """测试工作节点状态枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        from src.common.models import WorkerStatus

        assert WorkerStatus.STANDBY.value == "standby"
        assert WorkerStatus.LOADING.value == "loading"
        assert WorkerStatus.READY.value == "ready"
        assert WorkerStatus.BUSY.value == "busy"
        assert WorkerStatus.ERROR.value == "error"
        assert WorkerStatus.OFFLINE.value == "offline"


class TestNodeInfo:
    """测试节点信息模型"""

    def test_create_node_info(self):
        """测试创建节点信息"""
        from src.common.models import NodeInfo, EngineType, WorkerStatus

        node = NodeInfo(
            engine_type=EngineType.XTTS,
            host="localhost",
            port=8001,
        )

        assert node.engine_type == EngineType.XTTS
        assert node.host == "localhost"
        assert node.port == 8001
        assert node.status == WorkerStatus.OFFLINE
        assert node.model_loaded is False
        assert node.node_id is not None

    def test_node_address(self):
        """测试节点地址属性"""
        from src.common.models import NodeInfo, EngineType

        node = NodeInfo(
            engine_type=EngineType.XTTS,
            host="192.168.1.1",
            port=8001,
        )

        assert node.address == "192.168.1.1:8001"

    def test_node_availability(self):
        """测试节点可用性"""
        from src.common.models import NodeInfo, EngineType, WorkerStatus

        node = NodeInfo(
            engine_type=EngineType.XTTS,
            host="localhost",
            port=8001,
        )

        # 默认不可用
        assert node.is_available is False

        # 设置为就绪状态且模型已加载
        node.status = WorkerStatus.READY
        node.model_loaded = True
        assert node.is_available is True

        # 只有状态就绪但模型未加载
        node.model_loaded = False
        assert node.is_available is False


class TestSynthesizeRequest:
    """测试合成请求模型"""

    def test_create_request(self):
        """测试创建合成请求"""
        from src.common.models import SynthesizeRequest

        request = SynthesizeRequest(
            text="你好世界",
            voice_id="test_voice",
            language="zh",
        )

        assert request.text == "你好世界"
        assert request.voice_id == "test_voice"
        assert request.language == "zh"
        assert request.speed == 1.0
        assert request.output_format == "wav"

    def test_request_validation(self):
        """测试请求验证"""
        from src.common.models import SynthesizeRequest
        from pydantic import ValidationError

        # 空文本应该失败
        with pytest.raises(ValidationError):
            SynthesizeRequest(
                text="",
                voice_id="test",
            )

        # 速度超出范围应该失败
        with pytest.raises(ValidationError):
            SynthesizeRequest(
                text="test",
                voice_id="test",
                speed=3.0,  # 超出 0.5-2.0 范围
            )


class TestVoiceInfo:
    """测试音色信息模型"""

    def test_create_voice_info(self):
        """测试创建音色信息"""
        from src.common.models import VoiceInfo
        import time

        voice = VoiceInfo(
            voice_id="test_voice",
            name="测试音色",
            engine="xtts",
            created_at=time.time(),
        )

        assert voice.voice_id == "test_voice"
        assert voice.name == "测试音色"
        assert voice.engine == "xtts"


class TestAnnouncement:
    """测试公告模型"""

    def test_create_announcement(self):
        """测试创建公告"""
        from src.common.models import Announcement, AnnouncementType

        ann = Announcement(
            type=AnnouncementType.INFO,
            title="测试公告",
            message="这是一条测试公告",
        )

        assert ann.type == AnnouncementType.INFO
        assert ann.title == "测试公告"
        assert ann.message == "这是一条测试公告"
        assert ann.is_expired is False

    def test_announcement_expiry(self):
        """测试公告过期"""
        from src.common.models import Announcement, AnnouncementType
        import time

        # 已过期的公告
        expired_ann = Announcement(
            type=AnnouncementType.INFO,
            title="过期公告",
            message="这是一条过期公告",
            expires_at=time.time() - 100,  # 100 秒前过期
        )

        assert expired_ann.is_expired is True

        # 未过期的公告
        valid_ann = Announcement(
            type=AnnouncementType.INFO,
            title="有效公告",
            message="这是一条有效公告",
            expires_at=time.time() + 3600,  # 1 小时后过期
        )

        assert valid_ann.is_expired is False


class TestHealthCheck:
    """测试健康检查模型"""

    def test_create_health_check(self):
        """测试创建健康检查"""
        from src.common.models import HealthCheck

        health = HealthCheck(
            status="healthy",
            version="3.0.0",
            uptime_seconds=100.0,
        )

        assert health.status == "healthy"
        assert health.version == "3.0.0"
        assert health.uptime_seconds == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
