"""
GPT-SoVITS 工作节点

实现 GPT-SoVITS 引擎的工作节点。
GPT-SoVITS 使用独立的 API 服务器，此 Worker 作为代理。
"""

import os
import io
import json
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import httpx

from ..common.models import EngineType, VoiceInfo
from .base_worker import BaseWorker

logger = logging.getLogger(__name__)


class GPTSoVITSWorker(BaseWorker):
    """GPT-SoVITS 工作节点"""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8003,
        gateway_url: Optional[str] = None,
        node_id: Optional[str] = None,
        api_url: str = "http://127.0.0.1:9880",
        voices_dir: str = "./voices",
    ):
        """
        初始化 GPT-SoVITS Worker

        Args:
            host: 监听地址
            port: 监听端口
            gateway_url: 网关地址
            node_id: 节点 ID
            api_url: GPT-SoVITS API 服务地址
            voices_dir: 音色存储目录
        """
        super().__init__(
            engine_type=EngineType.GPT_SOVITS,
            host=host,
            port=port,
            gateway_url=gateway_url,
            node_id=node_id,
        )

        self.api_url = api_url.rstrip("/")
        self.voices_dir = Path(voices_dir)
        self.voices_dir.mkdir(parents=True, exist_ok=True)

        # HTTP 客户端
        self._client: Optional[httpx.AsyncClient] = None

    async def load_model(self) -> bool:
        """
        检查 GPT-SoVITS API 服务是否可用

        GPT-SoVITS 模型由独立的 API 服务管理，
        这里只是检查连接性。
        """
        try:
            logger.info(f"Connecting to GPT-SoVITS API at {self.api_url}...")

            self._client = httpx.AsyncClient(timeout=60.0)

            # 检查 API 服务是否可用 (使用 /docs 端点，因为根路径返回 404)
            resp = await self._client.get(f"{self.api_url}/docs")
            if resp.status_code == 200:
                logger.info("GPT-SoVITS API connected successfully")
                return True
            else:
                logger.warning(f"GPT-SoVITS API returned: {resp.status_code}")
                return False

        except httpx.ConnectError:
            logger.error(f"Cannot connect to GPT-SoVITS API at {self.api_url}")
            logger.info("Please start GPT-SoVITS API server first:")
            logger.info("  cd GPT-SoVITS && python api_v2.py")
            return False

        except Exception as e:
            logger.error(f"Failed to connect to GPT-SoVITS API: {e}")
            return False

    async def unload_model(self) -> bool:
        """关闭连接"""
        try:
            if self._client is not None:
                await self._client.aclose()
                self._client = None

            logger.info("GPT-SoVITS connection closed")
            return True

        except Exception as e:
            logger.error(f"Failed to close GPT-SoVITS connection: {e}")
            return False

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
            WAV 格式音频数据
        """
        if self._client is None:
            raise RuntimeError("API not connected")

        # 加载音色配置
        voice_config = await self._load_voice_config(voice_id)
        if voice_config is None:
            raise ValueError(f"Voice not found: {voice_id}")

        # 构建请求参数
        params = {
            "text": text,
            "text_lang": self._map_language(language),
            "ref_audio_path": voice_config.get("ref_audio_path", ""),
            "prompt_text": voice_config.get("prompt_text", ""),
            "prompt_lang": voice_config.get("prompt_lang", "zh"),
            "speed": kwargs.get("speed", 1.0),
        }

        # 如果有 GPT 模型路径，添加到参数
        if "gpt_model_path" in voice_config:
            params["gpt_model_path"] = voice_config["gpt_model_path"]
        if "sovits_model_path" in voice_config:
            params["sovits_model_path"] = voice_config["sovits_model_path"]

        try:
            # 调用 GPT-SoVITS API
            resp = await self._client.post(
                f"{self.api_url}/tts",
                json=params,
            )

            if resp.status_code != 200:
                error_msg = resp.text
                raise RuntimeError(f"GPT-SoVITS API error: {error_msg}")

            return resp.content

        except httpx.TimeoutException:
            raise RuntimeError("GPT-SoVITS API timeout")

    async def extract_voice(
        self,
        audio_data: bytes,
        voice_id: str,
        voice_name: str = "",
        **kwargs,
    ) -> VoiceInfo:
        """
        提取音色

        GPT-SoVITS 不需要预先提取嵌入，只需保存参考音频和相关配置。

        Args:
            audio_data: 音频数据
            voice_id: 音色 ID
            voice_name: 音色名称
            **kwargs: 其他参数
                - prompt_text: 参考音频的文本内容
                - prompt_lang: 参考音频的语言
                - gpt_model_path: 可选的 GPT 模型路径
                - sovits_model_path: 可选的 SoVITS 模型路径

        Returns:
            音色信息
        """
        import time

        voice_dir = self.voices_dir / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)

        # 保存参考音频
        ref_audio_path = voice_dir / "reference.wav"
        with open(ref_audio_path, "wb") as f:
            f.write(audio_data)

        # 保存配置
        config = {
            "voice_id": voice_id,
            "name": voice_name or voice_id,
            "engine": "gpt-sovits",
            "ref_audio_path": str(ref_audio_path.absolute()),
            "prompt_text": kwargs.get("prompt_text", ""),
            "prompt_lang": kwargs.get("prompt_lang", "zh"),
            "created_at": time.time(),
        }

        # 可选的模型路径
        if "gpt_model_path" in kwargs:
            config["gpt_model_path"] = kwargs["gpt_model_path"]
        if "sovits_model_path" in kwargs:
            config["sovits_model_path"] = kwargs["sovits_model_path"]

        with open(voice_dir / "voice.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return VoiceInfo(
            voice_id=voice_id,
            name=voice_name or voice_id,
            engine="gpt-sovits",
            created_at=config["created_at"],
        )

    async def _load_voice_config(self, voice_id: str) -> Optional[Dict]:
        """加载音色配置"""
        voice_dir = self.voices_dir / voice_id
        config_path = voice_dir / "voice.json"

        if not config_path.exists():
            return None

        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _map_language(self, language: str) -> str:
        """映射语言代码到 GPT-SoVITS 格式"""
        mapping = {
            "zh": "zh",
            "zh-cn": "zh",
            "zh-tw": "zh",
            "en": "en",
            "en-us": "en",
            "en-gb": "en",
            "ja": "ja",
            "jp": "ja",
            "ko": "ko",
            "kr": "ko",
            "yue": "yue",  # 粤语
            "auto": "auto",
        }
        return mapping.get(language.lower(), "zh")


def main():
    """启动 GPT-SoVITS Worker"""
    import argparse

    parser = argparse.ArgumentParser(description="GPT-SoVITS Worker")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8003, help="Port")
    parser.add_argument("--gateway", default=None, help="Gateway URL")
    parser.add_argument("--api-url", default="http://127.0.0.1:9880", help="GPT-SoVITS API URL")
    parser.add_argument("--voices-dir", default="./voices", help="Voices directory")

    args = parser.parse_args()

    worker = GPTSoVITSWorker(
        host=args.host,
        port=args.port,
        gateway_url=args.gateway,
        api_url=args.api_url,
        voices_dir=args.voices_dir,
    )

    worker.run()


if __name__ == "__main__":
    main()
