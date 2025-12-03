# 说话人分离 v3 解决方案

> 基于 v2 方案实测反馈的深度优化版本，聚焦于提升分离准确性

## 1. v2 方案问题分析

### 1.1 测试中发现的问题

| 问题类型 | 具体表现 | 根本原因 |
|---------|---------|---------|
| **分离边界不准** | 说话人切换点识别偏差 | VAD 和分割模型阈值未针对场景优化 |
| **同人误判为多人** | 同一说话人在不同时段被识别为不同人 | 嵌入向量对噪声/信道变化敏感 |
| **多人误判为同人** | 声音相似的说话人被合并 | 聚类阈值过松，嵌入区分度不足 |
| **重叠段处理差** | 重叠语音段识别不准或丢失 | 重叠检测灵敏度不足 |
| **短片段遗漏** | <1秒的短语音被忽略 | 最小段长阈值过高 |

### 1.2 v2 方案的技术局限

```
v2 问题点:
├── Pyannote 默认参数不适用于复杂场景
├── 单一嵌入模型对噪声鲁棒性不足
├── 缺乏多尺度分析机制
├── 聚类后缺乏精细化修正
└── 无预处理质量保证
```

## 2. v3 核心优化策略

### 2.1 技术路线选型对比

| 方案 | 技术栈 | DER | 优势 | 劣势 |
|------|--------|-----|------|------|
| **DiariZen** | WavLM + EEND-VC | 13.3% | 多说话人场景优秀 (5+人: 7.1%) | 需要 GPU，部署复杂 |
| **NeMo MSDD** | TitaNet + 多尺度解码 | ~8-12% | 重叠检测优秀，可减少 60% DER | 依赖 NVIDIA 生态 |
| **Pyannote 3.1 优化** | 参数调优 + 后处理 | ~8-11% | 易部署，社区活跃 | 需要针对场景优化 |
| **SpeakerLM** | 端到端 MLLM | 最新 | 联合 SD+ASR，无误差传播 | 2025 年论文，未开源 |

### 2.2 v3 推荐方案：多层级优化架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        v3 优化架构                               │
├─────────────────────────────────────────────────────────────────┤
│  1. 预处理增强层                                                  │
│     ├── DNS/DTLN 深度降噪                                        │
│     ├── DWT + CNN 信号增强                                       │
│     └── 自适应增益控制 (AGC)                                      │
├─────────────────────────────────────────────────────────────────┤
│  2. 多尺度分离层 (核心改进)                                        │
│     ├── DiariZen: WavLM + EEND 局部窗口分析                       │
│     ├── Pyannote 3.1: 全局端到端分离                              │
│     └── 融合决策: 置信度加权投票                                   │
├─────────────────────────────────────────────────────────────────┤
│  3. 嵌入增强层                                                    │
│     ├── TitaNet-Large: 主嵌入 (噪声鲁棒)                          │
│     ├── WavLM-TDNN: 辅助嵌入 (细节保留)                           │
│     └── 多嵌入融合: 拼接 + 注意力权重                              │
├─────────────────────────────────────────────────────────────────┤
│  4. 精细化后处理层                                                 │
│     ├── 边界平滑: 中值滤波 + 最小持续时间约束                       │
│     ├── 短片段回溯: 二次嵌入匹配                                   │
│     ├── 重叠修正: SepFormer 分离 + 重新分配                        │
│     └── LLM 后处理: 语义一致性校正 (可选)                          │
├─────────────────────────────────────────────────────────────────┤
│  5. 说话人一致性层                                                 │
│     ├── 跨会话数据库: FAISS 向量检索                               │
│     ├── 在线嵌入更新: EMA 动量更新                                 │
│     └── 置信度阈值: 动态自适应                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 具体代码优化

### 3.1 预处理增强

```python
"""
预处理增强模块 - 解决噪声导致的分离不准问题
"""
import torch
import torchaudio
from typing import Tuple
import numpy as np

class AudioPreprocessor:
    """音频预处理器 - v3 增强版"""

    def __init__(self,
                 sample_rate: int = 16000,
                 use_dns: bool = True,
                 use_agc: bool = True):
        self.sample_rate = sample_rate
        self.use_dns = use_dns
        self.use_agc = use_agc

        # DNS 深度降噪模型 (使用 DTLN 或 DNS-Challenge 模型)
        if use_dns:
            self._load_denoiser()

    def _load_denoiser(self):
        """加载深度降噪模型"""
        try:
            # 方案1: 使用 DTLN (轻量级，CPU 友好)
            # pip install DTLN
            from DTLN.run_DTLN import DTLN_model
            self.denoiser = DTLN_model()
            self.denoiser_type = "dtln"
        except ImportError:
            # 方案2: 使用 torchaudio 内置降噪
            self.denoiser = None
            self.denoiser_type = "spectral"

    def denoise(self, waveform: torch.Tensor) -> torch.Tensor:
        """深度降噪"""
        if self.denoiser_type == "dtln" and self.denoiser:
            # DTLN 降噪
            audio_np = waveform.numpy().squeeze()
            denoised = self.denoiser.process(audio_np)
            return torch.from_numpy(denoised).unsqueeze(0)
        else:
            # 谱减法降噪 (备选方案)
            return self._spectral_denoise(waveform)

    def _spectral_denoise(self, waveform: torch.Tensor) -> torch.Tensor:
        """谱减法降噪"""
        # 计算 STFT
        n_fft = 512
        hop_length = 160
        stft = torch.stft(waveform.squeeze(), n_fft=n_fft,
                          hop_length=hop_length, return_complex=True)

        # 估计噪声频谱 (使用前 0.5 秒)
        noise_frames = int(0.5 * self.sample_rate / hop_length)
        noise_spectrum = torch.abs(stft[:, :noise_frames]).mean(dim=1, keepdim=True)

        # 谱减法
        magnitude = torch.abs(stft)
        phase = torch.angle(stft)
        enhanced_magnitude = torch.clamp(magnitude - 1.5 * noise_spectrum, min=0)

        # 重建
        enhanced_stft = enhanced_magnitude * torch.exp(1j * phase)
        enhanced = torch.istft(enhanced_stft, n_fft=n_fft, hop_length=hop_length)

        return enhanced.unsqueeze(0)

    def apply_agc(self, waveform: torch.Tensor,
                  target_db: float = -20.0) -> torch.Tensor:
        """自适应增益控制"""
        # 计算当前 RMS
        rms = torch.sqrt(torch.mean(waveform ** 2))
        current_db = 20 * torch.log10(rms + 1e-8)

        # 计算增益
        gain_db = target_db - current_db
        gain = 10 ** (gain_db / 20)

        # 限制增益范围防止过度放大
        gain = torch.clamp(gain, 0.1, 10.0)

        return waveform * gain

    def process(self, audio_path: str) -> Tuple[torch.Tensor, int]:
        """完整预处理流程"""
        # 加载音频
        waveform, sr = torchaudio.load(audio_path)

        # 重采样
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)

        # 单声道
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        # 降噪
        if self.use_dns:
            waveform = self.denoise(waveform)

        # AGC
        if self.use_agc:
            waveform = self.apply_agc(waveform)

        return waveform, self.sample_rate
```

### 3.2 Pyannote 参数优化

```python
"""
Pyannote 3.1 参数优化 - 关键改进点
"""
from pyannote.audio import Pipeline
from pyannote.audio.pipelines import SpeakerDiarization
import torch

class OptimizedPyannote:
    """优化的 Pyannote 分离器"""

    def __init__(self,
                 hf_token: str,
                 device: str = "cuda"):

        # 加载 pipeline
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        self.pipeline.to(torch.device(device))

        # 优化参数 (关键!)
        self._optimize_parameters()

    def _optimize_parameters(self):
        """参数优化 - 提升分离准确性的关键"""

        # 1. 分割模型阈值优化
        # 降低阈值可以检测到更多说话人边界，但可能引入误检
        self.pipeline._segmentation.threshold = 0.4  # 默认 0.5

        # 2. 最小片段长度 (秒)
        # 降低可以保留更多短片段，但增加计算量
        self.pipeline._segmentation.min_duration_on = 0.1  # 默认 0.1
        self.pipeline._segmentation.min_duration_off = 0.1  # 默认 0.1

        # 3. 聚类阈值优化
        # 这是影响"同人判异人"和"异人判同人"的关键参数
        # 较高阈值 -> 更容易合并 (异人判同人)
        # 较低阈值 -> 更容易分开 (同人判异人)
        # 需要根据实际场景调整
        self.pipeline._clustering.threshold = 0.7  # 默认 0.7, 范围 0.5-0.9

        # 4. 嵌入聚合方式
        self.pipeline._embedding.window = "sliding"
        self.pipeline._embedding.duration = 3.0  # 嵌入窗口长度
        self.pipeline._embedding.step = 0.5  # 滑动步长

    def diarize(self,
                audio_path: str,
                num_speakers: int = None,
                min_speakers: int = None,
                max_speakers: int = None) -> dict:
        """
        执行分离

        优化技巧:
        1. 如果知道说话人数量，务必指定 num_speakers
        2. 否则至少指定 min_speakers 和 max_speakers 范围
        """
        kwargs = {}

        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers
        else:
            if min_speakers is not None:
                kwargs["min_speakers"] = min_speakers
            if max_speakers is not None:
                kwargs["max_speakers"] = max_speakers

        # 执行分离
        diarization = self.pipeline(audio_path, **kwargs)

        # 转换为字典格式
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker,
                "duration": turn.end - turn.start
            })

        return {
            "segments": segments,
            "speakers": list(set(s["speaker"] for s in segments))
        }


class PyannoteParameterTuner:
    """Pyannote 参数调优器 - 用于找到最佳参数"""

    @staticmethod
    def get_recommended_params(scenario: str) -> dict:
        """
        根据场景获取推荐参数

        场景类型:
        - meeting: 会议场景 (多人讨论，可能有重叠)
        - interview: 采访场景 (通常 2 人，少重叠)
        - call_center: 呼叫中心 (2 人，电话质量)
        - podcast: 播客场景 (2-3 人，高质量音频)
        - noisy: 噪声环境 (背景噪声大)
        """
        params = {
            "meeting": {
                "segmentation_threshold": 0.35,  # 更敏感的边界检测
                "clustering_threshold": 0.65,    # 更严格的聚类
                "min_duration_on": 0.1,
                "min_duration_off": 0.1,
                "embedding_duration": 3.0,
            },
            "interview": {
                "segmentation_threshold": 0.45,
                "clustering_threshold": 0.75,
                "min_duration_on": 0.2,
                "min_duration_off": 0.2,
                "embedding_duration": 4.0,
            },
            "call_center": {
                "segmentation_threshold": 0.4,
                "clustering_threshold": 0.7,
                "min_duration_on": 0.15,
                "min_duration_off": 0.15,
                "embedding_duration": 3.5,
            },
            "podcast": {
                "segmentation_threshold": 0.5,
                "clustering_threshold": 0.8,
                "min_duration_on": 0.3,
                "min_duration_off": 0.3,
                "embedding_duration": 5.0,
            },
            "noisy": {
                "segmentation_threshold": 0.3,   # 噪声环境需要更敏感
                "clustering_threshold": 0.6,     # 但聚类要更严格
                "min_duration_on": 0.2,
                "min_duration_off": 0.2,
                "embedding_duration": 4.0,
            }
        }

        return params.get(scenario, params["meeting"])
```

### 3.3 多嵌入融合

```python
"""
多嵌入融合模块 - 提升嵌入区分度和鲁棒性
"""
import torch
import torch.nn as nn
from speechbrain.pretrained import EncoderClassifier
from transformers import WavLMModel, Wav2Vec2FeatureExtractor
import numpy as np

class MultiEmbeddingExtractor:
    """多模型嵌入提取与融合"""

    def __init__(self, device: str = "cuda"):
        self.device = device
        self._load_models()

    def _load_models(self):
        """加载多个嵌入模型"""

        # 1. ECAPA-TDNN (SpeechBrain) - 主模型
        self.ecapa = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="pretrained_models/ecapa",
            run_opts={"device": self.device}
        )

        # 2. TitaNet (如果可用) - 噪声鲁棒
        try:
            import nemo.collections.asr as nemo_asr
            self.titanet = nemo_asr.models.EncDecSpeakerLabelModel.from_pretrained(
                "nvidia/speakerverification_en_titanet_large"
            )
            self.titanet.eval()
            self.titanet.to(self.device)
            self.has_titanet = True
        except:
            self.has_titanet = False

        # 3. WavLM - 自监督特征
        self.wavlm_processor = Wav2Vec2FeatureExtractor.from_pretrained(
            "microsoft/wavlm-base-plus-sv"
        )
        self.wavlm = WavLMModel.from_pretrained(
            "microsoft/wavlm-base-plus-sv"
        ).to(self.device)
        self.wavlm.eval()

        # 融合网络
        self.fusion_layer = self._build_fusion_layer()

    def _build_fusion_layer(self) -> nn.Module:
        """构建嵌入融合层"""
        # 各模型嵌入维度
        ecapa_dim = 192
        titanet_dim = 192 if self.has_titanet else 0
        wavlm_dim = 768

        total_dim = ecapa_dim + titanet_dim + wavlm_dim

        # 注意力融合
        fusion = nn.Sequential(
            nn.Linear(total_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(512, 256),
            nn.LayerNorm(256)
        ).to(self.device)

        return fusion

    def extract_ecapa(self, waveform: torch.Tensor) -> torch.Tensor:
        """提取 ECAPA-TDNN 嵌入"""
        with torch.no_grad():
            embedding = self.ecapa.encode_batch(waveform.to(self.device))
        return embedding.squeeze()

    def extract_titanet(self, waveform: torch.Tensor) -> torch.Tensor:
        """提取 TitaNet 嵌入"""
        if not self.has_titanet:
            return None

        with torch.no_grad():
            # TitaNet 需要特定的输入格式
            _, embedding = self.titanet.forward(
                input_signal=waveform.to(self.device),
                input_signal_length=torch.tensor([waveform.shape[-1]])
            )
        return embedding.squeeze()

    def extract_wavlm(self, waveform: torch.Tensor, sr: int = 16000) -> torch.Tensor:
        """提取 WavLM 嵌入"""
        with torch.no_grad():
            inputs = self.wavlm_processor(
                waveform.squeeze().numpy(),
                sampling_rate=sr,
                return_tensors="pt"
            )
            outputs = self.wavlm(inputs.input_values.to(self.device))
            # 使用最后一层的均值作为嵌入
            embedding = outputs.last_hidden_state.mean(dim=1)
        return embedding.squeeze()

    def extract_fused(self, waveform: torch.Tensor, sr: int = 16000) -> torch.Tensor:
        """
        提取融合嵌入

        这是 v3 的核心改进：通过多模型融合提升鲁棒性
        """
        embeddings = []

        # ECAPA
        ecapa_emb = self.extract_ecapa(waveform)
        embeddings.append(ecapa_emb)

        # TitaNet (如果可用)
        if self.has_titanet:
            titanet_emb = self.extract_titanet(waveform)
            embeddings.append(titanet_emb)

        # WavLM
        wavlm_emb = self.extract_wavlm(waveform, sr)
        embeddings.append(wavlm_emb)

        # 拼接
        combined = torch.cat(embeddings, dim=-1)

        # 融合
        with torch.no_grad():
            fused = self.fusion_layer(combined)

        return fused

    def compute_similarity(self,
                          emb1: torch.Tensor,
                          emb2: torch.Tensor) -> float:
        """计算嵌入相似度"""
        # 余弦相似度
        emb1_norm = emb1 / (emb1.norm() + 1e-8)
        emb2_norm = emb2 / (emb2.norm() + 1e-8)
        similarity = torch.dot(emb1_norm, emb2_norm).item()
        return similarity
```

### 3.4 精细化后处理

```python
"""
精细化后处理模块 - 修正分离错误
"""
import numpy as np
from scipy import signal
from scipy.ndimage import median_filter
from typing import List, Dict, Tuple
import torch

class DiarizationRefiner:
    """分离结果精细化处理器"""

    def __init__(self,
                 min_segment_duration: float = 0.3,
                 merge_threshold: float = 0.5,
                 embedding_extractor = None):
        self.min_segment_duration = min_segment_duration
        self.merge_threshold = merge_threshold
        self.embedding_extractor = embedding_extractor

    def smooth_boundaries(self,
                         segments: List[Dict],
                         audio_duration: float) -> List[Dict]:
        """
        边界平滑处理

        解决问题：边界抖动导致的碎片化分割
        """
        if len(segments) <= 1:
            return segments

        # 创建帧级标签 (10ms 分辨率)
        frame_rate = 100  # 每秒 100 帧
        n_frames = int(audio_duration * frame_rate)
        frame_labels = np.zeros(n_frames, dtype=int)

        # 创建说话人到索引的映射
        speakers = list(set(s["speaker"] for s in segments))
        speaker_to_idx = {spk: idx + 1 for idx, spk in enumerate(speakers)}

        # 填充帧标签
        for seg in segments:
            start_frame = int(seg["start"] * frame_rate)
            end_frame = int(seg["end"] * frame_rate)
            frame_labels[start_frame:end_frame] = speaker_to_idx[seg["speaker"]]

        # 中值滤波平滑 (窗口 30 帧 = 0.3 秒)
        smoothed = median_filter(frame_labels, size=30)

        # 重建片段
        refined_segments = []
        current_speaker = smoothed[0]
        current_start = 0

        for i, label in enumerate(smoothed):
            if label != current_speaker:
                if current_speaker > 0:  # 非静音
                    idx_to_speaker = {v: k for k, v in speaker_to_idx.items()}
                    refined_segments.append({
                        "start": current_start / frame_rate,
                        "end": i / frame_rate,
                        "speaker": idx_to_speaker[current_speaker],
                        "duration": (i - current_start) / frame_rate
                    })
                current_speaker = label
                current_start = i

        # 最后一个片段
        if current_speaker > 0:
            idx_to_speaker = {v: k for k, v in speaker_to_idx.items()}
            refined_segments.append({
                "start": current_start / frame_rate,
                "end": len(smoothed) / frame_rate,
                "speaker": idx_to_speaker[current_speaker],
                "duration": (len(smoothed) - current_start) / frame_rate
            })

        return refined_segments

    def merge_short_segments(self,
                            segments: List[Dict],
                            waveform: torch.Tensor = None,
                            sr: int = 16000) -> List[Dict]:
        """
        短片段合并

        解决问题：过短片段被错误分割
        策略：短片段根据嵌入相似度合并到相邻片段
        """
        if len(segments) <= 1:
            return segments

        refined = []
        i = 0

        while i < len(segments):
            seg = segments[i]

            if seg["duration"] < self.min_segment_duration:
                # 短片段处理
                if self.embedding_extractor and waveform is not None:
                    # 使用嵌入相似度决定合并方向
                    seg_audio = self._extract_segment_audio(
                        waveform, seg["start"], seg["end"], sr
                    )
                    seg_emb = self.embedding_extractor.extract_fused(seg_audio, sr)

                    best_match = None
                    best_sim = -1

                    # 检查前后相邻片段
                    for j in [i-1, i+1]:
                        if 0 <= j < len(segments):
                            neighbor = segments[j]
                            neighbor_audio = self._extract_segment_audio(
                                waveform, neighbor["start"], neighbor["end"], sr
                            )
                            neighbor_emb = self.embedding_extractor.extract_fused(
                                neighbor_audio, sr
                            )
                            sim = self.embedding_extractor.compute_similarity(
                                seg_emb, neighbor_emb
                            )
                            if sim > best_sim:
                                best_sim = sim
                                best_match = j

                    if best_match is not None and best_sim > self.merge_threshold:
                        # 合并到最相似的邻居
                        seg["speaker"] = segments[best_match]["speaker"]

                # 尝试与前一个片段合并
                if refined and refined[-1]["speaker"] == seg["speaker"]:
                    refined[-1]["end"] = seg["end"]
                    refined[-1]["duration"] = refined[-1]["end"] - refined[-1]["start"]
                else:
                    refined.append(seg)
            else:
                # 正常片段，检查是否可以与前一个合并
                if refined and refined[-1]["speaker"] == seg["speaker"]:
                    gap = seg["start"] - refined[-1]["end"]
                    if gap < 0.3:  # 间隔小于 0.3 秒则合并
                        refined[-1]["end"] = seg["end"]
                        refined[-1]["duration"] = refined[-1]["end"] - refined[-1]["start"]
                    else:
                        refined.append(seg)
                else:
                    refined.append(seg)

            i += 1

        return refined

    def _extract_segment_audio(self,
                               waveform: torch.Tensor,
                               start: float,
                               end: float,
                               sr: int) -> torch.Tensor:
        """提取片段音频"""
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        return waveform[:, start_sample:end_sample]

    def resegment_overlaps(self,
                          segments: List[Dict],
                          overlap_segments: List[Dict],
                          waveform: torch.Tensor,
                          sr: int,
                          separator = None) -> List[Dict]:
        """
        重叠段重新分割

        解决问题：重叠语音段分配不准
        策略：使用语音分离模型分离后重新分配
        """
        if separator is None or not overlap_segments:
            return segments

        for overlap in overlap_segments:
            # 提取重叠段音频
            overlap_audio = self._extract_segment_audio(
                waveform, overlap["start"], overlap["end"], sr
            )

            # 使用 SepFormer 分离
            separated = separator.separate(overlap_audio)

            # 为每个分离出的声音找到最匹配的说话人
            for sep_audio in separated:
                sep_emb = self.embedding_extractor.extract_fused(sep_audio, sr)

                best_speaker = None
                best_sim = -1

                # 与所有已知说话人比较
                for seg in segments:
                    if seg["start"] != overlap["start"]:  # 排除重叠段自身
                        seg_audio = self._extract_segment_audio(
                            waveform, seg["start"], seg["end"], sr
                        )
                        seg_emb = self.embedding_extractor.extract_fused(seg_audio, sr)
                        sim = self.embedding_extractor.compute_similarity(sep_emb, seg_emb)

                        if sim > best_sim:
                            best_sim = sim
                            best_speaker = seg["speaker"]

                if best_speaker:
                    # 添加分离出的片段
                    segments.append({
                        "start": overlap["start"],
                        "end": overlap["end"],
                        "speaker": best_speaker,
                        "duration": overlap["end"] - overlap["start"],
                        "is_overlap": True
                    })

        # 按时间排序
        segments.sort(key=lambda x: x["start"])

        return segments


class LLMPostProcessor:
    """
    LLM 后处理器 (可选)

    使用 LLM 进行语义一致性校正
    注意：需要先有 ASR 结果
    """

    def __init__(self, model_name: str = "Qwen/Qwen2.5-7B-Instruct"):
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, torch_dtype=torch.float16
            )
            self.available = True
        except:
            self.available = False

    def refine_with_context(self,
                           segments: List[Dict],
                           transcripts: List[str]) -> List[Dict]:
        """
        基于语义上下文优化分离结果

        注意：根据研究，零样本 LLM 可能产生幻觉。
        建议在有标注数据时微调，或仅用于明显错误的修正。
        """
        if not self.available or not transcripts:
            return segments

        # 构建上下文
        context = []
        for seg, text in zip(segments, transcripts):
            context.append(f"[{seg['speaker']}]: {text}")

        prompt = f"""分析以下对话，检查说话人分配是否合理。
如果发现明显的说话人分配错误（如同一句话被分给不同人），请指出。
只输出需要修正的行号和正确的说话人。

对话内容：
{chr(10).join(context)}

需要修正的内容（如果没有则输出"无需修正"）：
"""

        # 调用 LLM
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_new_tokens=200)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 解析响应并修正
        # (这里需要根据实际响应格式解析)

        return segments
```

### 3.5 NeMo MSDD 集成 (可选高精度方案)

```python
"""
NeMo MSDD 集成 - 多尺度分离解码器
可将 DER 降低最多 60%
"""

class NeMoMSDDDiarizer:
    """
    NVIDIA NeMo 多尺度分离解码器

    优势：
    - 多尺度动态权重
    - 内置重叠检测
    - 可处理任意数量说话人

    要求：
    - NVIDIA GPU
    - CUDA 11.x+
    - pip install nemo_toolkit[all]
    """

    def __init__(self, device: str = "cuda"):
        try:
            import nemo.collections.asr as nemo_asr
            from omegaconf import OmegaConf

            # 加载 VAD 模型 (MarbleNet)
            self.vad_model = nemo_asr.models.EncDecClassificationModel.from_pretrained(
                "nvidia/vad_marblenet"
            )

            # 加载嵌入模型 (TitaNet)
            self.speaker_model = nemo_asr.models.EncDecSpeakerLabelModel.from_pretrained(
                "nvidia/speakerverification_en_titanet_large"
            )

            # 加载 MSDD 模型
            self.msdd_model = nemo_asr.models.NeuralDiarizer.from_pretrained(
                "nvidia/diar_msdd_telephonic"
            )

            self.device = device
            self.available = True

        except ImportError:
            print("NeMo 未安装，MSDD 不可用")
            self.available = False

    def diarize(self,
                audio_path: str,
                num_speakers: int = None,
                max_speakers: int = 8) -> dict:
        """
        执行 MSDD 分离

        MSDD 工作原理：
        1. 多尺度片段提取 (不同时间尺度)
        2. TitaNet 提取各尺度嵌入
        3. 初始聚类提供说话人画像
        4. MSDD 解码器动态计算尺度权重
        5. 成对推理处理任意数量说话人
        """
        if not self.available:
            raise RuntimeError("NeMo MSDD 不可用")

        from omegaconf import OmegaConf

        # 配置
        config = OmegaConf.create({
            "diarizer": {
                "manifest_filepath": None,
                "out_dir": "/tmp/nemo_diar",
                "oracle_vad": False,
                "collar": 0.25,
                "ignore_overlap": False,
                "vad": {
                    "model_path": "nvidia/vad_marblenet",
                    "threshold": 0.5,
                    "pad_onset": 0.1,
                    "pad_offset": 0.1,
                },
                "speaker_embeddings": {
                    "model_path": "nvidia/speakerverification_en_titanet_large",
                    "window_length_in_sec": [1.5, 1.25, 1.0, 0.75, 0.5],  # 多尺度
                    "shift_length_in_sec": [0.75, 0.625, 0.5, 0.375, 0.25],
                },
                "clustering": {
                    "parameters": {
                        "max_num_speakers": max_speakers,
                    }
                },
                "msdd_model": {
                    "model_path": "nvidia/diar_msdd_telephonic",
                    "parameters": {
                        "sigmoid_threshold": [0.7],
                        "seq_eval_mode": True,
                    }
                }
            }
        })

        if num_speakers:
            config.diarizer.clustering.parameters.oracle_num_speakers = num_speakers

        # 执行分离
        self.msdd_model.diarize(
            config=config,
            audio_files=[audio_path]
        )

        # 解析结果
        # (根据 NeMo 输出格式解析)

        return {"segments": [], "speakers": []}
```

### 3.6 DiariZen 集成 (高说话人数场景)

```python
"""
DiariZen 集成 - 适用于 5+ 说话人场景
"""

class DiariZenDiarizer:
    """
    DiariZen 分离器

    优势：
    - 5+ 说话人场景 DER 仅 7.1%
    - 使用 WavLM 自监督特征
    - 两阶段 EEND-VC 方法

    要求：
    - pip install diarizen
    - pyannote-audio 3.1+
    """

    def __init__(self, device: str = "cuda"):
        try:
            # DiariZen 需要从 GitHub 安装
            # git clone https://github.com/BUTSpeechFIT/DiariZen
            # pip install -e .
            from diarizen import WavLMEENDVC

            self.model = WavLMEENDVC.from_pretrained()
            self.model.to(device)
            self.device = device
            self.available = True

        except ImportError:
            print("DiariZen 未安装")
            self.available = False

    def diarize(self,
                audio_path: str,
                num_speakers: int = None) -> dict:
        """
        执行 DiariZen 分离

        工作流程：
        1. EEND 模型在局部窗口内检测说话人活动
        2. 从每个窗口的每个说话人提取嵌入
        3. 聚类将局部身份映射到全局身份
        """
        if not self.available:
            raise RuntimeError("DiariZen 不可用")

        # 执行分离
        result = self.model(
            audio_path,
            num_speakers=num_speakers
        )

        return {
            "segments": result.segments,
            "speakers": result.speakers
        }
```

## 4. 完整 v3 Pipeline

```python
"""
v3 完整流水线 - 整合所有优化
"""
from dataclasses import dataclass
from typing import List, Optional
import torch

@dataclass
class DiarizationConfig:
    """分离配置"""
    # 预处理
    use_denoising: bool = True
    use_agc: bool = True

    # 分离器选择
    primary_diarizer: str = "pyannote"  # pyannote, nemo, diarizen
    use_ensemble: bool = False  # 是否使用多模型集成

    # Pyannote 参数
    pyannote_scenario: str = "meeting"  # meeting, interview, call_center, podcast, noisy

    # 嵌入
    use_multi_embedding: bool = True

    # 后处理
    use_boundary_smoothing: bool = True
    use_short_segment_merge: bool = True
    use_overlap_resegment: bool = True
    use_llm_postprocess: bool = False

    # 阈值
    min_segment_duration: float = 0.3
    merge_similarity_threshold: float = 0.6
    clustering_threshold: float = 0.7


class SpeakerDiarizationV3Pipeline:
    """v3 说话人分离完整流水线"""

    def __init__(self,
                 config: DiarizationConfig,
                 hf_token: str = None,
                 device: str = "cuda"):
        self.config = config
        self.device = device

        # 初始化组件
        self._init_components(hf_token)

    def _init_components(self, hf_token: str):
        """初始化所有组件"""

        # 1. 预处理器
        self.preprocessor = AudioPreprocessor(
            use_dns=self.config.use_denoising,
            use_agc=self.config.use_agc
        )

        # 2. 分离器
        if self.config.primary_diarizer == "pyannote":
            self.diarizer = OptimizedPyannote(hf_token, self.device)
            # 应用场景参数
            params = PyannoteParameterTuner.get_recommended_params(
                self.config.pyannote_scenario
            )
            self._apply_pyannote_params(params)
        elif self.config.primary_diarizer == "nemo":
            self.diarizer = NeMoMSDDDiarizer(self.device)
        elif self.config.primary_diarizer == "diarizen":
            self.diarizer = DiariZenDiarizer(self.device)

        # 3. 嵌入提取器
        if self.config.use_multi_embedding:
            self.embedding_extractor = MultiEmbeddingExtractor(self.device)

        # 4. 后处理器
        self.refiner = DiarizationRefiner(
            min_segment_duration=self.config.min_segment_duration,
            merge_threshold=self.config.merge_similarity_threshold,
            embedding_extractor=self.embedding_extractor if self.config.use_multi_embedding else None
        )

        # 5. LLM 后处理 (可选)
        if self.config.use_llm_postprocess:
            self.llm_processor = LLMPostProcessor()

    def _apply_pyannote_params(self, params: dict):
        """应用 Pyannote 参数"""
        if hasattr(self.diarizer, 'pipeline'):
            pipeline = self.diarizer.pipeline
            pipeline._segmentation.threshold = params["segmentation_threshold"]
            pipeline._clustering.threshold = params["clustering_threshold"]

    def process(self,
               audio_path: str,
               num_speakers: int = None,
               min_speakers: int = None,
               max_speakers: int = None) -> dict:
        """
        执行完整分离流程

        Returns:
            {
                "segments": [...],
                "speakers": [...],
                "processing_info": {...}
            }
        """
        processing_info = {}

        # 1. 预处理
        waveform, sr = self.preprocessor.process(audio_path)
        processing_info["preprocessed"] = True

        # 保存预处理后的音频用于后续处理
        preprocessed_path = "/tmp/preprocessed_audio.wav"
        import torchaudio
        torchaudio.save(preprocessed_path, waveform, sr)

        # 2. 分离
        result = self.diarizer.diarize(
            preprocessed_path,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        segments = result["segments"]
        processing_info["initial_segments"] = len(segments)

        # 3. 后处理
        audio_duration = waveform.shape[-1] / sr

        # 3.1 边界平滑
        if self.config.use_boundary_smoothing:
            segments = self.refiner.smooth_boundaries(segments, audio_duration)
            processing_info["after_smoothing"] = len(segments)

        # 3.2 短片段合并
        if self.config.use_short_segment_merge:
            segments = self.refiner.merge_short_segments(
                segments, waveform, sr
            )
            processing_info["after_merge"] = len(segments)

        # 3.3 重叠处理
        if self.config.use_overlap_resegment:
            # 检测重叠段
            overlap_segments = self._detect_overlaps(segments)
            if overlap_segments:
                segments = self.refiner.resegment_overlaps(
                    segments, overlap_segments, waveform, sr
                )
                processing_info["overlaps_processed"] = len(overlap_segments)

        return {
            "segments": segments,
            "speakers": list(set(s["speaker"] for s in segments)),
            "processing_info": processing_info
        }

    def _detect_overlaps(self, segments: List[dict]) -> List[dict]:
        """检测重叠段"""
        overlaps = []
        for i, seg1 in enumerate(segments):
            for seg2 in segments[i+1:]:
                # 检查是否重叠
                if seg1["start"] < seg2["end"] and seg2["start"] < seg1["end"]:
                    overlap_start = max(seg1["start"], seg2["start"])
                    overlap_end = min(seg1["end"], seg2["end"])
                    overlaps.append({
                        "start": overlap_start,
                        "end": overlap_end,
                        "speakers": [seg1["speaker"], seg2["speaker"]]
                    })
        return overlaps
```

## 5. 调优指南

### 5.1 场景化参数推荐

| 场景 | 分离阈值 | 聚类阈值 | 最小片段 | 嵌入窗口 | 推荐分离器 |
|------|---------|---------|---------|---------|-----------|
| 会议 (5+ 人) | 0.35 | 0.65 | 0.1s | 3.0s | DiariZen |
| 采访 (2 人) | 0.45 | 0.75 | 0.2s | 4.0s | Pyannote |
| 呼叫中心 | 0.40 | 0.70 | 0.15s | 3.5s | NeMo MSDD |
| 播客 | 0.50 | 0.80 | 0.3s | 5.0s | Pyannote |
| 噪声环境 | 0.30 | 0.60 | 0.2s | 4.0s | Pyannote + 降噪 |

### 5.2 问题诊断与解决

```
问题：同一说话人被分成多个
├── 原因1：嵌入对噪声敏感
│   └── 解决：启用预处理降噪，使用多嵌入融合
├── 原因2：聚类阈值过低
│   └── 解决：提高 clustering_threshold (0.7 -> 0.8)
└── 原因3：嵌入窗口太短
    └── 解决：增加 embedding_duration (3s -> 5s)

问题：不同说话人被合并
├── 原因1：声音相似度高
│   └── 解决：降低 clustering_threshold (0.7 -> 0.6)
├── 原因2：分割阈值过高
│   └── 解决：降低 segmentation_threshold (0.5 -> 0.4)
└── 原因3：嵌入区分度不足
    └── 解决：使用 TitaNet-Large 或多嵌入融合

问题：边界不准确
├── 原因1：分割模型精度
│   └── 解决：启用边界平滑后处理
├── 原因2：VAD 不准
│   └── 解决：使用 MarbleNet VAD
└── 原因3：最小片段约束
    └── 解决：调整 min_duration_on/off

问题：短片段丢失
├── 原因1：最小片段阈值过高
│   └── 解决：降低 min_segment_duration (0.3 -> 0.1)
└── 原因2：被错误合并
    └── 解决：启用短片段回溯匹配
```

### 5.3 性能优化建议

```python
# CPU 优化
config = DiarizationConfig(
    primary_diarizer="pyannote",  # CPU 友好
    use_multi_embedding=False,     # 减少计算
    use_denoising=False,           # 可选
    use_llm_postprocess=False,     # LLM 需要 GPU
)

# GPU 优化 (最佳精度)
config = DiarizationConfig(
    primary_diarizer="nemo",       # MSDD 最高精度
    use_ensemble=True,             # 多模型集成
    use_multi_embedding=True,      # 多嵌入融合
    use_denoising=True,
    use_overlap_resegment=True,
)

# 平衡方案
config = DiarizationConfig(
    primary_diarizer="pyannote",
    pyannote_scenario="meeting",
    use_multi_embedding=True,
    use_boundary_smoothing=True,
    use_short_segment_merge=True,
)
```

## 6. 部署配置

### 6.1 依赖安装

```bash
# 基础依赖
pip install torch torchaudio
pip install pyannote.audio==3.1.0
pip install speechbrain
pip install transformers

# 可选：NeMo (需要 NVIDIA GPU)
pip install nemo_toolkit[all]

# 可选：DiariZen
git clone https://github.com/BUTSpeechFIT/DiariZen
cd DiariZen && pip install -e .

# 可选：降噪模型
pip install DTLN
```

### 6.2 模型下载

```python
# Pyannote (需要 HuggingFace token)
from huggingface_hub import login
login(token="your_hf_token")

# 预下载模型
from pyannote.audio import Pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=True
)

# SpeechBrain ECAPA-TDNN
from speechbrain.pretrained import EncoderClassifier
encoder = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb"
)
```

## 7. 预期效果

| 指标 | v2 方案 | v3 方案 (预期) | 提升 |
|------|---------|---------------|------|
| DER (会议场景) | ~15% | ~8-10% | 33-47% |
| DER (噪声环境) | ~20% | ~12-15% | 25-40% |
| 边界准确性 | 一般 | 良好 | - |
| 短片段召回 | 60% | 85% | 42% |
| 重叠处理 | 差 | 良好 | - |

## 8. 参考资料

- [Pyannote 官方文档](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [DiariZen GitHub](https://github.com/BUTSpeechFIT/DiariZen)
- [NeMo MSDD 文档](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_diarization/models.html)
- [SpeakerLM 论文](https://arxiv.org/abs/2508.06372)
- [DiarizationLM 论文](https://arxiv.org/abs/2401.03506)
- [2025 Speaker Diarization 技术指南](https://www.marktechpost.com/2025/08/21/what-is-speaker-diarization-a-2025-technical-guide/)

---

文档版本: v3.0
更新时间: 2025-12-03
作者: Claude Code
