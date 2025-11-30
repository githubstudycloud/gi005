"""
WebSocket 实时状态推送

提供实时状态更新功能:
- 节点状态变更通知
- 系统指标实时推送
- 公告实时广播
"""

import json
import asyncio
import logging
from typing import Set, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型"""
    # 节点事件
    NODE_ONLINE = "node_online"
    NODE_OFFLINE = "node_offline"
    NODE_STATUS_CHANGED = "node_status_changed"
    NODE_METRICS = "node_metrics"

    # 系统事件
    SYSTEM_STATUS = "system_status"
    ANNOUNCEMENT = "announcement"

    # 请求事件
    REQUEST_START = "request_start"
    REQUEST_COMPLETE = "request_complete"
    REQUEST_ERROR = "request_error"


@dataclass
class WebSocketEvent:
    """WebSocket 事件"""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: float = 0

    def __post_init__(self):
        import time
        if self.timestamp == 0:
            self.timestamp = time.time()

    def to_json(self) -> str:
        return json.dumps({
            "type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp,
        }, ensure_ascii=False)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected: {len(self.active_connections)} active")

    async def disconnect(self, websocket: WebSocket):
        """断开连接"""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected: {len(self.active_connections)} active")

    async def broadcast(self, event: WebSocketEvent):
        """广播事件到所有连接"""
        if not self.active_connections:
            return

        message = event.to_json()
        disconnected = set()

        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.debug(f"Failed to send to connection: {e}")
                    disconnected.add(connection)

            # 移除断开的连接
            self.active_connections -= disconnected

    async def send_personal(self, websocket: WebSocket, event: WebSocketEvent):
        """发送事件到特定连接"""
        try:
            await websocket.send_text(event.to_json())
        except Exception as e:
            logger.debug(f"Failed to send personal message: {e}")

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


class StatusBroadcaster:
    """状态广播器"""

    def __init__(
        self,
        manager: ConnectionManager,
        registry: Any,  # ServiceRegistry
        interval: float = 2.0,
    ):
        self.manager = manager
        self.registry = registry
        self.interval = interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """启动广播"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._broadcast_loop())
        logger.info("Status broadcaster started")

    async def stop(self):
        """停止广播"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Status broadcaster stopped")

    async def _broadcast_loop(self):
        """广播循环"""
        while self._running:
            try:
                await self._broadcast_status()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                await asyncio.sleep(self.interval)

    async def _broadcast_status(self):
        """广播系统状态"""
        if self.manager.connection_count == 0:
            return

        # 获取系统状态
        status = self.registry.get_system_status()

        # 广播
        event = WebSocketEvent(
            event_type=EventType.SYSTEM_STATUS,
            data=status,
        )
        await self.manager.broadcast(event)

    async def notify_node_online(self, node_id: str, node_info: Dict):
        """通知节点上线"""
        event = WebSocketEvent(
            event_type=EventType.NODE_ONLINE,
            data={"node_id": node_id, **node_info},
        )
        await self.manager.broadcast(event)

    async def notify_node_offline(self, node_id: str):
        """通知节点下线"""
        event = WebSocketEvent(
            event_type=EventType.NODE_OFFLINE,
            data={"node_id": node_id},
        )
        await self.manager.broadcast(event)

    async def notify_node_status_changed(
        self,
        node_id: str,
        old_status: str,
        new_status: str,
    ):
        """通知节点状态变更"""
        event = WebSocketEvent(
            event_type=EventType.NODE_STATUS_CHANGED,
            data={
                "node_id": node_id,
                "old_status": old_status,
                "new_status": new_status,
            },
        )
        await self.manager.broadcast(event)

    async def notify_announcement(self, announcement: Dict):
        """通知新公告"""
        event = WebSocketEvent(
            event_type=EventType.ANNOUNCEMENT,
            data=announcement,
        )
        await self.manager.broadcast(event)


async def websocket_endpoint(
    websocket: WebSocket,
    manager: ConnectionManager,
    registry: Any,
):
    """
    WebSocket 端点处理

    客户端连接后会收到:
    - 初始状态推送
    - 定期状态更新
    - 节点变更通知
    """
    await manager.connect(websocket)

    try:
        # 发送初始状态
        status = registry.get_system_status()
        await manager.send_personal(
            websocket,
            WebSocketEvent(EventType.SYSTEM_STATUS, status),
        )

        # 保持连接并处理消息
        while True:
            try:
                # 等待客户端消息（可用于心跳）
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,
                )

                # 处理客户端请求
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif msg.get("type") == "get_status":
                        status = registry.get_system_status()
                        await manager.send_personal(
                            websocket,
                            WebSocketEvent(EventType.SYSTEM_STATUS, status),
                        )
                except json.JSONDecodeError:
                    logger.debug(f"Invalid JSON received from WebSocket client")

            except asyncio.TimeoutError:
                # 发送心跳
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except (ConnectionError, RuntimeError) as e:
                    logger.debug(f"WebSocket heartbeat failed, closing connection: {e}")
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)
