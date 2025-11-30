"""工作节点模块"""
from .base_worker import BaseWorker
from .xtts_worker import XTTSWorker
from .openvoice_worker import OpenVoiceWorker
from .gpt_sovits_worker import GPTSoVITSWorker

__all__ = [
    "BaseWorker",
    "XTTSWorker",
    "OpenVoiceWorker",
    "GPTSoVITSWorker",
]
