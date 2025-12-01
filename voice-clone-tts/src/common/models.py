"""
数据模型定义

定义 微服务版本使用的所有数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid
import time


# ===================== 枚举定义 =====================

class EngineType(str, Enum):
    """引擎类型"""
    XTTS = "xtts"
    OPENVOICE = "openvoice"
    GPT_SOVITS = "gpt-sovits"


class WorkerStatus(str, Enum):
    """工作节点状态"""
    STANDBY = "standby"      # 待机（模型未加载）
    LOADING = "loading"      # 加载中
    READY = "ready"          # 就绪（可接受请求）
    BUSY = "busy"            # 繁忙
    ERROR = "error"          # 错误
    OFFLINE = "offline"      # 离线


class AnnouncementType(str, Enum):
    """公告类型"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"


# ===================== 节点相关模型 =====================

class NodeInfo(BaseModel):
    """节点信息"""
    # 使用 UUID 前 8 位作为短 ID (约 40 亿种可能，对于节点管理足够)
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    engine_type: EngineType
    host: str
    port: int
    status: WorkerStatus = WorkerStatus.OFFLINE
    model_loaded: bool = False
    registered_at: float = Field(default_factory=time.time)
    last_heartbeat: float = Field(default_factory=time.time)

    # 资源信息
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    gpu_percent: float = 0.0
    gpu_memory_percent: float = 0.0

    # 统计信息
    request_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    current_concurrent: int = 0

    @property
    def address(self) -> str:
        """节点地址"""
        return f"{self.host}:{self.port}"

    @property
    def is_available(self) -> bool:
        """节点是否可用"""
        return self.status == WorkerStatus.READY and self.model_loaded


class NodeMetrics(BaseModel):
    """节点指标"""
    node_id: str
    timestamp: float = Field(default_factory=time.time)

    # 系统资源
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    gpu_percent: float = 0.0
    gpu_memory_percent: float = 0.0
    gpu_memory_used_mb: float = 0.0

    # 业务指标
    status: WorkerStatus = WorkerStatus.OFFLINE
    current_concurrent: int = 0
    queue_size: int = 0
    request_count: int = 0
    error_count: int = 0
    avg_response_time_ms: float = 0.0


class NodeCommand(BaseModel):
    """节点控制命令"""
    command: str  # start, stop, load_model, unload_model, activate, standby
    params: Dict[str, Any] = {}


# ===================== API 请求/响应模型 =====================

class SynthesizeRequest(BaseModel):
    """语音合成请求"""
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str
    engine: Optional[EngineType] = None  # 可选，不指定则使用默认
    language: str = "zh"
    output_format: str = "wav"

    # 高级参数
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)


class SynthesizeResponse(BaseModel):
    """语音合成响应"""
    success: bool
    message: str = ""
    audio_url: Optional[str] = None
    audio_size: int = 0
    duration_ms: float = 0.0
    engine_used: Optional[str] = None
    node_used: Optional[str] = None


class ExtractVoiceRequest(BaseModel):
    """提取音色请求"""
    voice_id: Optional[str] = None
    voice_name: str = ""
    reference_text: str = ""  # GPT-SoVITS 需要
    engine: Optional[EngineType] = None


class ExtractVoiceResponse(BaseModel):
    """提取音色响应"""
    success: bool
    message: str = ""
    voice_id: str = ""
    voice_name: str = ""
    engine: str = ""


class VoiceInfo(BaseModel):
    """音色信息"""
    voice_id: str
    name: str
    engine: str
    created_at: float
    source_audio: str = ""
    metadata: Dict[str, Any] = {}


class BatchSynthesizeRequest(BaseModel):
    """批量合成请求"""
    texts: List[str]
    voice_id: str
    engine: Optional[EngineType] = None
    language: str = "zh"


class BatchSynthesizeResponse(BaseModel):
    """批量合成响应"""
    success: bool
    message: str = ""
    results: List[Dict[str, Any]] = []
    total: int = 0
    succeeded: int = 0
    failed: int = 0


# ===================== 管理相关模型 =====================

class Announcement(BaseModel):
    """系统公告"""
    # 使用 UUID 前 8 位作为短 ID (约 40 亿种可能，对于公告管理足够)
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: AnnouncementType = AnnouncementType.INFO
    title: str
    message: str
    created_at: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class SystemConfig(BaseModel):
    """系统配置"""
    # 限流配置
    global_rpm: int = 1000  # 全局每分钟请求数
    ip_rpm: int = 100  # 单 IP 每分钟请求数
    concurrent_limit: int = 50  # 并发限制

    # 默认设置
    default_engine: EngineType = EngineType.XTTS

    # 日志级别
    log_level: str = "INFO"

    # 心跳配置
    heartbeat_interval: int = 10  # 秒
    dead_threshold: int = 30  # 超时阈值

    # WebSocket 配置
    ws_broadcast_interval: float = 2.0  # 状态广播间隔（秒）

    # 超时配置（秒）
    request_timeout: float = 60.0      # API 请求超时
    batch_timeout: float = 120.0       # 批量请求超时
    health_check_timeout: float = 5.0  # 健康检查超时


class SystemStatus(BaseModel):
    """系统状态概览"""
    online_nodes: int = 0
    total_nodes: int = 0
    total_requests: int = 0
    current_concurrent: int = 0
    avg_response_time_ms: float = 0.0

    # 各引擎状态
    engines: Dict[str, Dict[str, Any]] = {}

    # 公告
    announcements: List[Announcement] = []


# ===================== 健康检查模型 =====================

class HealthCheck(BaseModel):
    """健康检查结果"""
    status: str = "healthy"  # healthy, degraded, unhealthy
    version: str = "3.4.3"
    uptime_seconds: float = 0.0
    timestamp: float = Field(default_factory=time.time)

    # 组件状态
    components: Dict[str, Dict[str, Any]] = {}


class EndpointHealth(BaseModel):
    """接口健康状态"""
    endpoint: str
    method: str = "POST"
    status: str = "ok"  # ok, slow, error
    status_code: int = 200
    response_time_ms: float = 0.0
    last_check: float = Field(default_factory=time.time)
    error_message: str = ""
