"""
网关服务

提供统一的 API 入口、请求路由、Web 页面等功能。
"""

import os
import time
import logging
import asyncio
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File, Form, WebSocket
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

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
    BatchSynthesizeRequest,
    BatchSynthesizeResponse,
    Announcement,
    AnnouncementType,
    SystemStatus,
    SystemConfig,
    HealthCheck,
)
from ..common.exceptions import (
    VoiceCloneError,
    NoAvailableNodeError,
    NodeNotFoundError,
    RateLimitExceededError,
)
from .registry import ServiceRegistry
from .limiter import RateLimiter
from .websocket import ConnectionManager, StatusBroadcaster, websocket_endpoint

logger = logging.getLogger(__name__)

# 模板目录
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "static")


class GatewayApp:
    """网关应用"""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        config: Optional[SystemConfig] = None,
    ):
        """
        初始化网关

        Args:
            host: 监听地址
            port: 监听端口
            config: 系统配置
        """
        self.host = host
        self.port = port
        self.config = config or SystemConfig()

        # 服务注册中心
        self.registry = ServiceRegistry(
            heartbeat_interval=self.config.heartbeat_interval,
            dead_threshold=self.config.dead_threshold,
        )

        # 限流器
        self.limiter = RateLimiter(
            global_rpm=self.config.global_rpm,
            ip_rpm=self.config.ip_rpm,
            concurrent_limit=self.config.concurrent_limit,
        )

        # WebSocket 连接管理
        self.ws_manager = ConnectionManager()
        self.ws_broadcaster = StatusBroadcaster(
            manager=self.ws_manager,
            registry=self.registry,
            interval=self.config.ws_broadcast_interval,
        )

        # 公告列表
        self._announcements: List[Announcement] = []

        # 启动时间
        self._start_time = time.time()

        # FastAPI 应用
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """创建 FastAPI 应用"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self.registry.start_health_check()
            await self.ws_broadcaster.start()
            logger.info(f"Gateway started on {self.host}:{self.port}")
            yield
            await self.ws_broadcaster.stop()
            await self.registry.stop_health_check()
            logger.info("Gateway stopped")

        app = FastAPI(
            title="Voice Clone TTS Gateway",
            version="3.2.3",
            description="企业级语音克隆 TTS 服务网关",
            lifespan=lifespan,
        )

        # 静态文件和模板
        if os.path.exists(STATIC_DIR):
            app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

        # 中间件
        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            # 跳过静态文件和页面请求
            if request.url.path.startswith(("/static", "/status", "/admin", "/playground")):
                return await call_next(request)

            # 跳过健康检查
            if request.url.path in ("/health", "/", "/api/health"):
                return await call_next(request)

            client_ip = request.client.host if request.client else "unknown"
            endpoint = request.url.path

            try:
                await self.limiter.check(client_ip, endpoint)
                await self.limiter.acquire_concurrent()
                try:
                    response = await call_next(request)
                    return response
                finally:
                    await self.limiter.release_concurrent()
            except RateLimitExceededError as e:
                return JSONResponse(
                    status_code=429,
                    content={"error": str(e), "code": "RATE_LIMIT_EXCEEDED"},
                )

        # 异常处理
        @app.exception_handler(VoiceCloneError)
        async def voice_clone_error_handler(request: Request, exc: VoiceCloneError):
            return JSONResponse(
                status_code=400,
                content={"error": exc.message, "code": exc.code},
            )

        # ==================== 页面路由 ====================

        @app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """首页 - 重定向到状态页"""
            return HTMLResponse(
                content='<meta http-equiv="refresh" content="0; url=/status">'
            )

        @app.get("/status", response_class=HTMLResponse)
        async def status_page(request: Request):
            """状态监控页面"""
            return self._render_status_page()

        @app.get("/admin", response_class=HTMLResponse)
        async def admin_page(request: Request):
            """管理控制页面"""
            return self._render_admin_page()

        @app.get("/playground", response_class=HTMLResponse)
        async def playground_page(request: Request):
            """API 测试页面"""
            return self._render_playground_page()

        # ==================== API 路由 ====================

        # 健康检查
        @app.get("/health")
        @app.get("/api/health")
        async def health_check():
            """健康检查"""
            stats = self.registry.get_stats()
            status = "healthy"
            if stats["ready_nodes"] == 0:
                status = "degraded" if stats["online_nodes"] > 0 else "unhealthy"

            return HealthCheck(
                status=status,
                version=app.version,  # 从 FastAPI app 读取版本，保持一致
                uptime_seconds=time.time() - self._start_time,
                components={
                    "registry": {
                        "total_nodes": stats["total_nodes"],
                        "online_nodes": stats["online_nodes"],
                        "ready_nodes": stats["ready_nodes"],
                    },
                    "limiter": self.limiter.get_stats(),
                },
            )

        # 系统状态
        @app.get("/api/status")
        async def get_system_status():
            """获取系统状态"""
            stats = self.registry.get_stats()
            nodes = self.registry.get_nodes()

            # 计算总请求数和平均响应时间
            total_requests = sum(n.request_count for n in nodes)
            total_concurrent = sum(n.current_concurrent for n in nodes)

            avg_response_time = 0.0
            active_nodes = [n for n in nodes if n.request_count > 0]
            if active_nodes:
                avg_response_time = sum(
                    n.avg_response_time for n in active_nodes
                ) / len(active_nodes)

            return SystemStatus(
                online_nodes=stats["online_nodes"],
                total_nodes=stats["total_nodes"],
                total_requests=total_requests,
                current_concurrent=total_concurrent,
                avg_response_time_ms=avg_response_time,
                engines=stats["engines"],
                announcements=[a for a in self._announcements if not a.is_expired],
            )

        # ==================== 节点管理 API ====================

        @app.post("/api/nodes/register")
        async def register_node(node: NodeInfo):
            """注册节点"""
            node_id = self.registry.register(node)
            return {"success": True, "node_id": node_id}

        @app.delete("/api/nodes/{node_id}")
        async def unregister_node(node_id: str):
            """注销节点"""
            success = self.registry.unregister(node_id)
            return {"success": success}

        @app.post("/api/nodes/{node_id}/heartbeat")
        async def node_heartbeat(node_id: str, metrics: NodeMetrics):
            """节点心跳"""
            success = self.registry.heartbeat(node_id, metrics)
            return {"success": success}

        @app.get("/api/nodes")
        async def list_nodes(
            engine: Optional[str] = None,
            status: Optional[str] = None,
        ):
            """获取节点列表"""
            engine_type = EngineType(engine) if engine else None
            status_type = WorkerStatus(status) if status else None

            nodes = self.registry.get_nodes(engine=engine_type, status=status_type)
            return {"nodes": [n.model_dump() for n in nodes]}

        @app.get("/api/nodes/{node_id}")
        async def get_node(node_id: str):
            """获取节点信息"""
            try:
                node = self.registry.get_node(node_id)
                return node.model_dump()
            except NodeNotFoundError:
                raise HTTPException(status_code=404, detail="Node not found")

        @app.post("/api/nodes/{node_id}/command")
        async def send_node_command(node_id: str, command: NodeCommand):
            """向节点发送命令"""
            try:
                success = await self.registry.send_command(node_id, command)
                return {"success": success}
            except NodeNotFoundError:
                raise HTTPException(status_code=404, detail="Node not found")

        # ==================== 业务 API ====================

        @app.post("/api/synthesize")
        async def synthesize(request: SynthesizeRequest):
            """语音合成"""
            try:
                # 选择节点
                engine = request.engine or self.config.default_engine
                node = self.registry.select_node(engine)

                # 转发请求
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"http://{node.address}/synthesize",
                        json=request.model_dump(),
                    )

                    if resp.status_code != 200:
                        return SynthesizeResponse(
                            success=False,
                            message=f"Node error: {resp.text}",
                        )

                    # 返回音频
                    return Response(
                        content=resp.content,
                        media_type="audio/wav",
                        headers={
                            "X-Node-Id": node.node_id,
                            "X-Engine": engine.value,
                        },
                    )

            except NoAvailableNodeError as e:
                return SynthesizeResponse(
                    success=False,
                    message=str(e),
                )
            except Exception as e:
                logger.error(f"Synthesize error: {e}")
                return SynthesizeResponse(
                    success=False,
                    message=str(e),
                )

        @app.post("/api/extract_voice")
        async def extract_voice(
            audio: UploadFile = File(...),
            voice_id: Optional[str] = Form(None),
            voice_name: str = Form(""),
            engine: Optional[str] = Form(None),
        ):
            """提取音色"""
            try:
                # 选择节点
                engine_type = EngineType(engine) if engine else self.config.default_engine
                node = self.registry.select_node(engine_type)

                # 读取音频
                audio_data = await audio.read()

                # 转发请求
                async with httpx.AsyncClient(timeout=120.0) as client:
                    files = {"audio": (audio.filename, audio_data, audio.content_type)}
                    data = {"voice_id": voice_id or "", "voice_name": voice_name}

                    resp = await client.post(
                        f"http://{node.address}/extract_voice",
                        files=files,
                        data=data,
                    )

                    if resp.status_code != 200:
                        return ExtractVoiceResponse(
                            success=False,
                            message=f"Node error: {resp.text}",
                        )

                    result = resp.json()
                    return ExtractVoiceResponse(**result)

            except NoAvailableNodeError as e:
                return ExtractVoiceResponse(
                    success=False,
                    message=str(e),
                )
            except Exception as e:
                logger.error(f"Extract voice error: {e}")
                return ExtractVoiceResponse(
                    success=False,
                    message=str(e),
                )

        @app.post("/api/batch_synthesize")
        async def batch_synthesize(request: BatchSynthesizeRequest):
            """批量合成"""
            results = []
            succeeded = 0
            failed = 0

            for i, text in enumerate(request.texts):
                try:
                    engine = request.engine or self.config.default_engine
                    node = self.registry.select_node(engine)

                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(
                            f"http://{node.address}/synthesize",
                            json={
                                "text": text,
                                "voice_id": request.voice_id,
                                "language": request.language,
                            },
                        )

                        if resp.status_code == 200:
                            results.append({
                                "index": i,
                                "success": True,
                                "size": len(resp.content),
                            })
                            succeeded += 1
                        else:
                            results.append({
                                "index": i,
                                "success": False,
                                "error": resp.text,
                            })
                            failed += 1

                except Exception as e:
                    results.append({
                        "index": i,
                        "success": False,
                        "error": str(e),
                    })
                    failed += 1

            return BatchSynthesizeResponse(
                success=failed == 0,
                message=f"Batch completed: {succeeded}/{len(request.texts)}",
                results=results,
                total=len(request.texts),
                succeeded=succeeded,
                failed=failed,
            )

        # ==================== 公告管理 API ====================

        @app.get("/api/announcements")
        async def list_announcements():
            """获取公告列表"""
            return {"announcements": [
                a.model_dump() for a in self._announcements if not a.is_expired
            ]}

        @app.post("/api/announcements")
        async def create_announcement(announcement: Announcement):
            """创建公告"""
            self._announcements.append(announcement)
            return {"success": True, "id": announcement.id}

        @app.delete("/api/announcements/{announcement_id}")
        async def delete_announcement(announcement_id: str):
            """删除公告"""
            self._announcements = [
                a for a in self._announcements if a.id != announcement_id
            ]
            return {"success": True}

        # ==================== WebSocket 端点 ====================

        @app.websocket("/ws")
        async def ws_status(websocket: WebSocket):
            """WebSocket 实时状态推送"""
            await websocket_endpoint(websocket, self.ws_manager, self.registry)

        return app

    # ==================== 页面渲染 ====================

    def _render_status_page(self) -> str:
        """渲染状态页面"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统状态 - Voice Clone TTS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <style>
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen" x-data="statusApp()" x-init="init()">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-xl font-bold text-gray-900">Voice Clone TTS</span>
                    <span class="ml-2 text-sm text-gray-500">微服务架构</span>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="flex items-center text-sm">
                        <span :class="wsConnected ? 'bg-green-500' : 'bg-red-500'" class="w-2 h-2 rounded-full mr-1"></span>
                        <span :class="wsConnected ? 'text-green-600' : 'text-red-600'" x-text="wsConnected ? '实时' : '离线'"></span>
                    </span>
                    <a href="/status" class="text-blue-600 font-medium">状态</a>
                    <a href="/admin" class="text-gray-600 hover:text-gray-900">管理</a>
                    <a href="/playground" class="text-gray-600 hover:text-gray-900">测试</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <!-- 公告 -->
        <template x-if="announcements.length > 0">
            <div class="mb-6 space-y-2">
                <template x-for="ann in announcements" :key="ann.id">
                    <div :class="{
                        'bg-blue-100 border-blue-500': ann.type === 'info',
                        'bg-yellow-100 border-yellow-500': ann.type === 'warning',
                        'bg-red-100 border-red-500': ann.type === 'error',
                        'bg-purple-100 border-purple-500': ann.type === 'maintenance'
                    }" class="border-l-4 p-4 rounded">
                        <p class="font-medium" x-text="ann.title"></p>
                        <p class="text-sm" x-text="ann.message"></p>
                    </div>
                </template>
            </div>
        </template>

        <!-- 系统概览 -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-white rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">在线节点</div>
                <div class="text-2xl font-bold" x-text="status.online_nodes + '/' + status.total_nodes"></div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">总请求数</div>
                <div class="text-2xl font-bold" x-text="status.total_requests"></div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">当前并发</div>
                <div class="text-2xl font-bold" x-text="status.current_concurrent"></div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">平均响应</div>
                <div class="text-2xl font-bold" x-text="status.avg_response_time_ms.toFixed(1) + 'ms'"></div>
            </div>
        </div>

        <!-- 引擎状态 -->
        <div class="bg-white rounded-lg shadow mb-6">
            <div class="px-4 py-3 border-b">
                <h2 class="text-lg font-medium">引擎状态</h2>
            </div>
            <div class="p-4">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <template x-for="(info, engine) in status.engines" :key="engine">
                        <div class="border rounded-lg p-4">
                            <div class="flex items-center justify-between mb-2">
                                <span class="font-medium uppercase" x-text="engine"></span>
                                <span :class="{
                                    'bg-green-100 text-green-800': info.ready > 0,
                                    'bg-yellow-100 text-yellow-800': info.ready === 0 && info.online > 0,
                                    'bg-red-100 text-red-800': info.online === 0
                                }" class="px-2 py-1 rounded text-xs">
                                    <span x-text="info.ready > 0 ? '就绪' : (info.online > 0 ? '待机' : '离线')"></span>
                                </span>
                            </div>
                            <div class="text-sm text-gray-600">
                                <span x-text="'就绪: ' + info.ready"></span> /
                                <span x-text="'在线: ' + info.online"></span> /
                                <span x-text="'总计: ' + info.total"></span>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </div>

        <!-- 节点列表 -->
        <div class="bg-white rounded-lg shadow">
            <div class="px-4 py-3 border-b flex justify-between items-center">
                <h2 class="text-lg font-medium">节点列表</h2>
                <button @click="refreshNodes()" class="text-blue-600 text-sm hover:underline">刷新</button>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">节点 ID</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">引擎</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">地址</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CPU</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">内存</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">请求数</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">并发</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <template x-for="node in nodes" :key="node.node_id">
                            <tr>
                                <td class="px-4 py-3 text-sm font-mono" x-text="node.node_id"></td>
                                <td class="px-4 py-3 text-sm uppercase" x-text="node.engine_type"></td>
                                <td class="px-4 py-3 text-sm" x-text="node.host + ':' + node.port"></td>
                                <td class="px-4 py-3">
                                    <span :class="{
                                        'bg-green-100 text-green-800': node.status === 'ready',
                                        'bg-yellow-100 text-yellow-800': node.status === 'loading' || node.status === 'standby',
                                        'bg-red-100 text-red-800': node.status === 'error' || node.status === 'offline',
                                        'bg-blue-100 text-blue-800': node.status === 'busy'
                                    }" class="px-2 py-1 rounded text-xs" x-text="node.status"></span>
                                </td>
                                <td class="px-4 py-3 text-sm" x-text="node.cpu_percent.toFixed(1) + '%'"></td>
                                <td class="px-4 py-3 text-sm" x-text="node.memory_percent.toFixed(1) + '%'"></td>
                                <td class="px-4 py-3 text-sm" x-text="node.request_count"></td>
                                <td class="px-4 py-3 text-sm" x-text="node.current_concurrent"></td>
                            </tr>
                        </template>
                        <template x-if="nodes.length === 0">
                            <tr>
                                <td colspan="8" class="px-4 py-8 text-center text-gray-500">暂无节点</td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <script>
    function statusApp() {
        return {
            status: {
                online_nodes: 0,
                total_nodes: 0,
                total_requests: 0,
                current_concurrent: 0,
                avg_response_time_ms: 0,
                engines: {}
            },
            nodes: [],
            announcements: [],
            wsConnected: false,
            ws: null,

            async init() {
                await this.refresh();
                this.connectWebSocket();
                // Fallback polling if WebSocket fails
                setInterval(() => {
                    if (!this.wsConnected) this.refresh();
                }, 5000);
            },

            connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;

                try {
                    this.ws = new WebSocket(wsUrl);

                    this.ws.onopen = () => {
                        console.log('WebSocket connected');
                        this.wsConnected = true;
                    };

                    this.ws.onmessage = (event) => {
                        const msg = JSON.parse(event.data);
                        this.handleWsMessage(msg);
                    };

                    this.ws.onclose = () => {
                        console.log('WebSocket disconnected');
                        this.wsConnected = false;
                        // Reconnect after 3 seconds
                        setTimeout(() => this.connectWebSocket(), 3000);
                    };

                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                    };
                } catch (e) {
                    console.error('Failed to connect WebSocket:', e);
                }
            },

            handleWsMessage(msg) {
                if (msg.type === 'system_status') {
                    this.status = msg.data;
                    this.announcements = msg.data.announcements || [];
                } else if (msg.type === 'node_online' || msg.type === 'node_offline' || msg.type === 'node_status_changed') {
                    // Refresh nodes on node events
                    this.refreshNodes();
                } else if (msg.type === 'ping') {
                    // Send pong response
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send(JSON.stringify({type: 'pong'}));
                    }
                }
            },

            async refresh() {
                await Promise.all([
                    this.refreshStatus(),
                    this.refreshNodes()
                ]);
            },

            async refreshStatus() {
                try {
                    const resp = await fetch('/api/status');
                    const data = await resp.json();
                    this.status = data;
                    this.announcements = data.announcements || [];
                } catch (e) {
                    console.error('Failed to fetch status:', e);
                }
            },

            async refreshNodes() {
                try {
                    const resp = await fetch('/api/nodes');
                    const data = await resp.json();
                    this.nodes = data.nodes || [];
                } catch (e) {
                    console.error('Failed to fetch nodes:', e);
                }
            }
        }
    }
    </script>
</body>
</html>"""

    def _render_admin_page(self) -> str:
        """渲染管理页面"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理控制 - Voice Clone TTS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
</head>
<body class="bg-gray-100 min-h-screen" x-data="adminApp()" x-init="init()">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-xl font-bold text-gray-900">Voice Clone TTS</span>
                    <span class="ml-2 text-sm text-gray-500">微服务架构</span>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/status" class="text-gray-600 hover:text-gray-900">状态</a>
                    <a href="/admin" class="text-blue-600 font-medium">管理</a>
                    <a href="/playground" class="text-gray-600 hover:text-gray-900">测试</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <!-- 节点控制 -->
        <div class="bg-white rounded-lg shadow mb-6">
            <div class="px-4 py-3 border-b">
                <h2 class="text-lg font-medium">节点控制</h2>
            </div>
            <div class="p-4">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">节点</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">引擎</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">模型</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        <template x-for="node in nodes" :key="node.node_id">
                            <tr>
                                <td class="px-4 py-3 text-sm font-mono" x-text="node.node_id"></td>
                                <td class="px-4 py-3 text-sm uppercase" x-text="node.engine_type"></td>
                                <td class="px-4 py-3">
                                    <span :class="{
                                        'bg-green-100 text-green-800': node.status === 'ready',
                                        'bg-yellow-100 text-yellow-800': node.status === 'standby',
                                        'bg-blue-100 text-blue-800': node.status === 'loading',
                                        'bg-red-100 text-red-800': node.status === 'error' || node.status === 'offline'
                                    }" class="px-2 py-1 rounded text-xs" x-text="node.status"></span>
                                </td>
                                <td class="px-4 py-3 text-sm" x-text="node.model_loaded ? '已加载' : '未加载'"></td>
                                <td class="px-4 py-3 space-x-2">
                                    <button @click="sendCommand(node.node_id, 'activate')"
                                        :disabled="node.model_loaded || node.status === 'loading'"
                                        :class="{'opacity-50 cursor-not-allowed': node.model_loaded || node.status === 'loading'}"
                                        class="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600">
                                        激活
                                    </button>
                                    <button @click="sendCommand(node.node_id, 'standby')"
                                        :disabled="!node.model_loaded"
                                        :class="{'opacity-50 cursor-not-allowed': !node.model_loaded}"
                                        class="px-3 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600">
                                        待机
                                    </button>
                                    <button @click="removeNode(node.node_id)"
                                        class="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">
                                        移除
                                    </button>
                                </td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 公告管理 -->
        <div class="bg-white rounded-lg shadow">
            <div class="px-4 py-3 border-b flex justify-between items-center">
                <h2 class="text-lg font-medium">公告管理</h2>
                <button @click="showAddAnnouncement = true" class="px-3 py-1 bg-blue-500 text-white rounded text-sm">
                    添加公告
                </button>
            </div>
            <div class="p-4">
                <template x-if="announcements.length === 0">
                    <div class="text-center text-gray-500 py-4">暂无公告</div>
                </template>
                <div class="space-y-2">
                    <template x-for="ann in announcements" :key="ann.id">
                        <div class="flex items-center justify-between p-3 border rounded">
                            <div>
                                <span :class="{
                                    'text-blue-600': ann.type === 'info',
                                    'text-yellow-600': ann.type === 'warning',
                                    'text-red-600': ann.type === 'error'
                                }" class="font-medium" x-text="'[' + ann.type + '] ' + ann.title"></span>
                                <p class="text-sm text-gray-600" x-text="ann.message"></p>
                            </div>
                            <button @click="deleteAnnouncement(ann.id)" class="text-red-500 hover:text-red-700">
                                删除
                            </button>
                        </div>
                    </template>
                </div>
            </div>
        </div>

        <!-- 添加公告弹窗 -->
        <div x-show="showAddAnnouncement" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div class="bg-white rounded-lg p-6 w-96" @click.outside="showAddAnnouncement = false">
                <h3 class="text-lg font-medium mb-4">添加公告</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">类型</label>
                        <select x-model="newAnnouncement.type" class="mt-1 block w-full rounded border-gray-300 shadow-sm">
                            <option value="info">信息</option>
                            <option value="warning">警告</option>
                            <option value="error">错误</option>
                            <option value="maintenance">维护</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">标题</label>
                        <input type="text" x-model="newAnnouncement.title" class="mt-1 block w-full rounded border-gray-300 shadow-sm">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">内容</label>
                        <textarea x-model="newAnnouncement.message" rows="3" class="mt-1 block w-full rounded border-gray-300 shadow-sm"></textarea>
                    </div>
                    <div class="flex justify-end space-x-2">
                        <button @click="showAddAnnouncement = false" class="px-4 py-2 border rounded">取消</button>
                        <button @click="addAnnouncement()" class="px-4 py-2 bg-blue-500 text-white rounded">添加</button>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
    function adminApp() {
        return {
            nodes: [],
            announcements: [],
            showAddAnnouncement: false,
            newAnnouncement: { type: 'info', title: '', message: '' },

            async init() {
                await this.refresh();
                setInterval(() => this.refresh(), 5000);
            },

            async refresh() {
                const [nodesResp, annResp] = await Promise.all([
                    fetch('/api/nodes'),
                    fetch('/api/announcements')
                ]);
                this.nodes = (await nodesResp.json()).nodes || [];
                this.announcements = (await annResp.json()).announcements || [];
            },

            async sendCommand(nodeId, command) {
                await fetch(`/api/nodes/${nodeId}/command`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command })
                });
                await this.refresh();
            },

            async removeNode(nodeId) {
                if (confirm('确定要移除该节点吗？')) {
                    await fetch(`/api/nodes/${nodeId}`, { method: 'DELETE' });
                    await this.refresh();
                }
            },

            async addAnnouncement() {
                await fetch('/api/announcements', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.newAnnouncement)
                });
                this.showAddAnnouncement = false;
                this.newAnnouncement = { type: 'info', title: '', message: '' };
                await this.refresh();
            },

            async deleteAnnouncement(id) {
                await fetch(`/api/announcements/${id}`, { method: 'DELETE' });
                await this.refresh();
            }
        }
    }
    </script>
</body>
</html>"""

    def _render_playground_page(self) -> str:
        """渲染 API 测试页面"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API 测试 - Voice Clone TTS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
</head>
<body class="bg-gray-100 min-h-screen" x-data="playgroundApp()">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-xl font-bold text-gray-900">Voice Clone TTS</span>
                    <span class="ml-2 text-sm text-gray-500">微服务架构</span>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/status" class="text-gray-600 hover:text-gray-900">状态</a>
                    <a href="/admin" class="text-gray-600 hover:text-gray-900">管理</a>
                    <a href="/playground" class="text-blue-600 font-medium">测试</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 语音合成测试 -->
            <div class="bg-white rounded-lg shadow">
                <div class="px-4 py-3 border-b">
                    <h2 class="text-lg font-medium">语音合成测试</h2>
                </div>
                <div class="p-4 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">文本内容</label>
                        <textarea x-model="synthesize.text" rows="3" placeholder="输入要合成的文本..."
                            class="mt-1 block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"></textarea>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">音色 ID</label>
                            <input type="text" x-model="synthesize.voice_id" placeholder="voice_id"
                                class="mt-1 block w-full rounded border-gray-300 shadow-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">引擎</label>
                            <select x-model="synthesize.engine" class="mt-1 block w-full rounded border-gray-300 shadow-sm">
                                <option value="">自动选择</option>
                                <option value="xtts">XTTS</option>
                                <option value="openvoice">OpenVoice</option>
                                <option value="gpt-sovits">GPT-SoVITS</option>
                            </select>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">语言</label>
                            <select x-model="synthesize.language" class="mt-1 block w-full rounded border-gray-300 shadow-sm">
                                <option value="zh">中文</option>
                                <option value="en">英语</option>
                                <option value="ja">日语</option>
                                <option value="ko">韩语</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">语速</label>
                            <input type="range" x-model="synthesize.speed" min="0.5" max="2" step="0.1"
                                class="mt-1 block w-full">
                            <span class="text-sm text-gray-500" x-text="synthesize.speed + 'x'"></span>
                        </div>
                    </div>
                    <button @click="doSynthesize()" :disabled="synthesizing"
                        class="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50">
                        <span x-show="!synthesizing">开始合成</span>
                        <span x-show="synthesizing">合成中...</span>
                    </button>
                    <div x-show="synthesizeResult" class="mt-4">
                        <template x-if="synthesizeResult.success">
                            <div>
                                <audio :src="synthesizeResult.audioUrl" controls class="w-full"></audio>
                                <p class="text-sm text-gray-500 mt-2" x-text="'响应时间: ' + synthesizeResult.time + 'ms'"></p>
                            </div>
                        </template>
                        <template x-if="!synthesizeResult.success">
                            <div class="text-red-500" x-text="synthesizeResult.error"></div>
                        </template>
                    </div>
                </div>
            </div>

            <!-- 音色提取测试 -->
            <div class="bg-white rounded-lg shadow">
                <div class="px-4 py-3 border-b">
                    <h2 class="text-lg font-medium">音色提取测试</h2>
                </div>
                <div class="p-4 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">参考音频</label>
                        <input type="file" @change="handleAudioFile($event)" accept="audio/*"
                            class="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">音色 ID (可选)</label>
                            <input type="text" x-model="extract.voice_id" placeholder="自动生成"
                                class="mt-1 block w-full rounded border-gray-300 shadow-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">音色名称</label>
                            <input type="text" x-model="extract.voice_name" placeholder="我的音色"
                                class="mt-1 block w-full rounded border-gray-300 shadow-sm">
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">引擎</label>
                        <select x-model="extract.engine" class="mt-1 block w-full rounded border-gray-300 shadow-sm">
                            <option value="">自动选择</option>
                            <option value="xtts">XTTS</option>
                            <option value="openvoice">OpenVoice</option>
                            <option value="gpt-sovits">GPT-SoVITS</option>
                        </select>
                    </div>
                    <button @click="doExtract()" :disabled="extracting || !extract.audioFile"
                        class="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50">
                        <span x-show="!extracting">提取音色</span>
                        <span x-show="extracting">提取中...</span>
                    </button>
                    <div x-show="extractResult" class="mt-4 p-3 rounded" :class="extractResult.success ? 'bg-green-50' : 'bg-red-50'">
                        <template x-if="extractResult.success">
                            <div>
                                <p class="text-green-800">音色提取成功!</p>
                                <p class="text-sm text-gray-600">Voice ID: <code class="bg-gray-100 px-1 rounded" x-text="extractResult.voice_id"></code></p>
                            </div>
                        </template>
                        <template x-if="!extractResult.success">
                            <p class="text-red-800" x-text="extractResult.error"></p>
                        </template>
                    </div>
                </div>
            </div>
        </div>

        <!-- API 文档 -->
        <div class="bg-white rounded-lg shadow mt-6">
            <div class="px-4 py-3 border-b">
                <h2 class="text-lg font-medium">API 文档</h2>
            </div>
            <div class="p-4">
                <div class="space-y-4">
                    <div class="border rounded p-4">
                        <div class="flex items-center mb-2">
                            <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-mono">POST</span>
                            <span class="ml-2 font-mono text-sm">/api/synthesize</span>
                        </div>
                        <p class="text-sm text-gray-600">语音合成接口，返回 audio/wav 格式音频</p>
                        <pre class="mt-2 bg-gray-50 p-2 rounded text-xs overflow-x-auto">{
  "text": "要合成的文本",
  "voice_id": "音色ID",
  "engine": "xtts|openvoice|gpt-sovits",
  "language": "zh|en|ja|ko",
  "speed": 1.0
}</pre>
                    </div>
                    <div class="border rounded p-4">
                        <div class="flex items-center mb-2">
                            <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-mono">POST</span>
                            <span class="ml-2 font-mono text-sm">/api/extract_voice</span>
                        </div>
                        <p class="text-sm text-gray-600">音色提取接口，上传音频文件提取音色特征</p>
                        <pre class="mt-2 bg-gray-50 p-2 rounded text-xs overflow-x-auto">multipart/form-data:
- audio: 音频文件
- voice_id: 音色ID (可选)
- voice_name: 音色名称
- engine: 引擎类型</pre>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
    function playgroundApp() {
        return {
            synthesize: {
                text: '你好，这是一个语音克隆测试。',
                voice_id: 'default',
                engine: '',
                language: 'zh',
                speed: 1.0
            },
            synthesizing: false,
            synthesizeResult: null,

            extract: {
                audioFile: null,
                voice_id: '',
                voice_name: '',
                engine: ''
            },
            extracting: false,
            extractResult: null,

            async doSynthesize() {
                this.synthesizing = true;
                this.synthesizeResult = null;
                const startTime = Date.now();

                try {
                    const resp = await fetch('/api/synthesize', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.synthesize)
                    });

                    if (resp.ok && resp.headers.get('content-type')?.includes('audio')) {
                        const blob = await resp.blob();
                        this.synthesizeResult = {
                            success: true,
                            audioUrl: URL.createObjectURL(blob),
                            time: Date.now() - startTime
                        };
                    } else {
                        const data = await resp.json();
                        this.synthesizeResult = {
                            success: false,
                            error: data.message || data.error || '合成失败'
                        };
                    }
                } catch (e) {
                    this.synthesizeResult = { success: false, error: e.message };
                }

                this.synthesizing = false;
            },

            handleAudioFile(event) {
                this.extract.audioFile = event.target.files[0];
            },

            async doExtract() {
                if (!this.extract.audioFile) return;

                this.extracting = true;
                this.extractResult = null;

                try {
                    const formData = new FormData();
                    formData.append('audio', this.extract.audioFile);
                    if (this.extract.voice_id) formData.append('voice_id', this.extract.voice_id);
                    if (this.extract.voice_name) formData.append('voice_name', this.extract.voice_name);
                    if (this.extract.engine) formData.append('engine', this.extract.engine);

                    const resp = await fetch('/api/extract_voice', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await resp.json();
                    if (data.success) {
                        this.extractResult = {
                            success: true,
                            voice_id: data.voice_id
                        };
                    } else {
                        this.extractResult = {
                            success: false,
                            error: data.message || '提取失败'
                        };
                    }
                } catch (e) {
                    this.extractResult = { success: false, error: e.message };
                }

                this.extracting = false;
            }
        }
    }
    </script>
</body>
</html>"""

    def run(self, **kwargs):
        """运行网关"""
        import uvicorn
        uvicorn.run(self.app, host=self.host, port=self.port, **kwargs)


def create_gateway(
    host: str = "0.0.0.0",
    port: int = 8080,
    config: Optional[SystemConfig] = None,
) -> GatewayApp:
    """创建网关实例"""
    return GatewayApp(host=host, port=port, config=config)
