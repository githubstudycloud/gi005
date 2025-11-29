"""
服务注册中心

提供节点注册、发现、健康检查和负载均衡功能。
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Callable
from collections import defaultdict
import httpx

from ..common.models import (
    NodeInfo,
    NodeMetrics,
    WorkerStatus,
    EngineType,
    NodeCommand,
)
from ..common.exceptions import (
    NodeNotFoundError,
    NoAvailableNodeError,
)

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """服务注册中心"""

    def __init__(
        self,
        heartbeat_interval: int = 10,
        dead_threshold: int = 30,
    ):
        """
        初始化服务注册中心

        Args:
            heartbeat_interval: 心跳间隔（秒）
            dead_threshold: 节点死亡阈值（秒）
        """
        self.heartbeat_interval = heartbeat_interval
        self.dead_threshold = dead_threshold

        # 节点存储: node_id -> NodeInfo
        self._nodes: Dict[str, NodeInfo] = {}

        # 引擎索引: engine_type -> [node_id, ...]
        self._engine_index: Dict[EngineType, List[str]] = defaultdict(list)

        # 负载均衡计数器（轮询）
        self._round_robin_counters: Dict[EngineType, int] = defaultdict(int)

        # 事件回调
        self._on_node_online: Optional[Callable] = None
        self._on_node_offline: Optional[Callable] = None
        self._on_node_status_change: Optional[Callable] = None

        # 健康检查任务
        self._health_check_task: Optional[asyncio.Task] = None

    # ===================== 节点注册 =====================

    def register(self, node: NodeInfo) -> str:
        """
        注册节点

        Args:
            node: 节点信息

        Returns:
            节点 ID
        """
        node_id = node.node_id
        is_new = node_id not in self._nodes

        # 更新节点信息
        node.registered_at = time.time()
        node.last_heartbeat = time.time()
        self._nodes[node_id] = node

        # 更新引擎索引
        engine = node.engine_type
        if node_id not in self._engine_index[engine]:
            self._engine_index[engine].append(node_id)

        if is_new:
            logger.info(f"Node registered: {node_id} ({engine.value}) at {node.address}")
            if self._on_node_online:
                self._on_node_online(node)
        else:
            logger.debug(f"Node re-registered: {node_id}")

        return node_id

    def unregister(self, node_id: str) -> bool:
        """
        注销节点

        Args:
            node_id: 节点 ID

        Returns:
            是否成功注销
        """
        if node_id not in self._nodes:
            return False

        node = self._nodes.pop(node_id)

        # 从引擎索引中移除
        engine = node.engine_type
        if node_id in self._engine_index[engine]:
            self._engine_index[engine].remove(node_id)

        logger.info(f"Node unregistered: {node_id}")
        if self._on_node_offline:
            self._on_node_offline(node)

        return True

    # ===================== 心跳与健康检查 =====================

    def heartbeat(self, node_id: str, metrics: Optional[NodeMetrics] = None) -> bool:
        """
        节点心跳

        Args:
            node_id: 节点 ID
            metrics: 节点指标（可选）

        Returns:
            是否成功
        """
        if node_id not in self._nodes:
            return False

        node = self._nodes[node_id]
        node.last_heartbeat = time.time()

        # 更新指标
        if metrics:
            node.cpu_percent = metrics.cpu_percent
            node.memory_percent = metrics.memory_percent
            node.gpu_percent = metrics.gpu_percent
            node.gpu_memory_percent = metrics.gpu_memory_percent
            node.current_concurrent = metrics.current_concurrent
            node.request_count = metrics.request_count
            node.error_count = metrics.error_count
            node.avg_response_time = metrics.avg_response_time_ms

            # 同步状态
            if metrics.status != node.status:
                old_status = node.status
                node.status = metrics.status
                if self._on_node_status_change:
                    self._on_node_status_change(node, old_status, metrics.status)

        return True

    def update_status(self, node_id: str, status: WorkerStatus) -> bool:
        """
        更新节点状态

        Args:
            node_id: 节点 ID
            status: 新状态

        Returns:
            是否成功
        """
        if node_id not in self._nodes:
            return False

        node = self._nodes[node_id]
        old_status = node.status
        node.status = status
        node.last_heartbeat = time.time()

        if old_status != status:
            logger.info(f"Node {node_id} status: {old_status.value} -> {status.value}")
            if self._on_node_status_change:
                self._on_node_status_change(node, old_status, status)

        return True

    async def start_health_check(self):
        """启动健康检查任务"""
        if self._health_check_task is not None:
            return

        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Health check task started")

    async def stop_health_check(self):
        """停止健康检查任务"""
        if self._health_check_task is None:
            return

        self._health_check_task.cancel()
        try:
            await self._health_check_task
        except asyncio.CancelledError:
            pass
        self._health_check_task = None
        logger.info("Health check task stopped")

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            await self._check_nodes_health()

    async def _check_nodes_health(self):
        """检查所有节点健康状态"""
        now = time.time()
        dead_nodes = []

        for node_id, node in list(self._nodes.items()):
            elapsed = now - node.last_heartbeat

            if elapsed > self.dead_threshold:
                # 节点超时，标记为离线
                if node.status != WorkerStatus.OFFLINE:
                    logger.warning(
                        f"Node {node_id} marked offline (no heartbeat for {elapsed:.1f}s)"
                    )
                    node.status = WorkerStatus.OFFLINE
                    if self._on_node_offline:
                        self._on_node_offline(node)

            # 可选：主动探测节点
            # await self._probe_node(node)

    async def _probe_node(self, node: NodeInfo) -> bool:
        """
        主动探测节点健康状态

        Args:
            node: 节点信息

        Returns:
            节点是否健康
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"http://{node.address}/health")
                if resp.status_code == 200:
                    return True
        except Exception as e:
            logger.debug(f"Failed to probe node {node.node_id}: {e}")
        return False

    # ===================== 节点发现与负载均衡 =====================

    def get_node(self, node_id: str) -> NodeInfo:
        """
        获取节点信息

        Args:
            node_id: 节点 ID

        Returns:
            节点信息

        Raises:
            NodeNotFoundError: 节点不存在
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        return self._nodes[node_id]

    def get_nodes(
        self,
        engine: Optional[EngineType] = None,
        status: Optional[WorkerStatus] = None,
        available_only: bool = False,
    ) -> List[NodeInfo]:
        """
        获取节点列表

        Args:
            engine: 筛选引擎类型
            status: 筛选状态
            available_only: 只返回可用节点

        Returns:
            节点列表
        """
        nodes = list(self._nodes.values())

        if engine:
            nodes = [n for n in nodes if n.engine_type == engine]

        if status:
            nodes = [n for n in nodes if n.status == status]

        if available_only:
            nodes = [n for n in nodes if n.is_available]

        return nodes

    def select_node(
        self,
        engine: EngineType,
        strategy: str = "round_robin",
    ) -> NodeInfo:
        """
        选择一个可用节点（负载均衡）

        Args:
            engine: 引擎类型
            strategy: 负载均衡策略 (round_robin, least_load, random)

        Returns:
            选中的节点

        Raises:
            NoAvailableNodeError: 无可用节点
        """
        available = self.get_nodes(engine=engine, available_only=True)

        if not available:
            raise NoAvailableNodeError(engine.value)

        if strategy == "round_robin":
            # 轮询
            counter = self._round_robin_counters[engine]
            node = available[counter % len(available)]
            self._round_robin_counters[engine] = (counter + 1) % len(available)
            return node

        elif strategy == "least_load":
            # 最小负载（按当前并发数）
            return min(available, key=lambda n: n.current_concurrent)

        elif strategy == "random":
            # 随机
            import random
            return random.choice(available)

        else:
            # 默认轮询
            return available[0]

    # ===================== 节点控制 =====================

    async def send_command(self, node_id: str, command: NodeCommand) -> bool:
        """
        向节点发送控制命令

        Args:
            node_id: 节点 ID
            command: 控制命令

        Returns:
            是否成功
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)

        node = self._nodes[node_id]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"http://{node.address}/command",
                    json=command.model_dump(),
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send command to {node_id}: {e}")
            return False

    # ===================== 统计与状态 =====================

    def get_stats(self) -> Dict:
        """获取注册中心统计信息"""
        total = len(self._nodes)
        online = len([n for n in self._nodes.values() if n.status != WorkerStatus.OFFLINE])
        ready = len([n for n in self._nodes.values() if n.is_available])

        # 各引擎统计
        engines = {}
        for engine in EngineType:
            nodes = self.get_nodes(engine=engine)
            engines[engine.value] = {
                "total": len(nodes),
                "online": len([n for n in nodes if n.status != WorkerStatus.OFFLINE]),
                "ready": len([n for n in nodes if n.is_available]),
            }

        return {
            "total_nodes": total,
            "online_nodes": online,
            "ready_nodes": ready,
            "engines": engines,
        }

    def get_system_status(self) -> Dict:
        """
        获取完整系统状态（用于 WebSocket 广播）

        Returns:
            包含节点状态和系统指标的完整状态信息
        """
        stats = self.get_stats()
        nodes = list(self._nodes.values())

        # 计算总请求数和平均响应时间
        total_requests = sum(n.request_count for n in nodes)
        total_concurrent = sum(n.current_concurrent for n in nodes)

        avg_response_time = 0.0
        active_nodes = [n for n in nodes if n.request_count > 0]
        if active_nodes:
            avg_response_time = sum(
                n.avg_response_time for n in active_nodes
            ) / len(active_nodes)

        return {
            "online_nodes": stats["online_nodes"],
            "total_nodes": stats["total_nodes"],
            "total_requests": total_requests,
            "current_concurrent": total_concurrent,
            "avg_response_time_ms": avg_response_time,
            "engines": stats["engines"],
        }

    # ===================== 事件回调设置 =====================

    def on_node_online(self, callback: Callable[[NodeInfo], None]):
        """设置节点上线回调"""
        self._on_node_online = callback

    def on_node_offline(self, callback: Callable[[NodeInfo], None]):
        """设置节点离线回调"""
        self._on_node_offline = callback

    def on_node_status_change(
        self, callback: Callable[[NodeInfo, WorkerStatus, WorkerStatus], None]
    ):
        """设置节点状态变化回调"""
        self._on_node_status_change = callback
