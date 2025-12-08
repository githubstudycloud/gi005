"""
NeMo MSDD Speaker Diarization Implementation
基于 NVIDIA NeMo 的多尺度说话人分离解决方案
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import torch
import torchaudio
from omegaconf import OmegaConf

logger = logging.getLogger(__name__)


class NeMoMSDDDiarizer:
    """
    NeMo MSDD (Multi-Scale Diarization Decoder) 说话人分离器

    特点：
    - 使用 TitaNet 提取说话人嵌入
    - 多尺度段落分析（1.5s, 1.25s, 1.0s, 0.75s, 0.5s）
    - 动态尺度加权
    - 可降低 DER 60%
    """

    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        output_dir: str = "./outputs/nemo_msdd",
        cache_dir: str = "./cache/nemo_models"
    ):
        """
        初始化 NeMo MSDD 分离器

        Args:
            device: 计算设备 (cuda/cpu)
            output_dir: 输出目录
            cache_dir: 模型缓存目录
        """
        self.device = device
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)

        # 创建必要的目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.config = None

        logger.info(f"NeMo MSDD Diarizer initialized on {device}")

    def _check_dependencies(self) -> bool:
        """检查依赖是否安装"""
        try:
            import nemo.collections.asr as nemo_asr
            return True
        except ImportError:
            logger.error(
                "NeMo toolkit not found. Please install with:\n"
                "pip install nemo_toolkit[asr]"
            )
            return False

    def _create_config(
        self,
        manifest_path: str,
        num_speakers: Optional[int] = None,
        oracle_vad: bool = False,
        vad_model: str = "vad_multilingual_marblenet",
        speaker_model: str = "titanet_large",
        msdd_model: str = "diar_msdd_telephonic"
    ) -> OmegaConf:
        """
        创建 NeMo 配置

        Args:
            manifest_path: 输入清单文件路径
            num_speakers: 说话人数量（None 表示自动检测）
            oracle_vad: 是否使用真实 VAD 时间戳
            vad_model: VAD 模型名称
            speaker_model: 说话人嵌入模型
            msdd_model: MSDD 模型名称

        Returns:
            OmegaConf 配置对象
        """
        config = {
            "diarizer": {
                "manifest_filepath": manifest_path,
                "out_dir": str(self.output_dir),
                "oracle_vad": oracle_vad,
                "vad": {
                    "model_path": vad_model,
                    "parameters": {
                        "window_length_in_sec": 0.15,
                        "shift_length_in_sec": 0.01,
                        "smoothing": "median",
                        "overlap": 0.5,
                        "onset": 0.8,
                        "offset": 0.6,
                        "pad_onset": 0.05,
                        "pad_offset": -0.1,
                        "min_duration_on": 0.2,
                        "min_duration_off": 0.2,
                        "filter_speech_first": True
                    }
                },
                "speaker_embeddings": {
                    "model_path": speaker_model,
                    "parameters": {
                        # 多尺度窗口长度（秒）
                        "window_length_in_sec": [1.5, 1.25, 1.0, 0.75, 0.5],
                        # 对应的滑动步长
                        "shift_length_in_sec": [0.75, 0.625, 0.5, 0.375, 0.25],
                        # 多尺度权重（相等权重）
                        "multiscale_weights": [1.0, 1.0, 1.0, 1.0, 1.0],
                        "save_embeddings": True
                    }
                },
                "clustering": {
                    "parameters": {
                        "oracle_num_speakers": num_speakers is not None,
                        "max_num_speakers": num_speakers if num_speakers else 8,
                        "enhanced_count_thres": 80,
                        "max_rp_threshold": 0.25,
                        "sparse_search_volume": 30
                    }
                },
                "msdd_model": {
                    "model_path": msdd_model,
                    "parameters": {
                        # Sigmoid 阈值 [开始, 结束]
                        "sigmoid_threshold": [0.7, 1.0],
                        "seq_eval_mode": False,
                        "split_infer": True,
                        "diar_window_length": 50,
                        "overlap_infer_spk_limit": 5
                    }
                }
            }
        }

        return OmegaConf.create(config)

    def _create_manifest(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
        rttm_path: Optional[str] = None
    ) -> str:
        """
        创建 NeMo 输入清单文件

        Args:
            audio_path: 音频文件路径
            num_speakers: 说话人数量
            rttm_path: RTTM 标注文件路径（用于 oracle VAD）

        Returns:
            清单文件路径
        """
        manifest_path = self.output_dir / "input_manifest.json"

        # 获取音频时长
        waveform, sample_rate = torchaudio.load(audio_path)
        duration = waveform.shape[1] / sample_rate

        manifest_entry = {
            "audio_filepath": str(Path(audio_path).absolute()),
            "offset": 0,
            "duration": duration,
            "label": "infer",
            "text": "-",
            "num_speakers": num_speakers if num_speakers else None,
            "rttm_filepath": rttm_path if rttm_path else None
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_entry, f)
            f.write("\n")

        logger.info(f"Created manifest: {manifest_path}")
        return str(manifest_path)

    def load_model(self, config: Optional[OmegaConf] = None):
        """
        加载 NeMo MSDD 模型

        Args:
            config: 可选的配置对象
        """
        if not self._check_dependencies():
            raise RuntimeError("NeMo dependencies not installed")

        try:
            from nemo.collections.asr.models.msdd_models import NeuralDiarizer

            if config is None:
                # 使用默认配置
                manifest_path = self.output_dir / "input_manifest.json"
                config = self._create_config(str(manifest_path))

            self.config = config

            logger.info("Loading NeMo MSDD models...")
            logger.info(f"  VAD Model: {config.diarizer.vad.model_path}")
            logger.info(f"  Speaker Embedding: {config.diarizer.speaker_embeddings.model_path}")
            logger.info(f"  MSDD Model: {config.diarizer.msdd_model.model_path}")

            # 创建神经分离器
            self.model = NeuralDiarizer(cfg=config)

            logger.info("NeMo MSDD models loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load NeMo MSDD models: {e}")
            raise

    def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
        oracle_vad: bool = False,
        rttm_path: Optional[str] = None
    ) -> Dict:
        """
        执行说话人分离

        Args:
            audio_path: 音频文件路径
            num_speakers: 说话人数量（None 表示自动检测）
            oracle_vad: 是否使用真实 VAD 时间戳
            rttm_path: RTTM 标注文件路径

        Returns:
            分离结果字典，包含：
            - segments: 说话人片段列表
            - num_speakers: 检测到的说话人数量
            - rttm_path: 输出的 RTTM 文件路径
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # 创建清单文件
        manifest_path = self._create_manifest(
            audio_path,
            num_speakers=num_speakers,
            rttm_path=rttm_path
        )

        # 更新配置
        self.config.diarizer.manifest_filepath = manifest_path
        self.config.diarizer.oracle_vad = oracle_vad
        if num_speakers:
            self.config.diarizer.clustering.parameters.oracle_num_speakers = True
            self.config.diarizer.clustering.parameters.max_num_speakers = num_speakers

        logger.info(f"Starting MSDD diarization for: {audio_path}")
        logger.info(f"  Oracle VAD: {oracle_vad}")
        logger.info(f"  Num speakers: {num_speakers if num_speakers else 'auto'}")

        try:
            # 执行分离
            self.model.diarize()

            # 解析结果
            rttm_output = self.output_dir / "pred_rttms" / f"{Path(audio_path).stem}.rttm"
            segments = self._parse_rttm(rttm_output)

            detected_speakers = len(set(seg["speaker"] for seg in segments))

            result = {
                "audio_path": audio_path,
                "segments": segments,
                "num_speakers": detected_speakers,
                "rttm_path": str(rttm_output)
            }

            logger.info(f"Diarization completed. Detected {detected_speakers} speakers")
            logger.info(f"RTTM output: {rttm_output}")

            return result

        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            raise

    def _parse_rttm(self, rttm_path: Path) -> List[Dict]:
        """
        解析 RTTM 文件

        Args:
            rttm_path: RTTM 文件路径

        Returns:
            片段列表
        """
        segments = []

        if not rttm_path.exists():
            logger.warning(f"RTTM file not found: {rttm_path}")
            return segments

        with open(rttm_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 8:
                    continue

                # RTTM 格式: SPEAKER <file-id> <channel-id> <start> <duration> <NA> <NA> <speaker-id> <NA>
                segment = {
                    "start": float(parts[3]),
                    "end": float(parts[3]) + float(parts[4]),
                    "duration": float(parts[4]),
                    "speaker": parts[7]
                }
                segments.append(segment)

        # 按开始时间排序
        segments.sort(key=lambda x: x["start"])

        return segments

    def format_output(self, result: Dict, format_type: str = "detailed") -> str:
        """
        格式化输出结果

        Args:
            result: 分离结果字典
            format_type: 输出格式 (detailed/simple/json)

        Returns:
            格式化的字符串
        """
        if format_type == "json":
            return json.dumps(result, indent=2, ensure_ascii=False)

        segments = result["segments"]
        num_speakers = result["num_speakers"]

        if format_type == "simple":
            output = f"Detected {num_speakers} speakers\n"
            output += f"Total segments: {len(segments)}\n\n"
            for seg in segments:
                output += f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['speaker']}\n"
            return output

        # detailed format
        output = f"=" * 60 + "\n"
        output += f"NeMo MSDD Speaker Diarization Results\n"
        output += f"=" * 60 + "\n"
        output += f"Audio: {result['audio_path']}\n"
        output += f"Detected speakers: {num_speakers}\n"
        output += f"Total segments: {len(segments)}\n"
        output += f"RTTM file: {result['rttm_path']}\n"
        output += f"-" * 60 + "\n"

        for i, seg in enumerate(segments, 1):
            output += f"{i:3d}. [{seg['start']:7.2f}s - {seg['end']:7.2f}s] "
            output += f"({seg['duration']:5.2f}s) | Speaker: {seg['speaker']}\n"

        return output


def main():
    """命令行测试入口"""
    import argparse

    parser = argparse.ArgumentParser(description="NeMo MSDD Speaker Diarization")
    parser.add_argument("audio_path", type=str, help="Path to audio file")
    parser.add_argument("--num-speakers", type=int, default=None, help="Number of speakers")
    parser.add_argument("--oracle-vad", action="store_true", help="Use oracle VAD")
    parser.add_argument("--rttm-path", type=str, default=None, help="Path to RTTM file")
    parser.add_argument("--output-dir", type=str, default="./outputs/nemo_msdd", help="Output directory")
    parser.add_argument("--device", type=str, default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--format", type=str, default="detailed", choices=["detailed", "simple", "json"], help="Output format")

    args = parser.parse_args()

    # 创建分离器
    diarizer = NeMoMSDDDiarizer(
        device=args.device,
        output_dir=args.output_dir
    )

    # 加载模型
    diarizer.load_model()

    # 执行分离
    result = diarizer.diarize(
        audio_path=args.audio_path,
        num_speakers=args.num_speakers,
        oracle_vad=args.oracle_vad,
        rttm_path=args.rttm_path
    )

    # 输出结果
    output = diarizer.format_output(result, format_type=args.format)
    print(output)


if __name__ == "__main__":
    main()
