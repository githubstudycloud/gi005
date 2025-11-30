"""
异常定义

定义 微服务版本使用的所有异常类。
"""


class VoiceCloneError(Exception):
    """音色克隆基础异常"""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class EngineError(VoiceCloneError):
    """引擎相关错误"""
    def __init__(self, message: str, engine: str = ""):
        super().__init__(message, code="ENGINE_ERROR")
        self.engine = engine


class ModelNotLoadedError(EngineError):
    """模型未加载"""
    def __init__(self, engine: str):
        super().__init__(f"Engine {engine} model not loaded", engine)
        self.code = "MODEL_NOT_LOADED"


class NodeNotFoundError(VoiceCloneError):
    """节点未找到"""
    def __init__(self, node_id: str):
        super().__init__(f"Node {node_id} not found", code="NODE_NOT_FOUND")
        self.node_id = node_id


class NoAvailableNodeError(VoiceCloneError):
    """无可用节点"""
    def __init__(self, engine: str = ""):
        message = f"No available node for engine {engine}" if engine else "No available node"
        super().__init__(message, code="NO_AVAILABLE_NODE")
        self.engine = engine


class VoiceNotFoundError(VoiceCloneError):
    """音色未找到"""
    def __init__(self, voice_id: str):
        super().__init__(f"Voice {voice_id} not found", code="VOICE_NOT_FOUND")
        self.voice_id = voice_id


class RateLimitExceededError(VoiceCloneError):
    """超出限流"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")


class RequestTimeoutError(VoiceCloneError):
    """请求超时"""
    def __init__(self, message: str = "Request timeout"):
        super().__init__(message, code="REQUEST_TIMEOUT")


class InvalidRequestError(VoiceCloneError):
    """无效请求"""
    def __init__(self, message: str):
        super().__init__(message, code="INVALID_REQUEST")


class AuthenticationError(VoiceCloneError):
    """认证错误"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTH_ERROR")


class ConfigurationError(VoiceCloneError):
    """配置错误"""
    def __init__(self, message: str):
        super().__init__(message, code="CONFIG_ERROR")
