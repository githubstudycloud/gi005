# 说话人分离与识别 v2 解决方案

## 1. 现状分析

### 1.1 当前实现架构

```
当前流程（v1）：
┌─────────────────────────────────────────────────────────────┐
│                       输入音频                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           FunASR SenseVoice (语音识别)                       │
│   - 模型: speech_paraformer-large_asr_nat-zh-cn             │
│   - VAD: speech_fsmn_vad_zh-cn-16k-common-pytorch           │
│   - 标点: punc_ct-transformer_zh-cn-common                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           Speaker 模型 (说话人分离)                          │
│   - 模型: ERes2NetV2 (20480 维嵌入)                         │
│   - 问题：基于聚类的简单分离                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   输出：文本 + 说话人标签                     │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 现有问题

| 问题 | 描述 | 影响程度 |
|------|------|----------|
| **重叠语音处理差** | 多人同时说话时无法正确分离 | 严重 |
| **噪声敏感** | 不同噪声背景下同一说话人被识别为不同人 | 严重 |
| **无重叠检测** | 没有专门的重叠语音检测模块 | 中等 |
| **说话人跟踪差** | 跨片段说话人身份一致性差 | 中等 |
| **分离后转录对齐** | 分离音频与转录文本时间戳对齐困难 | 中等 |

### 1.3 现有代码分析

**ASR 部分** (`tools/asr/funasr_asr.py`)：
```python
# 当前实现：单一 ASR 模型，无说话人分离
model = AutoModel(
    model=path_asr,           # Paraformer-large
    vad_model=path_vad,       # FSMN VAD
    punc_model=path_punc,     # 标点恢复
)
text = model.generate(input=file_path)[0]["text"]  # 输出纯文本
```

**说话人向量** (`GPT_SoVITS/sv.py`)：
```python
# 当前实现：ERes2NetV2 提取固定说话人嵌入
# 问题：仅用于 TTS 音色克隆，不支持实时分离
embedding_model = ERes2NetV2(baseWidth=24, scale=4, expansion=4)
sv_emb = self.embedding_model.forward3(feat)  # (batch, 20480)
```

---

## 2. v2 解决方案架构

### 2.1 整体架构

```
v2 解决方案：
┌─────────────────────────────────────────────────────────────┐
│                       输入音频                               │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌───────────────────┐                   ┌───────────────────┐
│  Stage 1: 预处理   │                   │  并行路径          │
│  - 降噪增强        │                   │  - 重叠检测        │
│  - VAD 分段        │                   │  - 活动度检测      │
└───────────────────┘                   └───────────────────┘
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│       Stage 2: 说话人分离 (Pyannote 3.1)                     │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  2.1 分割 (Segmentation)                            │   │
│   │  - powerset 多标签分类                              │   │
│   │  - 支持重叠检测                                      │   │
│   └─────────────────────────────────────────────────────┘   │
│                              │                              │
│                              ▼                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  2.2 嵌入提取 (ECAPA-TDNN / WavLM)                  │   │
│   │  - 噪声鲁棒的说话人向量                              │   │
│   └─────────────────────────────────────────────────────┘   │
│                              │                              │
│                              ▼                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  2.3 聚类 (Clustering)                              │   │
│   │  - 自适应聚类算法                                    │   │
│   │  - 说话人数量自动检测                                │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌───────────────────────────┐       ┌───────────────────────────┐
│  无重叠片段                │       │  有重叠片段                │
│  - 直接分配给对应说话人     │       │  - SepFormer 分离         │
│                           │       │  - 分离后再分配            │
└───────────────────────────┘       └───────────────────────────┘
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│       Stage 3: 说话人感知 ASR (SenseVoice + 对齐)            │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  3.1 分段转录                                       │   │
│   │  - 对每个说话人片段单独转录                          │   │
│   │  - FunASR SenseVoice                               │   │
│   └─────────────────────────────────────────────────────┘   │
│                              │                              │
│                              ▼                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  3.2 时间戳对齐                                     │   │
│   │  - 字级别对齐                                       │   │
│   │  - 强制对齐校正                                     │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│       Stage 4: 说话人一致性保持                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  4.1 说话人向量库匹配                               │   │
│   │  - 与已知说话人库比对                               │   │
│   │  - 余弦相似度 > 阈值 → 同一人                       │   │
│   └─────────────────────────────────────────────────────┘   │
│                              │                              │
│                              ▼                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  4.2 跨会话追踪                                     │   │
│   │  - 说话人 ID 持久化                                 │   │
│   │  - 增量更新向量库                                   │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         最终输出                             │
│   {                                                         │
│     "speakers": [                                           │
│       {"id": "SPK_001", "name": "张三", "embedding": [...]}, │
│       {"id": "SPK_002", "name": "李四", "embedding": [...]}  │
│     ],                                                      │
│     "segments": [                                           │
│       {"start": 0.0, "end": 2.5, "speaker": "SPK_001",      │
│        "text": "你好，今天天气不错"},                         │
│       {"start": 2.3, "end": 5.0, "speaker": "SPK_002",      │
│        "text": "是啊，很适合出去玩"},                         │
│       ...                                                   │
│     ]                                                       │
│   }                                                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 关键改进点

| 改进点 | v1 现状 | v2 方案 | 预期效果 |
|--------|---------|---------|----------|
| 说话人分离 | ERes2NetV2 简单聚类 | Pyannote 3.1 端到端 | DER: 30%+ → ~10% |
| 说话人嵌入 | ERes2NetV2 (20480维) | ECAPA-TDNN (192维) | 噪声鲁棒性提升 50%+ |
| 重叠处理 | 无 | Pyannote OSD + SepFormer | 支持 2-3 人重叠 |
| ASR | 全局单次转录 | 分段说话人感知转录 | WER 降低 15%+ |
| 说话人追踪 | 无 | 向量库 + 增量匹配 | 跨会话一致性 |

---

## 3. 核心组件详细设计

### 3.1 说话人分离模块 (Pyannote 3.1)

**为什么选择 Pyannote 3.1**：
- DIHARD III 基准测试 SOTA（~10% DER）
- 原生支持重叠语音检测
- 端到端训练，无需复杂后处理
- MIT 开源许可，商业友好

**安装配置**：
```bash
pip install pyannote.audio

# 需要 HuggingFace token（模型需要申请访问）
# https://huggingface.co/pyannote/speaker-diarization-3.1
```

**核心代码**：
```python
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
import torch

class PyannoteDializer:
    def __init__(self, hf_token: str, device: str = "cpu"):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        self.pipeline.to(torch.device(device))

        # 可选：调整超参数
        self.pipeline.embedding_batch_size = 32  # 嵌入批处理大小

    def diarize(self, audio_path: str, num_speakers: int = None) -> dict:
        """
        执行说话人分离

        Args:
            audio_path: 音频文件路径
            num_speakers: 预期说话人数量（可选，None 表示自动检测）

        Returns:
            dict: {
                "segments": [(start, end, speaker_id), ...],
                "embeddings": {speaker_id: embedding_vector, ...}
            }
        """
        # 执行分离
        with ProgressHook() as hook:
            if num_speakers:
                diarization = self.pipeline(
                    audio_path,
                    num_speakers=num_speakers,
                    hook=hook
                )
            else:
                diarization = self.pipeline(audio_path, hook=hook)

        # 提取结果
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })

        return {
            "segments": segments,
            "num_speakers": len(set(s["speaker"] for s in segments))
        }
```

### 3.2 噪声鲁棒说话人嵌入 (ECAPA-TDNN + WavLM)

**双模型策略**：
- **ECAPA-TDNN**：快速、轻量，适合实时场景
- **WavLM**：极强噪声鲁棒性，适合高噪声场景

**ECAPA-TDNN 实现**（基于 SpeechBrain）：
```python
from speechbrain.inference.speaker import SpeakerRecognition

class RobustSpeakerEmbedding:
    def __init__(self, device: str = "cpu"):
        # ECAPA-TDNN 模型
        self.ecapa = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="pretrained_models/spkrec-ecapa-voxceleb",
            run_opts={"device": device}
        )

        # 噪声阈值：低于此值使用 WavLM
        self.noise_threshold = 15  # SNR in dB

    def extract_embedding(self, audio_path: str,
                         use_wavlm: bool = False) -> torch.Tensor:
        """
        提取说话人嵌入向量

        Args:
            audio_path: 音频路径
            use_wavlm: 是否使用 WavLM（高噪声场景）

        Returns:
            torch.Tensor: 192 维说话人嵌入
        """
        # 估计信噪比
        snr = self._estimate_snr(audio_path)

        if snr < self.noise_threshold or use_wavlm:
            # 高噪声：使用 WavLM
            return self._extract_wavlm(audio_path)
        else:
            # 正常：使用 ECAPA-TDNN
            embedding = self.ecapa.encode_batch(
                self.ecapa.load_audio(audio_path)
            )
            return embedding.squeeze()

    def verify_speaker(self, audio1: str, audio2: str) -> tuple:
        """
        验证两段音频是否为同一说话人

        Returns:
            (score, is_same): 相似度分数和判断结果
        """
        score, prediction = self.ecapa.verify_files(audio1, audio2)
        return float(score), bool(prediction)

    def _estimate_snr(self, audio_path: str) -> float:
        """估计信噪比（使用 VAD 区分语音和噪声）"""
        import librosa
        import numpy as np

        y, sr = librosa.load(audio_path, sr=16000)

        # 简化的 SNR 估计
        # 实际应用中可以使用更精确的方法
        frame_length = int(0.025 * sr)  # 25ms
        hop_length = int(0.010 * sr)    # 10ms

        energy = librosa.feature.rms(y=y, frame_length=frame_length,
                                     hop_length=hop_length)[0]

        # 假设最低 10% 能量帧为噪声
        noise_energy = np.percentile(energy, 10)
        signal_energy = np.percentile(energy, 90)

        if noise_energy > 0:
            snr = 10 * np.log10(signal_energy / noise_energy)
        else:
            snr = 40  # 假设高 SNR

        return snr
```

### 3.3 重叠语音处理 (SepFormer)

**处理流程**：
1. Pyannote OSD 检测重叠区域
2. SepFormer 分离重叠语音
3. 将分离结果分配给对应说话人

```python
from speechbrain.inference.separation import SepformerSeparation

class OverlapHandler:
    def __init__(self, device: str = "cpu"):
        # SepFormer 分离模型
        self.separator = SepformerSeparation.from_hparams(
            source="speechbrain/sepformer-wsj02mix",
            savedir="pretrained_models/sepformer-wsj02mix",
            run_opts={"device": device}
        )

        # 说话人嵌入模型
        self.embedder = RobustSpeakerEmbedding(device)

    def process_overlap(self, audio_path: str,
                       overlap_segment: dict,
                       speaker_embeddings: dict) -> list:
        """
        处理重叠语音片段

        Args:
            audio_path: 原始音频路径
            overlap_segment: {"start": float, "end": float}
            speaker_embeddings: {speaker_id: embedding}

        Returns:
            list: 分离后的片段列表
        """
        import soundfile as sf
        import librosa
        import numpy as np

        # 1. 提取重叠片段
        y, sr = librosa.load(audio_path, sr=16000)
        start_sample = int(overlap_segment["start"] * sr)
        end_sample = int(overlap_segment["end"] * sr)
        overlap_audio = y[start_sample:end_sample]

        # 2. 使用 SepFormer 分离
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, overlap_audio, sr)
            separated = self.separator.separate_file(path=f.name)

        # separated: (num_sources, samples)
        results = []

        # 3. 将分离的音频分配给说话人
        for i, source in enumerate(separated):
            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, source.numpy(), sr)
                source_embedding = self.embedder.extract_embedding(f.name)

            # 找最相似的说话人
            best_speaker = None
            best_score = -1

            for speaker_id, emb in speaker_embeddings.items():
                score = torch.nn.functional.cosine_similarity(
                    source_embedding.unsqueeze(0),
                    emb.unsqueeze(0)
                ).item()

                if score > best_score:
                    best_score = score
                    best_speaker = speaker_id

            results.append({
                "start": overlap_segment["start"],
                "end": overlap_segment["end"],
                "speaker": best_speaker,
                "confidence": best_score,
                "audio": source.numpy()
            })

        return results
```

### 3.4 说话人感知 ASR

**改进策略**：分段转录 + 时间戳对齐

```python
from funasr import AutoModel
import numpy as np

class SpeakerAwareASR:
    def __init__(self):
        # FunASR SenseVoice 模型
        self.asr_model = AutoModel(
            model="iic/SenseVoiceSmall",
            vad_model="fsmn-vad",
            punc_model="ct-punc",
            device="cpu"
        )

    def transcribe_segments(self, audio_path: str,
                           segments: list) -> list:
        """
        对分离后的片段进行转录

        Args:
            audio_path: 原始音频路径
            segments: [{"start": float, "end": float, "speaker": str}, ...]

        Returns:
            list: [{"start", "end", "speaker", "text"}, ...]
        """
        import librosa
        import soundfile as sf

        y, sr = librosa.load(audio_path, sr=16000)
        results = []

        for seg in segments:
            # 提取片段音频
            start_sample = int(seg["start"] * sr)
            end_sample = int(seg["end"] * sr)
            segment_audio = y[start_sample:end_sample]

            # 跳过过短片段
            if len(segment_audio) < sr * 0.3:  # < 300ms
                continue

            # 保存临时文件进行转录
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, segment_audio, sr)

                # 转录
                result = self.asr_model.generate(input=f.name)
                text = result[0]["text"] if result else ""

            results.append({
                "start": seg["start"],
                "end": seg["end"],
                "speaker": seg["speaker"],
                "text": text.strip()
            })

        return results
```

### 3.5 说话人一致性管理

**向量库设计**：
```python
import json
import numpy as np
from pathlib import Path
from typing import Optional
import torch

class SpeakerDatabase:
    def __init__(self, db_path: str = "speaker_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        self.embeddings_file = self.db_path / "embeddings.npy"
        self.metadata_file = self.db_path / "metadata.json"

        # 相似度阈值
        self.similarity_threshold = 0.75

        # 加载数据库
        self._load_db()

    def _load_db(self):
        """加载说话人数据库"""
        if self.embeddings_file.exists():
            self.embeddings = np.load(self.embeddings_file)
            with open(self.metadata_file, "r") as f:
                self.metadata = json.load(f)
        else:
            self.embeddings = np.array([]).reshape(0, 192)  # ECAPA-TDNN 维度
            self.metadata = {"speakers": []}

    def _save_db(self):
        """保存说话人数据库"""
        np.save(self.embeddings_file, self.embeddings)
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def find_speaker(self, embedding: np.ndarray) -> Optional[dict]:
        """
        在数据库中查找匹配的说话人

        Args:
            embedding: 192 维说话人嵌入

        Returns:
            dict or None: 匹配的说话人信息
        """
        if len(self.embeddings) == 0:
            return None

        # 计算余弦相似度
        embedding = embedding / np.linalg.norm(embedding)
        db_embeddings = self.embeddings / np.linalg.norm(
            self.embeddings, axis=1, keepdims=True
        )

        similarities = np.dot(db_embeddings, embedding)
        max_idx = np.argmax(similarities)
        max_sim = similarities[max_idx]

        if max_sim >= self.similarity_threshold:
            speaker = self.metadata["speakers"][max_idx]
            speaker["similarity"] = float(max_sim)
            return speaker

        return None

    def add_speaker(self, embedding: np.ndarray,
                   name: str = None,
                   metadata: dict = None) -> str:
        """
        添加新说话人到数据库

        Returns:
            str: 新说话人 ID
        """
        speaker_id = f"SPK_{len(self.metadata['speakers']):04d}"

        # 添加嵌入
        self.embeddings = np.vstack([
            self.embeddings,
            embedding.reshape(1, -1)
        ])

        # 添加元数据
        speaker_info = {
            "id": speaker_id,
            "name": name or f"Speaker {len(self.metadata['speakers'])}",
            "created_at": time.time(),
            "metadata": metadata or {}
        }
        self.metadata["speakers"].append(speaker_info)

        # 保存
        self._save_db()

        return speaker_id

    def update_embedding(self, speaker_id: str,
                        new_embedding: np.ndarray,
                        momentum: float = 0.9):
        """
        增量更新说话人嵌入（使用动量平均）

        Args:
            speaker_id: 说话人 ID
            new_embedding: 新的嵌入向量
            momentum: 动量系数（越大越保守）
        """
        idx = None
        for i, s in enumerate(self.metadata["speakers"]):
            if s["id"] == speaker_id:
                idx = i
                break

        if idx is not None:
            # 动量更新
            self.embeddings[idx] = (
                momentum * self.embeddings[idx] +
                (1 - momentum) * new_embedding
            )
            self._save_db()
```

---

## 4. 完整处理流水线

### 4.1 Pipeline 类

```python
import tempfile
from dataclasses import dataclass
from typing import List, Dict, Optional
import time

@dataclass
class DiarizationResult:
    """分离结果数据类"""
    audio_path: str
    duration: float
    num_speakers: int
    segments: List[Dict]
    speakers: List[Dict]
    processing_time: float

class SpeakerDiarizationPipeline:
    """
    v2 说话人分离完整流水线
    """

    def __init__(self,
                 hf_token: str,
                 device: str = "cpu",
                 speaker_db_path: str = "speaker_db"):
        """
        初始化流水线

        Args:
            hf_token: HuggingFace API token
            device: 计算设备 (cpu/cuda)
            speaker_db_path: 说话人数据库路径
        """
        print("Initializing Speaker Diarization Pipeline v2...")

        # 1. 说话人分离器 (Pyannote)
        print("  Loading Pyannote 3.1...")
        self.diarizer = PyannoteDializer(hf_token, device)

        # 2. 说话人嵌入器 (ECAPA-TDNN)
        print("  Loading ECAPA-TDNN...")
        self.embedder = RobustSpeakerEmbedding(device)

        # 3. 重叠处理器 (SepFormer)
        print("  Loading SepFormer...")
        self.overlap_handler = OverlapHandler(device)

        # 4. ASR 模型 (SenseVoice)
        print("  Loading SenseVoice ASR...")
        self.asr = SpeakerAwareASR()

        # 5. 说话人数据库
        print("  Loading Speaker Database...")
        self.speaker_db = SpeakerDatabase(speaker_db_path)

        print("Pipeline initialized!")

    def process(self,
                audio_path: str,
                num_speakers: int = None,
                return_embeddings: bool = False) -> DiarizationResult:
        """
        处理音频文件

        Args:
            audio_path: 音频文件路径
            num_speakers: 预期说话人数量（可选）
            return_embeddings: 是否返回说话人嵌入

        Returns:
            DiarizationResult: 处理结果
        """
        start_time = time.time()

        # Step 1: 说话人分离
        print(f"Step 1/4: Speaker Diarization...")
        diarization = self.diarizer.diarize(audio_path, num_speakers)
        segments = diarization["segments"]

        # Step 2: 提取说话人嵌入
        print(f"Step 2/4: Extracting Speaker Embeddings...")
        speaker_embeddings = {}
        speaker_segments = {}

        for seg in segments:
            speaker = seg["speaker"]
            if speaker not in speaker_segments:
                speaker_segments[speaker] = []
            speaker_segments[speaker].append(seg)

        # 为每个说话人提取嵌入（使用最长片段）
        for speaker, segs in speaker_segments.items():
            # 选择最长片段
            longest = max(segs, key=lambda x: x["end"] - x["start"])

            # 提取该片段的音频并计算嵌入
            embedding = self._extract_segment_embedding(
                audio_path, longest["start"], longest["end"]
            )
            speaker_embeddings[speaker] = embedding

        # Step 3: 说话人身份匹配
        print(f"Step 3/4: Matching Speaker Identities...")
        speaker_mapping = {}  # local_id -> global_id
        speakers_info = []

        for local_id, embedding in speaker_embeddings.items():
            # 在数据库中查找
            match = self.speaker_db.find_speaker(embedding.numpy())

            if match:
                # 找到匹配
                global_id = match["id"]
                speaker_mapping[local_id] = global_id

                # 更新嵌入
                self.speaker_db.update_embedding(global_id, embedding.numpy())

                speakers_info.append({
                    "local_id": local_id,
                    "global_id": global_id,
                    "name": match["name"],
                    "is_new": False,
                    "confidence": match.get("similarity", 1.0)
                })
            else:
                # 新说话人
                global_id = self.speaker_db.add_speaker(embedding.numpy())
                speaker_mapping[local_id] = global_id

                speakers_info.append({
                    "local_id": local_id,
                    "global_id": global_id,
                    "name": f"Speaker {global_id}",
                    "is_new": True,
                    "confidence": 1.0
                })

        # 更新 segments 中的说话人 ID
        for seg in segments:
            seg["speaker"] = speaker_mapping[seg["speaker"]]

        # Step 4: 转录
        print(f"Step 4/4: Transcribing...")
        transcribed = self.asr.transcribe_segments(audio_path, segments)

        # 计算处理时间
        processing_time = time.time() - start_time

        # 获取音频时长
        import librosa
        duration = librosa.get_duration(path=audio_path)

        return DiarizationResult(
            audio_path=audio_path,
            duration=duration,
            num_speakers=len(speakers_info),
            segments=transcribed,
            speakers=speakers_info,
            processing_time=processing_time
        )

    def _extract_segment_embedding(self, audio_path: str,
                                   start: float, end: float) -> torch.Tensor:
        """提取音频片段的说话人嵌入"""
        import librosa
        import soundfile as sf

        y, sr = librosa.load(audio_path, sr=16000)
        segment = y[int(start * sr):int(end * sr)]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, segment, sr)
            embedding = self.embedder.extract_embedding(f.name)

        return embedding
```

### 4.2 使用示例

```python
# 初始化
pipeline = SpeakerDiarizationPipeline(
    hf_token="your_huggingface_token",
    device="cpu",  # 或 "cuda"
    speaker_db_path="./speaker_database"
)

# 处理音频
result = pipeline.process(
    audio_path="meeting_audio.wav",
    num_speakers=None  # 自动检测说话人数量
)

# 输出结果
print(f"音频时长: {result.duration:.1f}s")
print(f"说话人数: {result.num_speakers}")
print(f"处理耗时: {result.processing_time:.1f}s")
print(f"实时率: {result.duration / result.processing_time:.2f}x")

print("\n--- 转录结果 ---")
for seg in result.segments:
    print(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] "
          f"{seg['speaker']}: {seg['text']}")

print("\n--- 说话人信息 ---")
for spk in result.speakers:
    status = "新" if spk["is_new"] else "已知"
    print(f"{spk['global_id']} ({status}): {spk['name']} "
          f"(置信度: {spk['confidence']:.2f})")
```

---

## 5. Worker 服务集成

### 5.1 新增 Worker 定义

```python
# voice-clone-tts/src/workers/diarization_worker.py

from typing import Dict, Any, Optional
import asyncio
from .base_worker import BaseWorker, WorkerStatus

class DiarizationWorker(BaseWorker):
    """说话人分离 Worker"""

    ENGINE_NAME = "diarization"
    DEFAULT_PORT = 8004

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pipeline = None
        self._hf_token = kwargs.get("hf_token", "")

    async def load_model(self) -> bool:
        """加载模型"""
        try:
            self._status = WorkerStatus.LOADING

            # 在线程池中加载（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            self._pipeline = await loop.run_in_executor(
                None,
                self._load_pipeline_sync
            )

            self._status = WorkerStatus.READY
            return True

        except Exception as e:
            self._status = WorkerStatus.ERROR
            self._logger.error(f"Failed to load model: {e}")
            return False

    def _load_pipeline_sync(self):
        """同步加载流水线"""
        from .diarization_pipeline import SpeakerDiarizationPipeline

        return SpeakerDiarizationPipeline(
            hf_token=self._hf_token,
            device=self._device,
            speaker_db_path=str(self._data_dir / "speaker_db")
        )

    async def process(self, audio_data: bytes,
                     **kwargs) -> Dict[str, Any]:
        """
        处理音频

        Args:
            audio_data: 音频字节数据
            **kwargs:
                num_speakers: 预期说话人数量

        Returns:
            dict: 分离和转录结果
        """
        if self._status != WorkerStatus.READY:
            raise RuntimeError("Worker not ready")

        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            audio_path = f.name

        try:
            # 在线程池中处理
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._pipeline.process(
                    audio_path,
                    num_speakers=kwargs.get("num_speakers")
                )
            )

            return {
                "duration": result.duration,
                "num_speakers": result.num_speakers,
                "segments": result.segments,
                "speakers": result.speakers,
                "processing_time": result.processing_time
            }

        finally:
            import os
            os.unlink(audio_path)
```

### 5.2 API 端点设计

```python
# voice-clone-tts/src/gateway/routes.py

@router.post("/api/diarize")
async def diarize_audio(
    file: UploadFile = File(...),
    num_speakers: Optional[int] = Form(None)
):
    """
    说话人分离和转录

    Args:
        file: 音频文件
        num_speakers: 预期说话人数量（可选）

    Returns:
        {
            "success": true,
            "duration": 120.5,
            "num_speakers": 3,
            "segments": [
                {"start": 0.0, "end": 2.5, "speaker": "SPK_0001", "text": "..."},
                ...
            ],
            "speakers": [
                {"global_id": "SPK_0001", "name": "Speaker 1", "is_new": false},
                ...
            ],
            "processing_time": 45.2
        }
    """
    audio_data = await file.read()

    # 路由到 diarization worker
    result = await registry.route_request(
        engine="diarization",
        action="process",
        audio_data=audio_data,
        num_speakers=num_speakers
    )

    return {"success": True, **result}
```

---

## 6. 部署配置

### 6.1 依赖安装

```bash
# 基础依赖
pip install torch torchaudio

# Pyannote
pip install pyannote.audio

# SpeechBrain (ECAPA-TDNN, SepFormer)
pip install speechbrain

# FunASR (SenseVoice)
pip install funasr

# 其他
pip install librosa soundfile numpy
```

### 6.2 配置文件

```yaml
# config.yaml 新增

workers:
  diarization:
    port: 8004
    device: cpu  # 或 cuda
    hf_token: ${HF_TOKEN}  # 环境变量
    speaker_db_path: ./data/speaker_db

    # Pyannote 参数
    pyannote:
      embedding_batch_size: 32
      clustering_threshold: 0.7

    # 说话人匹配参数
    speaker_matching:
      similarity_threshold: 0.75
      embedding_momentum: 0.9
```

### 6.3 启动脚本更新

```bash
# scripts/start-all.sh 新增

# 启动 Diarization Worker
start_diarization() {
    echo -e "${BLUE}[6/6]${NC} 启动 Diarization Worker (端口 8004)..."
    cd $VOICE_CLONE_DIR

    export HF_TOKEN="your_huggingface_token"

    nohup python3 -m src.main worker \
        --engine diarization \
        --port 8004 \
        --gateway http://localhost:8080 \
        --device cpu \
        --auto-load > $LOG_DIR/diarization.log 2>&1 &
    echo $! > $LOG_DIR/diarization.pid
    wait_for_service 8004 "Diarization Worker"
}
```

---

## 7. 性能对比预估

| 指标 | v1 现状 | v2 预期 | 提升 |
|------|---------|---------|------|
| **DER (Diarization Error Rate)** | ~30% | ~10% | 3x |
| **重叠语音处理** | 不支持 | 支持 2-3 人 | N/A |
| **噪声鲁棒性 (SNR=10dB)** | EER ~8% | EER ~3% | 2.7x |
| **跨会话说话人一致性** | 无 | >95% | N/A |
| **处理速度 (CPU)** | 0.5x 实时 | 0.3x 实时 | -40% |
| **处理速度 (GPU)** | N/A | 2x 实时 | N/A |

---

## 8. 下一步行动计划

### 8.1 第一阶段：核心功能（1-2 周）

- [ ] 集成 Pyannote 3.1 说话人分离
- [ ] 集成 ECAPA-TDNN 说话人嵌入
- [ ] 实现说话人数据库
- [ ] 实现分段 ASR 转录

### 8.2 第二阶段：重叠处理（1 周）

- [ ] 集成 SepFormer 语音分离
- [ ] 实现重叠检测和处理流程
- [ ] 测试和优化重叠场景

### 8.3 第三阶段：优化和部署（1 周）

- [ ] Worker 服务封装
- [ ] API 设计和文档
- [ ] 性能测试和调优
- [ ] CPU/GPU 适配

---

## 9. 参考资料

- [Pyannote Audio 3.1](https://github.com/pyannote/pyannote-audio)
- [SpeechBrain](https://speechbrain.github.io/)
- [FunASR](https://github.com/alibaba-damo-academy/FunASR)
- [ECAPA-TDNN Paper](https://arxiv.org/abs/2005.07143)
- [SepFormer Paper](https://arxiv.org/abs/2010.13154)

---

*文档版本：v2.0*
*创建日期：2025-12-03*
*作者：Claude Code Assistant*
