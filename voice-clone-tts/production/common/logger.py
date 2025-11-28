"""
统一日志系统

使用示例:
    from common.logger import get_logger, setup_logging

    # 设置日志（在应用启动时调用一次）
    setup_logging(level="DEBUG", log_dir="./logs")

    # 获取 logger
    logger = get_logger(__name__)
    logger.info("应用启动")
    logger.debug("调试信息")
    logger.warning("警告信息")
    logger.error("错误信息", exc_info=True)
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler

import coloredlogs


# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 全局配置
_logging_configured = False


def get_logger(name: str) -> logging.Logger:
    """
    获取 logger 实例

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        logging.Logger 实例
    """
    return logging.getLogger(name)


def setup_logging(
    level: str = "INFO",
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    format_string: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True,
    file_output: bool = True,
    color_output: bool = True,
):
    """
    设置全局日志配置

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志目录
        log_file: 日志文件名（不含路径）
        format_string: 日志格式
        date_format: 时间格式
        max_file_size: 单个日志文件最大大小（字节）
        backup_count: 保留的日志文件数量
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        color_output: 控制台是否使用彩色输出
    """
    global _logging_configured

    if _logging_configured:
        return

    # 获取根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台输出
    if console_output:
        if color_output:
            # 使用 coloredlogs
            coloredlogs.install(
                level=level.upper(),
                fmt=format_string,
                datefmt=date_format,
                level_styles={
                    'debug': {'color': 'cyan'},
                    'info': {'color': 'green'},
                    'warning': {'color': 'yellow'},
                    'error': {'color': 'red'},
                    'critical': {'color': 'red', 'bold': True},
                },
                field_styles={
                    'asctime': {'color': 'white'},
                    'name': {'color': 'blue'},
                    'levelname': {'bold': True},
                }
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_handler.setFormatter(
                logging.Formatter(format_string, date_format)
            )
            root_logger.addHandler(console_handler)

    # 文件输出
    if file_output and log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        if not log_file:
            log_file = f"voice_clone_{datetime.now().strftime('%Y%m%d')}.log"

        file_path = log_path / log_file

        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(
            logging.Formatter(format_string, date_format)
        )
        root_logger.addHandler(file_handler)

    # 设置第三方库日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)

    _logging_configured = True


def setup_logging_from_config(config: dict):
    """
    从配置字典设置日志

    Args:
        config: 日志配置字典，格式参考 config.yaml 中的 logging 部分
    """
    logging_config = config.get("logging", {})

    level = logging_config.get("level", "INFO")
    format_string = logging_config.get("format", DEFAULT_FORMAT)

    file_config = logging_config.get("file", {})
    file_enabled = file_config.get("enabled", True)
    max_size_str = file_config.get("max_size", "10MB")
    backup_count = file_config.get("backup_count", 5)

    # 解析文件大小
    max_size = parse_size(max_size_str)

    console_config = logging_config.get("console", {})
    console_enabled = console_config.get("enabled", True)
    color_enabled = console_config.get("color", True)

    log_dir = config.get("paths", {}).get("log_dir", "./logs")

    setup_logging(
        level=level,
        log_dir=log_dir if file_enabled else None,
        format_string=format_string,
        max_file_size=max_size,
        backup_count=backup_count,
        console_output=console_enabled,
        file_output=file_enabled,
        color_output=color_enabled,
    )


def parse_size(size_str: str) -> int:
    """
    解析大小字符串

    Args:
        size_str: 大小字符串，如 "10MB", "1GB"

    Returns:
        字节数
    """
    size_str = size_str.upper().strip()

    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 * 1024,
        'GB': 1024 * 1024 * 1024,
    }

    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            number = float(size_str[:-len(unit)])
            return int(number * multiplier)

    return int(size_str)


class LoggerMixin:
    """
    日志混入类，为类提供 logger 属性

    使用示例:
        class MyClass(LoggerMixin):
            def do_something(self):
                self.logger.info("Doing something")
    """

    @property
    def logger(self) -> logging.Logger:
        """获取以类名命名的 logger"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


# 预定义的 logger
main_logger = get_logger("voice_clone")
api_logger = get_logger("voice_clone.api")
engine_logger = get_logger("voice_clone.engine")
