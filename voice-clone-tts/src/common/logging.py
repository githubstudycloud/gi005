"""
日志系统配置

提供统一的日志配置，支持:
- 控制台彩色输出
- 文件日志（按大小轮转）
- JSON 格式日志
- 请求追踪 ID
"""

import os
import sys
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
from contextvars import ContextVar

# 请求追踪 ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # 添加请求 ID
        request_id = request_id_var.get()
        if request_id:
            record.request_id = f"[{request_id[:8]}]"
        else:
            record.request_id = ""

        # 添加颜色
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加请求 ID
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)


class RequestContextFilter(logging.Filter):
    """添加请求上下文信息的过滤器"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


def setup_logging(
    level: str = "INFO",
    log_dir: Optional[str] = None,
    json_logs: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别
        log_dir: 日志文件目录（None 表示不写入文件）
        json_logs: 是否使用 JSON 格式
        max_file_size: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if json_logs:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_format = (
            "%(asctime)s %(levelname)-8s "
            "%(request_id)s "
            "[%(name)s] %(message)s"
        )
        console_handler.setFormatter(ColoredFormatter(console_format))

    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)

    # 文件处理器
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # 常规日志
        file_handler = RotatingFileHandler(
            log_path / "voice_clone.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)

        if json_logs:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_format = (
                "%(asctime)s %(levelname)-8s "
                "[%(request_id)s] "
                "[%(name)s:%(lineno)d] %(message)s"
            )
            file_handler.setFormatter(logging.Formatter(file_format))

        file_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(file_handler)

        # 错误日志（单独文件）
        error_handler = RotatingFileHandler(
            log_path / "voice_clone_error.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-8s "
            "[%(request_id)s] "
            "[%(name)s:%(lineno)d] %(message)s\n"
            "%(pathname)s"
        ))
        error_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(error_handler)

    # 抑制一些过于verbose的库日志
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)


def generate_request_id() -> str:
    """生成请求 ID"""
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    """设置当前请求的 ID"""
    request_id_var.set(request_id)


def get_request_id() -> str:
    """获取当前请求的 ID"""
    return request_id_var.get()


class LogContext:
    """日志上下文管理器"""

    def __init__(self, request_id: Optional[str] = None):
        self.request_id = request_id or generate_request_id()
        self._token = None

    def __enter__(self):
        self._token = request_id_var.set(self.request_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token:
            request_id_var.reset(self._token)


class RequestLogMiddleware:
    """FastAPI 请求日志中间件"""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("request")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import time

        request_id = generate_request_id()
        set_request_id(request_id)

        start_time = time.time()
        method = scope.get("method", "")
        path = scope.get("path", "")

        # 记录请求
        self.logger.info(f"→ {method} {path}")

        # 捕获响应状态
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = (time.time() - start_time) * 1000
            self.logger.info(
                f"← {method} {path} {status_code} ({elapsed:.2f}ms)"
            )
