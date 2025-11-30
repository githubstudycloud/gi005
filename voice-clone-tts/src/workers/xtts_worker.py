"""
XTTS 工作节点

实现 XTTS-v2 引擎的工作节点。
"""

import os
import io
import json
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

from ..common.models import EngineType, VoiceInfo
from ..common.paths import XTTS_MODEL_PATH, VOICES_DIR
from .base_worker import BaseWorker

logger = logging.getLogger(__name__)


class XTTSWorker(BaseWorker):
    """XTTS-v2 工作节点"""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8001,
        gateway_url: Optional[str] = None,
        node_id: Optional[str] = None,
        model_path: Optional[str] = None,
        device: str = "cuda",
        voices_dir: str = "./voices",
    ):
        """
        初始化 XTTS Worker

        Args:
            host: 监听地址
            port: 监听端口
            gateway_url: 网关地址
            node_id: 节点 ID
            model_path: 模型路径
            device: 设备 (cuda/cpu)
            voices_dir: 音色存储目录
        """
        super().__init__(
            engine_type=EngineType.XTTS,
            host=host,
            port=port,
            gateway_url=gateway_url,
            node_id=node_id,
        )

        self.model_path = model_path
        self.device = device
        self.voices_dir = Path(voices_dir)
        self.voices_dir.mkdir(parents=True, exist_ok=True)

        # XTTS 模型实例
        self._model = None
        self._config = None

    async def load_model(self) -> bool:
        """加载 XTTS 模型"""
        try:
            logger.info(f"Loading XTTS model on {self.device}...")

            # 在线程池中运行同步加载代码
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model_sync)

            logger.info("XTTS model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load XTTS model: {e}")
            return False

    def _load_model_sync(self):
        """同步加载模型"""
        import torch
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts

        # 设置环境变量
        os.environ["COQUI_TOS_AGREED"] = "1"

        # 确定模型路径
        if self.model_path:
            model_dir = Path(self.model_path)
        else:
            # 使用 paths 模块中定义的默认路径
            model_dir = XTTS_MODEL_PATH

        config_path = model_dir / "config.json"
        checkpoint_dir = model_dir

        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        # 加载配置和模型
        self._config = XttsConfig()
        self._config.load_json(str(config_path))

        self._model = Xtts.init_from_config(self._config)
        self._model.load_checkpoint(
            self._config,
            checkpoint_dir=str(checkpoint_dir),
            eval=True,
        )

        if self.device == "cuda" and torch.cuda.is_available():
            self._model.cuda()
        else:
            self.device = "cpu"

    async def unload_model(self) -> bool:
        """卸载模型"""
        try:
            if self._model is not None:
                del self._model
                self._model = None
                self._config = None

                # 清理 GPU 内存
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            logger.info("XTTS model unloaded")
            return True

        except Exception as e:
            logger.error(f"Failed to unload XTTS model: {e}")
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
            **kwargs: 其他参数（speed, pitch 等）

        Returns:
            WAV 格式音频数据
        """
        if self._model is None:
            raise RuntimeError("Model not loaded")

        # 加载音色
        voice_embedding = await self._load_voice_embedding(voice_id)
        if voice_embedding is None:
            raise ValueError(f"Voice not found: {voice_id}")

        # 在线程池中运行合成
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(
            None,
            self._synthesize_sync,
            text,
            voice_embedding,
            language,
            kwargs.get("speed", 1.0),
        )

        return audio_data

    def _synthesize_sync(
        self,
        text: str,
        voice_embedding: Dict,
        language: str,
        speed: float,
    ) -> bytes:
        """同步合成"""
        import torch
        import torchaudio
        import io

        gpt_cond_latent = voice_embedding["gpt_cond_latent"]
        speaker_embedding = voice_embedding["speaker_embedding"]

        # 合成
        out = self._model.inference(
            text=text,
            language=language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            speed=speed,
        )

        # 转换为 WAV
        audio_tensor = torch.tensor(out["wav"]).unsqueeze(0)
        buffer = io.BytesIO()
        torchaudio.save(buffer, audio_tensor, 24000, format="wav")
        buffer.seek(0)

        return buffer.read()

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
        if self._model is None:
            raise RuntimeError("Model not loaded")

        # 保存临时音频文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            # 在线程池中提取
            loop = asyncio.get_event_loop()
            voice_embedding = await loop.run_in_executor(
                None,
                self._extract_voice_sync,
                temp_path,
            )

            # 保存音色
            voice_dir = self.voices_dir / voice_id
            voice_dir.mkdir(parents=True, exist_ok=True)

            # 保存嵌入
            import torch
            torch.save(voice_embedding, voice_dir / "embedding.pt")

            # 保存元数据
            metadata = {
                "voice_id": voice_id,
                "name": voice_name or voice_id,
                "engine": "xtts",
                "created_at": __import__("time").time(),
            }
            with open(voice_dir / "voice.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            return VoiceInfo(
                voice_id=voice_id,
                name=voice_name or voice_id,
                engine="xtts",
                created_at=metadata["created_at"],
            )

        finally:
            os.unlink(temp_path)

    def _extract_voice_sync(self, audio_path: str) -> Dict:
        """同步提取音色"""
        gpt_cond_latent, speaker_embedding = self._model.get_conditioning_latents(
            audio_path=[audio_path]
        )

        return {
            "gpt_cond_latent": gpt_cond_latent,
            "speaker_embedding": speaker_embedding,
        }

    async def _load_voice_embedding(self, voice_id: str) -> Optional[Dict]:
        """加载音色嵌入"""
        import torch

        voice_dir = self.voices_dir / voice_id
        embedding_path = voice_dir / "embedding.pt"

        if not embedding_path.exists():
            # 尝试从参考音频提取
            # 这里可以添加默认音色逻辑
            return None

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: torch.load(str(embedding_path), map_location=self.device),
        )

        return embedding


def main():
    """启动 XTTS Worker"""
    import argparse

    parser = argparse.ArgumentParser(description="XTTS Worker")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8001, help="Port")
    parser.add_argument("--gateway", default=None, help="Gateway URL")
    parser.add_argument("--device", default="cuda", help="Device")
    parser.add_argument("--voices-dir", default="./voices", help="Voices directory")

    args = parser.parse_args()

    worker = XTTSWorker(
        host=args.host,
        port=args.port,
        gateway_url=args.gateway,
        device=args.device,
        voices_dir=args.voices_dir,
    )

    worker.run()


if __name__ == "__main__":
    main()
