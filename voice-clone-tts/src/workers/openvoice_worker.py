"""
OpenVoice 工作节点

实现 OpenVoice 引擎的工作节点。
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
from ..common.paths import OPENVOICE_MODEL_PATH, VOICES_DIR
from .base_worker import BaseWorker

logger = logging.getLogger(__name__)


class OpenVoiceWorker(BaseWorker):
    """OpenVoice 工作节点"""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8002,
        gateway_url: Optional[str] = None,
        node_id: Optional[str] = None,
        checkpoint_path: Optional[str] = None,
        device: str = "cuda",
        voices_dir: str = "./voices",
    ):
        """
        初始化 OpenVoice Worker

        Args:
            host: 监听地址
            port: 监听端口
            gateway_url: 网关地址
            node_id: 节点 ID
            checkpoint_path: 模型检查点路径
            device: 设备 (cuda/cpu)
            voices_dir: 音色存储目录
        """
        super().__init__(
            engine_type=EngineType.OPENVOICE,
            host=host,
            port=port,
            gateway_url=gateway_url,
            node_id=node_id,
        )

        self.checkpoint_path = checkpoint_path
        self.device = device
        self.voices_dir = Path(voices_dir)
        self.voices_dir.mkdir(parents=True, exist_ok=True)

        # OpenVoice 模型实例
        self._base_speaker_tts = None
        self._tone_color_converter = None
        self._source_se = None

    async def load_model(self) -> bool:
        """加载 OpenVoice 模型"""
        try:
            logger.info(f"Loading OpenVoice model on {self.device}...")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model_sync)

            logger.info("OpenVoice model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load OpenVoice model: {e}")
            return False

    def _load_model_sync(self):
        """同步加载模型"""
        import torch

        # 确定模型路径
        if self.checkpoint_path:
            ckpt_base = Path(self.checkpoint_path)
        else:
            # 使用 paths 模块中定义的默认路径
            ckpt_base = OPENVOICE_MODEL_PATH

        ckpt_converter = ckpt_base / "converter"

        # 导入 OpenVoice
        from openvoice import se_extractor
        from openvoice.api import ToneColorConverter
        from melo.api import TTS

        # 加载 TTS 基础模型
        self._base_speaker_tts = TTS(language="ZH", device=self.device)

        # 加载音色转换器
        self._tone_color_converter = ToneColorConverter(
            str(ckpt_converter / "config.json"),
            device=self.device,
        )
        self._tone_color_converter.load_ckpt(str(ckpt_converter / "checkpoint.pth"))

        # 提取源说话人嵌入
        source_audio = ckpt_base / "base_speakers" / "ses" / "zh.wav"
        if source_audio.exists():
            self._source_se = se_extractor.get_se(
                str(source_audio),
                self._tone_color_converter,
                vad=False,
            )[0]

    async def unload_model(self) -> bool:
        """卸载模型"""
        try:
            if self._base_speaker_tts is not None:
                del self._base_speaker_tts
                self._base_speaker_tts = None

            if self._tone_color_converter is not None:
                del self._tone_color_converter
                self._tone_color_converter = None

            self._source_se = None

            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("OpenVoice model unloaded")
            return True

        except Exception as e:
            logger.error(f"Failed to unload OpenVoice model: {e}")
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
        if self._base_speaker_tts is None:
            raise RuntimeError("Model not loaded")

        # 加载目标音色
        target_se = await self._load_voice_embedding(voice_id)
        if target_se is None:
            raise ValueError(f"Voice not found: {voice_id}")

        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(
            None,
            self._synthesize_sync,
            text,
            target_se,
            language,
            kwargs.get("speed", 1.0),
        )

        return audio_data

    def _synthesize_sync(
        self,
        text: str,
        target_se,
        language: str,
        speed: float,
    ) -> bytes:
        """同步合成"""
        import torch
        import torchaudio
        import tempfile
        import io

        # 使用临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as src_file:
            src_path = src_file.name

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out_file:
            out_path = out_file.name

        try:
            # 1. 基础 TTS
            speaker_ids = self._base_speaker_tts.hps.data.spk2id
            speaker_key = list(speaker_ids.keys())[0]

            self._base_speaker_tts.tts_to_file(
                text=text,
                speaker_id=speaker_ids[speaker_key],
                output_path=src_path,
                speed=speed,
            )

            # 2. 音色转换
            self._tone_color_converter.convert(
                audio_src_path=src_path,
                src_se=self._source_se,
                tgt_se=target_se,
                output_path=out_path,
                message="@OpenVoice",
            )

            # 读取输出
            with open(out_path, "rb") as f:
                return f.read()

        finally:
            if os.path.exists(src_path):
                os.unlink(src_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

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
        if self._tone_color_converter is None:
            raise RuntimeError("Model not loaded")

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            loop = asyncio.get_event_loop()
            target_se = await loop.run_in_executor(
                None,
                self._extract_voice_sync,
                temp_path,
            )

            # 保存音色
            voice_dir = self.voices_dir / voice_id
            voice_dir.mkdir(parents=True, exist_ok=True)

            import torch
            torch.save(target_se, voice_dir / "speaker_embedding.pt")

            metadata = {
                "voice_id": voice_id,
                "name": voice_name or voice_id,
                "engine": "openvoice",
                "created_at": __import__("time").time(),
            }
            with open(voice_dir / "voice.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            return VoiceInfo(
                voice_id=voice_id,
                name=voice_name or voice_id,
                engine="openvoice",
                created_at=metadata["created_at"],
            )

        finally:
            os.unlink(temp_path)

    def _extract_voice_sync(self, audio_path: str):
        """同步提取音色"""
        from openvoice import se_extractor

        target_se, _ = se_extractor.get_se(
            audio_path,
            self._tone_color_converter,
            vad=True,
        )
        return target_se

    async def _load_voice_embedding(self, voice_id: str):
        """加载音色嵌入"""
        import torch

        voice_dir = self.voices_dir / voice_id
        embedding_path = voice_dir / "speaker_embedding.pt"

        if not embedding_path.exists():
            return None

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: torch.load(str(embedding_path), map_location=self.device),
        )

        return embedding


def main():
    """启动 OpenVoice Worker"""
    import argparse

    parser = argparse.ArgumentParser(description="OpenVoice Worker")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8002, help="Port")
    parser.add_argument("--gateway", default=None, help="Gateway URL")
    parser.add_argument("--device", default="cuda", help="Device")
    parser.add_argument("--voices-dir", default="./voices", help="Voices directory")

    args = parser.parse_args()

    worker = OpenVoiceWorker(
        host=args.host,
        port=args.port,
        gateway_url=args.gateway,
        device=args.device,
        voices_dir=args.voices_dir,
    )

    worker.run()


if __name__ == "__main__":
    main()
