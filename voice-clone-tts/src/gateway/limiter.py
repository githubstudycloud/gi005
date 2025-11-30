"""
限流器

提供多层次的请求限流功能。
"""

import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict
import logging

from ..common.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)


class TokenBucket:
    """令牌桶算法实现"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶

        Args:
            capacity: 桶容量
            refill_rate: 每秒填充令牌数
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """
        尝试获取令牌

        Args:
            tokens: 需要的令牌数

        Returns:
            是否获取成功
        """
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        """填充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        refill_amount = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + refill_amount)
        self.last_refill = now


class SlidingWindowCounter:
    """滑动窗口计数器"""

    def __init__(self, window_size: int = 60, limit: int = 100):
        """
        初始化滑动窗口

        Args:
            window_size: 窗口大小（秒）
            limit: 窗口内最大请求数
        """
        self.window_size = window_size
        self.limit = limit
        self.requests: Dict[float, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def is_allowed(self) -> bool:
        """
        检查请求是否被允许

        Returns:
            是否允许
        """
        async with self._lock:
            now = time.time()
            window_start = now - self.window_size

            # 清理过期记录
            expired_keys = [k for k in self.requests if k < window_start]
            for k in expired_keys:
                del self.requests[k]

            # 计算当前窗口内的请求数
            current_count = sum(self.requests.values())

            if current_count >= self.limit:
                return False

            # 记录本次请求
            self.requests[now] = self.requests.get(now, 0) + 1
            return True

    async def get_remaining(self) -> int:
        """获取剩余配额"""
        async with self._lock:
            now = time.time()
            window_start = now - self.window_size

            current_count = sum(
                v for k, v in self.requests.items() if k >= window_start
            )
            return max(0, self.limit - current_count)


class RateLimiter:
    """多层限流器"""

    def __init__(
        self,
        global_rpm: int = 1000,
        ip_rpm: int = 100,
        endpoint_rpm: Optional[Dict[str, int]] = None,
        concurrent_limit: int = 50,
    ):
        """
        初始化限流器

        Args:
            global_rpm: 全局每分钟请求数
            ip_rpm: 单 IP 每分钟请求数
            endpoint_rpm: 各接口每分钟请求数
            concurrent_limit: 并发请求限制
        """
        self.global_rpm = global_rpm
        self.ip_rpm = ip_rpm
        self.endpoint_rpm = endpoint_rpm or {}
        self.concurrent_limit = concurrent_limit

        # 全局限流
        self._global_limiter = SlidingWindowCounter(60, global_rpm)

        # IP 限流
        self._ip_limiters: Dict[str, SlidingWindowCounter] = {}

        # 接口限流
        self._endpoint_limiters: Dict[str, SlidingWindowCounter] = {}

        # 并发计数
        self._current_concurrent = 0
        self._concurrent_lock = asyncio.Lock()

        # 统计
        self._total_requests = 0
        self._rejected_requests = 0

    async def check(
        self,
        client_ip: str,
        endpoint: str = "",
    ) -> bool:
        """
        检查请求是否被允许

        Args:
            client_ip: 客户端 IP
            endpoint: 请求接口

        Returns:
            是否允许

        Raises:
            RateLimitExceededError: 超出限流
        """
        self._total_requests += 1

        # 检查全局限流
        if not await self._global_limiter.is_allowed():
            self._rejected_requests += 1
            logger.warning(f"Global rate limit exceeded")
            raise RateLimitExceededError("Global rate limit exceeded")

        # 检查 IP 限流
        if client_ip not in self._ip_limiters:
            self._ip_limiters[client_ip] = SlidingWindowCounter(60, self.ip_rpm)

        if not await self._ip_limiters[client_ip].is_allowed():
            self._rejected_requests += 1
            logger.warning(f"IP rate limit exceeded: {client_ip}")
            raise RateLimitExceededError(f"Rate limit exceeded for IP: {client_ip}")

        # 检查接口限流
        if endpoint and endpoint in self.endpoint_rpm:
            if endpoint not in self._endpoint_limiters:
                self._endpoint_limiters[endpoint] = SlidingWindowCounter(
                    60, self.endpoint_rpm[endpoint]
                )

            if not await self._endpoint_limiters[endpoint].is_allowed():
                self._rejected_requests += 1
                logger.warning(f"Endpoint rate limit exceeded: {endpoint}")
                raise RateLimitExceededError(
                    f"Rate limit exceeded for endpoint: {endpoint}"
                )

        return True

    async def acquire_concurrent(self) -> bool:
        """
        获取并发槽位

        Returns:
            是否获取成功

        Raises:
            RateLimitExceededError: 并发超限
        """
        async with self._concurrent_lock:
            if self._current_concurrent >= self.concurrent_limit:
                self._rejected_requests += 1
                raise RateLimitExceededError(
                    f"Concurrent limit exceeded: {self.concurrent_limit}"
                )
            self._current_concurrent += 1
            return True

    async def release_concurrent(self):
        """释放并发槽位"""
        async with self._concurrent_lock:
            self._current_concurrent = max(0, self._current_concurrent - 1)

    def get_stats(self) -> Dict:
        """获取限流统计"""
        return {
            "total_requests": self._total_requests,
            "rejected_requests": self._rejected_requests,
            "rejection_rate": (
                self._rejected_requests / self._total_requests
                if self._total_requests > 0
                else 0
            ),
            "current_concurrent": self._current_concurrent,
            "concurrent_limit": self.concurrent_limit,
            "global_rpm": self.global_rpm,
            "ip_rpm": self.ip_rpm,
        }

    async def get_remaining(self, client_ip: str) -> Dict:
        """
        获取客户端剩余配额

        Args:
            client_ip: 客户端 IP

        Returns:
            剩余配额信息
        """
        global_remaining = await self._global_limiter.get_remaining()

        ip_remaining = self.ip_rpm
        if client_ip in self._ip_limiters:
            ip_remaining = await self._ip_limiters[client_ip].get_remaining()

        return {
            "global_remaining": global_remaining,
            "ip_remaining": ip_remaining,
            "concurrent_available": max(
                0, self.concurrent_limit - self._current_concurrent
            ),
        }

    def cleanup_expired(self):
        """
        清理过期的 IP 限流器

        定期调用此方法可释放不活跃 IP 的内存。
        当前实现: 清空所有 IP 限流器（适用于低流量场景）。
        TODO: 实现基于 LRU 或最后访问时间的清理策略。
        """
        if len(self._ip_limiters) > 1000:
            # 当 IP 限流器数量超过阈值时清理
            logger.info(f"Cleaning up {len(self._ip_limiters)} IP rate limiters")
            self._ip_limiters.clear()
