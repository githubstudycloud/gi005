"""
工作节点基类

定义工作节点的通用接口和生命周期管理。
"""

import asyncio
import time
import uuid
import logging
import signal
import psutil
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from ..common.models import (
    NodeInfo,
    NodeMetrics,
    NodeCommand,
    WorkerStatus,
    EngineType,
    SynthesizeRequest,
    SynthesizeResponse,
    ExtractVoiceRequest,
    ExtractVoiceResponse,
    VoiceInfo,
    HealthCheck,
)
from ..common.exceptions import ModelNotLoadedError

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """工作节点基类"""

    def __init__(
        self,
        engine_type: EngineType,
        host: str = "0.0.0.0",
        port: int = 8001,
        gateway_url: Optional[str] = None,
        node_id: Optional[str] = None,
        auto_register: bool = True,
        heartbeat_interval: int = 10,
    ):
        """
        初始化工作节点

        Args:
            engine_type: 引擎类型
            host: 监听地址
            port: 监听端口
            gateway_url: 网关地址（用于注册）
            node_id: 节点 ID（不指定则自动生成）
            auto_register: 是否自动向网关注册
            heartbeat_interval: 心跳间隔（秒）
        """
        self.engine_type = engine_type
        self.host = host
        self.port = port
        self.gateway_url = gateway_url
        self.node_id = node_id or f"{engine_type.value}-{str(uuid.uuid4())[:8]}"
        self.auto_register = auto_register
        self.heartbeat_interval = heartbeat_interval

        # 状态
        self._status = WorkerStatus.STANDBY
        self._model_loaded = False
        self._start_time = time.time()

        # 统计
        self._request_count = 0
        self._error_count = 0
        self._current_concurrent = 0
        self._total_response_time = 0.0

        # 任务
        self._heartbeat_task: Optional[asyncio.Task] = None

        # FastAPI 应用
        self.app = self._create_app()

    # ===================== 抽象方法 =====================

    @abstractmethod
    async def load_model(self) -> bool:
        """
        加载模型

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def unload_model(self) -> bool:
        """
        卸载模型

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        language: str = "zh",
        **kwargs,
    ) -> bytes:
        """
        合成语音

        Args:
            text: 文本
            voice_id: 音色 ID
            language: 语言
            **kwargs: 其他参数

        Returns:
            音频数据
        """
        pass

    @abstractmethod
    async def extract_voice(
        self,
        audio_data: bytes,
        voice_id: str,
        voice_name: str = "",
        **kwargs,
    ) -> VoiceInfo:
        """
        提取音色

        Args:
            audio_data: 音频数据
            voice_id: 音色 ID
            voice_name: 音色名称
            **kwargs: 其他参数

        Returns:
            音色信息
        """
        pass

    # ===================== 生命周期 =====================

    async def start(self):
        """启动节点"""
        logger.info(f"Starting worker {self.node_id} ({self.engine_type.value})")

        # 注册到网关
        if self.auto_register and self.gateway_url:
            await self._register_to_gateway()

        # 启动心跳
        if self.gateway_url:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # 如果模型已加载，保持 READY 状态；否则设为 STANDBY
        if self._model_loaded:
            self._status = WorkerStatus.READY
        else:
            self._status = WorkerStatus.STANDBY
        logger.info(f"Worker {self.node_id} started (status: {self._status.value})")

    async def stop(self, timeout: float = 30.0):
        """
        停止节点

        Args:
            timeout: 停止操作的超时时间（秒）
        """
        logger.info(f"Stopping worker {self.node_id} (timeout={timeout}s)")

        async def _do_stop():
            # 停止心跳
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._heartbeat_task = None

            # 等待当前请求完成（最多等待一半的超时时间）
            wait_start = time.time()
            while self._current_concurrent > 0 and (time.time() - wait_start) < (timeout / 2):
                logger.info(f"Waiting for {self._current_concurrent} ongoing requests to complete...")
                await asyncio.sleep(0.5)

            if self._current_concurrent > 0:
                logger.warning(f"Force stopping with {self._current_concurrent} requests still in progress")

            # 卸载模型
            if self._model_loaded:
                await self.unload_model()

            # 从网关注销
            if self.gateway_url:
                await self._unregister_from_gateway()

        try:
            await asyncio.wait_for(_do_stop(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Worker stop timed out after {timeout}s")

        self._status = WorkerStatus.OFFLINE
        logger.info(f"Worker {self.node_id} stopped")

    async def activate(self) -> bool:
        """
        激活节点（加载模型）

        Returns:
            是否成功
        """
        if self._model_loaded:
            # 模型已加载，确保状态是 READY
            self._status = WorkerStatus.READY
            return True

        self._status = WorkerStatus.LOADING
        try:
            success = await self.load_model()
            if success:
                self._model_loaded = True
                self._status = WorkerStatus.READY
                logger.info(f"Worker {self.node_id} activated")
                return True
            else:
                self._status = WorkerStatus.ERROR
                return False
        except Exception as e:
            logger.error(f"Failed to activate worker: {e}")
            self._status = WorkerStatus.ERROR
            return False

    async def standby(self) -> bool:
        """
        进入待机（卸载模型）

        Returns:
            是否成功
        """
        if not self._model_loaded:
            return True

        try:
            success = await self.unload_model()
            if success:
                self._model_loaded = False
                self._status = WorkerStatus.STANDBY
                logger.info(f"Worker {self.node_id} on standby")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to standby worker: {e}")
            return False

    # ===================== 网关通信 =====================

    async def _register_to_gateway(self):
        """向网关注册"""
        if not self.gateway_url:
            return

        node_info = self._get_node_info()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.gateway_url}/api/nodes/register",
                    json=node_info.model_dump(),
                )
                if resp.status_code == 200:
                    logger.info(f"Registered to gateway: {self.gateway_url}")
                else:
                    logger.warning(f"Failed to register: {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to register to gateway: {e}")

    async def _unregister_from_gateway(self):
        """从网关注销"""
        if not self.gateway_url:
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.delete(
                    f"{self.gateway_url}/api/nodes/{self.node_id}"
                )
                if resp.status_code == 200:
                    logger.info("Unregistered from gateway")
        except Exception as e:
            logger.error(f"Failed to unregister: {e}")

    async def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            await self._send_heartbeat()

    async def _send_heartbeat(self):
        """发送心跳"""
        if not self.gateway_url:
            return

        metrics = self._get_metrics()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{self.gateway_url}/api/nodes/{self.node_id}/heartbeat",
                    json=metrics.model_dump(),
                )
        except Exception as e:
            logger.debug(f"Heartbeat failed: {e}")

    # ===================== 信息获取 =====================

    def _get_node_info(self) -> NodeInfo:
        """获取节点信息"""
        return NodeInfo(
            node_id=self.node_id,
            engine_type=self.engine_type,
            host=self.host,
            port=self.port,
            status=self._status,
            model_loaded=self._model_loaded,
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            request_count=self._request_count,
            error_count=self._error_count,
            current_concurrent=self._current_concurrent,
        )

    def _get_metrics(self) -> NodeMetrics:
        """获取节点指标"""
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()

        # GPU 指标（如果可用）
        gpu_percent = 0.0
        gpu_mem_percent = 0.0
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_percent = util.gpu
            gpu_mem_percent = (mem_info.used / mem_info.total) * 100
            pynvml.nvmlShutdown()
        except ImportError:
            # pynvml not installed, GPU metrics unavailable
            pass
        except Exception as e:
            logger.debug(f"Failed to get GPU metrics: {e}")

        avg_response_time = 0.0
        if self._request_count > 0:
            avg_response_time = self._total_response_time / self._request_count

        return NodeMetrics(
            node_id=self.node_id,
            status=self._status,
            cpu_percent=cpu,
            memory_percent=mem.percent,
            memory_used_mb=mem.used / (1024 * 1024),
            gpu_percent=gpu_percent,
            gpu_memory_percent=gpu_mem_percent,
            current_concurrent=self._current_concurrent,
            request_count=self._request_count,
            error_count=self._error_count,
            avg_response_time_ms=avg_response_time,
        )

    # ===================== FastAPI 应用 =====================

    def _create_app(self) -> FastAPI:
        """创建 FastAPI 应用"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self.start()
            yield
            await self.stop()

        app = FastAPI(
            title=f"Voice Clone Worker - {self.engine_type.value}",
            version="3.0.0",
            lifespan=lifespan,
        )

        # 路由
        app.add_api_route("/health", self._handle_health, methods=["GET"])
        app.add_api_route("/info", self._handle_info, methods=["GET"])
        app.add_api_route("/metrics", self._handle_metrics, methods=["GET"])
        app.add_api_route("/command", self._handle_command, methods=["POST"])
        app.add_api_route("/synthesize", self._handle_synthesize, methods=["POST"])
        app.add_api_route("/extract_voice", self._handle_extract_voice, methods=["POST"])

        return app

    async def _handle_health(self) -> Dict:
        """健康检查"""
        return HealthCheck(
            status="healthy" if self._status == WorkerStatus.READY else "degraded",
            version="3.0.0",
            uptime_seconds=time.time() - self._start_time,
            components={
                "model": {
                    "status": "loaded" if self._model_loaded else "not_loaded",
                    "engine": self.engine_type.value,
                }
            },
        ).model_dump()

    async def _handle_info(self) -> Dict:
        """节点信息"""
        return self._get_node_info().model_dump()

    async def _handle_metrics(self) -> Dict:
        """节点指标"""
        return self._get_metrics().model_dump()

    async def _handle_command(self, command: NodeCommand) -> Dict:
        """处理控制命令"""
        cmd = command.command.lower()

        if cmd == "activate" or cmd == "load_model":
            success = await self.activate()
            return {"success": success, "status": self._status.value}

        elif cmd == "standby" or cmd == "unload_model":
            success = await self.standby()
            return {"success": success, "status": self._status.value}

        elif cmd == "stop":
            await self.stop()
            return {"success": True, "status": self._status.value}

        else:
            return {"success": False, "error": f"Unknown command: {cmd}"}

    async def _handle_synthesize(self, request: Request) -> Response:
        """处理合成请求"""
        if not self._model_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded")

        self._current_concurrent += 1
        start_time = time.time()

        try:
            data = await request.json()
            req = SynthesizeRequest(**data)

            audio_data = await self.synthesize(
                text=req.text,
                voice_id=req.voice_id,
                language=req.language,
                speed=req.speed,
                pitch=req.pitch,
            )

            self._request_count += 1
            elapsed = (time.time() - start_time) * 1000
            self._total_response_time += elapsed

            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={
                    "X-Response-Time": f"{elapsed:.2f}ms",
                    "X-Node-Id": self.node_id,
                },
            )

        except Exception as e:
            self._error_count += 1
            logger.error(f"Synthesize error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            self._current_concurrent -= 1

    async def _handle_extract_voice(self, request: Request) -> Dict:
        """处理音色提取请求"""
        if not self._model_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded")

        self._current_concurrent += 1

        try:
            # 解析 multipart 表单
            form = await request.form()
            audio_file = form.get("audio")
            voice_id = form.get("voice_id", "")
            voice_name = form.get("voice_name", "")

            if not audio_file:
                raise HTTPException(status_code=400, detail="Missing audio file")

            audio_data = await audio_file.read()

            voice_info = await self.extract_voice(
                audio_data=audio_data,
                voice_id=voice_id or str(uuid.uuid4())[:8],
                voice_name=voice_name,
            )

            self._request_count += 1
            return ExtractVoiceResponse(
                success=True,
                voice_id=voice_info.voice_id,
                voice_name=voice_info.name,
                engine=self.engine_type.value,
            ).model_dump()

        except Exception as e:
            self._error_count += 1
            logger.error(f"Extract voice error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            self._current_concurrent -= 1

    def run(self, **kwargs):
        """运行节点"""
        import uvicorn

        # 创建 uvicorn 服务器配置
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            **kwargs
        )
        server = uvicorn.Server(config)

        # 设置信号处理器以支持优雅关闭
        self._setup_signal_handlers(server)

        # 运行服务器
        server.run()

    def _setup_signal_handlers(self, server):
        """设置信号处理器"""
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)

        def signal_handler(signum, frame):
            logger.info(f"Worker {self.node_id} received signal {signum}, initiating shutdown...")
            server.should_exit = True

            # 如果有原始处理器，也调用它（用于链式处理）
            if signum == signal.SIGINT and callable(original_sigint):
                try:
                    original_sigint(signum, frame)
                except (TypeError, SystemExit):
                    # TypeError: original handler may not be callable in all cases
                    # SystemExit: original handler may raise SystemExit
                    pass
                except Exception as e:
                    logger.debug(f"Error calling original SIGINT handler: {e}")
            elif signum == signal.SIGTERM and callable(original_sigterm):
                try:
                    original_sigterm(signum, frame)
                except (TypeError, SystemExit):
                    pass
                except Exception as e:
                    logger.debug(f"Error calling original SIGTERM handler: {e}")

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
