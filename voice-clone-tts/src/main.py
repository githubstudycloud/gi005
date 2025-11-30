"""
Voice Clone TTS - 入口文件

使用方法:
    # 启动网关
    python -m src.main gateway --port 8080

    # 启动 XTTS 工作节点
    python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080

    # 启动 OpenVoice 工作节点
    python -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080
"""

import argparse
import sys
import os
import signal
import asyncio
import atexit
from typing import List, Any

from .common.logging import setup_logging, get_logger


# 全局资源跟踪器，用于优雅关闭
_cleanup_handlers: List[Any] = []
_shutdown_event: asyncio.Event = None


def register_cleanup(handler):
    """注册清理回调"""
    _cleanup_handlers.append(handler)


def _do_cleanup():
    """执行所有注册的清理操作"""
    logger = get_logger("shutdown")
    logger.info("Executing cleanup handlers...")

    for handler in reversed(_cleanup_handlers):
        try:
            if asyncio.iscoroutinefunction(handler):
                # 异步清理
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(handler())
                finally:
                    loop.close()
            else:
                handler()
        except Exception as e:
            logger.warning(f"Cleanup handler error: {e}")

    _cleanup_handlers.clear()
    logger.info("Cleanup completed")


def _signal_handler(signum, frame):
    """信号处理器"""
    logger = get_logger("shutdown")
    sig_name = signal.Signals(signum).name
    logger.info(f"Received signal {sig_name}, initiating graceful shutdown...")

    # 设置关闭事件（如果存在）
    global _shutdown_event
    if _shutdown_event is not None:
        _shutdown_event.set()

    # 执行清理
    _do_cleanup()

    # 正常退出
    sys.exit(0)


def setup_signal_handlers():
    """设置信号处理器"""
    # SIGINT (Ctrl+C) 和 SIGTERM (kill)
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Windows 不支持 SIGHUP，但 Unix 系统支持
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, _signal_handler)

    # 注册 atexit 处理器作为备份
    atexit.register(_do_cleanup)


def main():
    parser = argparse.ArgumentParser(
        description="Voice Clone TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 启动网关服务
    python -m src.main gateway --port 8080

    # 启动 XTTS 工作节点（自动注册到网关）
    python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080

    # 启动 OpenVoice 工作节点
    python -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080

    # 单机测试模式（网关 + 工作节点）
    python -m src.main standalone --engine xtts --port 8080
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 全局日志参数
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="日志级别")
    parser.add_argument("--log-dir", default=None, help="日志目录（不指定则不写文件）")
    parser.add_argument("--json-logs", action="store_true", help="使用 JSON 格式日志")

    # 网关命令
    gateway_parser = subparsers.add_parser("gateway", help="启动网关服务")
    gateway_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    gateway_parser.add_argument("--port", type=int, default=8080, help="监听端口")
    gateway_parser.add_argument("--global-rpm", type=int, default=1000, help="全局每分钟请求数")
    gateway_parser.add_argument("--ip-rpm", type=int, default=100, help="单IP每分钟请求数")

    # 工作节点命令
    worker_parser = subparsers.add_parser("worker", help="启动工作节点")
    worker_parser.add_argument("--engine", required=True, choices=["xtts", "openvoice", "gpt-sovits"], help="引擎类型")
    worker_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    worker_parser.add_argument("--port", type=int, default=8001, help="监听端口")
    worker_parser.add_argument("--gateway", default=None, help="网关地址")
    worker_parser.add_argument("--device", default="cuda", help="设备 (cuda/cpu)")
    worker_parser.add_argument("--voices-dir", default="./voices", help="音色存储目录")
    worker_parser.add_argument("--auto-load", action="store_true", help="启动时自动加载模型")

    # 单机模式命令
    standalone_parser = subparsers.add_parser("standalone", help="单机测试模式")
    standalone_parser.add_argument("--engine", default="xtts", choices=["xtts", "openvoice", "gpt-sovits"], help="引擎类型")
    standalone_parser.add_argument("--port", type=int, default=8080, help="网关端口")
    standalone_parser.add_argument("--device", default="cuda", help="设备")

    args = parser.parse_args()

    # 初始化日志系统
    setup_logging(
        level=args.log_level,
        log_dir=args.log_dir,
        json_logs=args.json_logs,
    )

    logger = get_logger("main")

    # 设置信号处理器，确保优雅关闭
    setup_signal_handlers()

    logger.info(f"Voice Clone TTS starting...")

    if args.command == "gateway":
        run_gateway(args)
    elif args.command == "worker":
        run_worker(args)
    elif args.command == "standalone":
        run_standalone(args)
    else:
        parser.print_help()
        sys.exit(1)


def run_gateway(args):
    """启动网关"""
    from .gateway.app import create_gateway
    from .common.models import SystemConfig

    config = SystemConfig(
        global_rpm=args.global_rpm,
        ip_rpm=args.ip_rpm,
    )

    gateway = create_gateway(
        host=args.host,
        port=args.port,
        config=config,
    )

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              Voice Clone TTS - Gateway                  ║
╠══════════════════════════════════════════════════════════════╣
║  Status Page:    http://{args.host}:{args.port}/status                    ║
║  Admin Page:     http://{args.host}:{args.port}/admin                     ║
║  Playground:     http://{args.host}:{args.port}/playground                ║
║  API Docs:       http://{args.host}:{args.port}/docs                      ║
╚══════════════════════════════════════════════════════════════╝
    """)

    gateway.run()


def run_worker(args):
    """启动工作节点"""
    if args.engine == "xtts":
        from .workers.xtts_worker import XTTSWorker

        worker = XTTSWorker(
            host=args.host,
            port=args.port,
            gateway_url=args.gateway,
            device=args.device,
            voices_dir=args.voices_dir,
        )

    elif args.engine == "openvoice":
        from .workers.openvoice_worker import OpenVoiceWorker

        worker = OpenVoiceWorker(
            host=args.host,
            port=args.port,
            gateway_url=args.gateway,
            device=args.device,
            voices_dir=args.voices_dir,
        )

    elif args.engine == "gpt-sovits":
        from .workers.gpt_sovits_worker import GPTSoVITSWorker

        # GPT-SoVITS 需要额外的 API URL 参数
        api_url = os.environ.get("GPT_SOVITS_API_URL", "http://127.0.0.1:9880")

        worker = GPTSoVITSWorker(
            host=args.host,
            port=args.port,
            gateway_url=args.gateway,
            api_url=api_url,
            voices_dir=args.voices_dir,
        )

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          Voice Clone TTS - {args.engine.upper()} Worker               ║
╠══════════════════════════════════════════════════════════════╣
║  Address:        http://{args.host}:{args.port}                           ║
║  Gateway:        {args.gateway or 'Not configured'}                             ║
║  Device:         {args.device}                                         ║
╚══════════════════════════════════════════════════════════════╝
    """)

    if args.auto_load:
        import asyncio
        asyncio.run(worker.activate())

    worker.run()


def run_standalone(args):
    """单机测试模式"""
    import asyncio
    import threading
    import uvicorn

    from .gateway.app import create_gateway
    from .common.models import SystemConfig

    worker_port = args.port + 1
    logger = get_logger("standalone")

    # 创建关闭事件
    global _shutdown_event
    _shutdown_event = asyncio.Event()

    # 启动网关
    config = SystemConfig()
    gateway = create_gateway(
        host="0.0.0.0",
        port=args.port,
        config=config,
    )

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║        Voice Clone TTS - Standalone Mode                ║
╠══════════════════════════════════════════════════════════════╣
║  Gateway:        http://localhost:{args.port}                         ║
║  Worker:         http://localhost:{worker_port} ({args.engine.upper()})                ║
║  Status Page:    http://localhost:{args.port}/status                  ║
║  Playground:     http://localhost:{args.port}/playground              ║
╚══════════════════════════════════════════════════════════════╝

启动中... (按 Ctrl+C 优雅关闭)
    """)

    # 用于存储 uvicorn server 以便后续关闭
    gateway_server = None

    # 在线程中启动网关
    def run_gateway_thread():
        nonlocal gateway_server
        config = uvicorn.Config(
            gateway.app,
            host="0.0.0.0",
            port=args.port,
            log_level="warning",
        )
        gateway_server = uvicorn.Server(config)
        gateway_server.run()

    gateway_thread = threading.Thread(target=run_gateway_thread, name="gateway-thread")
    gateway_thread.start()

    # 等待网关启动
    import time
    time.sleep(2)

    # 创建工作节点
    worker = None

    if args.engine == "xtts":
        from .workers.xtts_worker import XTTSWorker

        worker = XTTSWorker(
            host="0.0.0.0",
            port=worker_port,
            gateway_url=f"http://localhost:{args.port}",
            device=args.device,
        )

    elif args.engine == "openvoice":
        from .workers.openvoice_worker import OpenVoiceWorker

        worker = OpenVoiceWorker(
            host="0.0.0.0",
            port=worker_port,
            gateway_url=f"http://localhost:{args.port}",
            device=args.device,
        )

    elif args.engine == "gpt-sovits":
        from .workers.gpt_sovits_worker import GPTSoVITSWorker

        api_url = os.environ.get("GPT_SOVITS_API_URL", "http://127.0.0.1:9880")

        worker = GPTSoVITSWorker(
            host="0.0.0.0",
            port=worker_port,
            gateway_url=f"http://localhost:{args.port}",
            api_url=api_url,
        )

    else:
        print(f"Unknown engine: {args.engine}")
        sys.exit(1)

    # 注册清理函数
    async def cleanup_worker():
        """清理 Worker 资源"""
        logger.info(f"Stopping {args.engine} worker...")
        try:
            await worker.stop()
            logger.info(f"{args.engine} worker stopped")
        except Exception as e:
            logger.warning(f"Error stopping worker: {e}")

    def cleanup_gateway():
        """清理 Gateway 资源"""
        logger.info("Stopping gateway...")
        if gateway_server is not None:
            gateway_server.should_exit = True
        if gateway_thread.is_alive():
            gateway_thread.join(timeout=5.0)
        logger.info("Gateway stopped")

    # 注册清理处理器（按顺序：先停 worker，再停 gateway）
    register_cleanup(cleanup_worker)
    register_cleanup(cleanup_gateway)

    # 自动激活并运行
    async def activate_and_run():
        await worker.start()
        await worker.activate()

    try:
        asyncio.get_event_loop().run_until_complete(activate_and_run())
        worker.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        # 信号处理器会处理清理


if __name__ == "__main__":
    main()
