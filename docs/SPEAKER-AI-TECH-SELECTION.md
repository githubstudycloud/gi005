# 说话人分离与识别 AI 技术选型评判文档

## 1. 项目背景与需求

### 1.1 业务需求

在 Voice Clone TTS 项目基础上，需要增加以下 AI Worker 服务能力：

1. **说话人分离（Speaker Diarization）**：处理多人对话场景，识别"谁在什么时候说话"
2. **语音重叠处理（Overlapping Speech）**：处理多人同时说话的复杂场景
3. **说话人识别（Speaker Recognition）**：在不同噪音背景下，确保同一说话人不会被识别为不同的人
4. **语音分离（Speech Separation）**：将重叠的语音分离成独立的音频流

### 1.2 技术挑战

| 挑战 | 描述 |
|------|------|
| 语音重叠 | 多人同时说话时准确区分每个人的语音 |
| 噪声鲁棒性 | 不同噪音环境下保持说话人身份一致性 |
| 实时性要求 | 部分场景需要低延迟处理 |
| 中文支持 | 需要良好的中文语音支持 |
| 资源限制 | 需在 CPU 模式下可运行（RTX 5070 暂不支持） |

---

## 2. 说话人分离（Speaker Diarization）模型选型

### 2.1 候选模型对比

| 模型 | DER (%) | 重叠处理 | 实时性 | 中文支持 | 许可证 | 推荐度 |
|------|---------|----------|--------|----------|--------|--------|
| **Pyannote 3.1** | ~10% | 优秀 | 近实时 | 好 | MIT | ⭐⭐⭐⭐⭐ |
| NVIDIA NeMo Sortformer | ~8-12% | 优秀 | 中等 | 好 | Apache 2.0 | ⭐⭐⭐⭐ |
| WhisperX | ~12-15% | 良好 | 慢 | 优秀 | BSD | ⭐⭐⭐⭐ |
| Simple Diarizer | ~15-20% | 基础 | 快 | 中等 | MIT | ⭐⭐⭐ |

> DER = Diarization Error Rate，越低越好

### 2.2 详细评估

#### 2.2.1 Pyannote Audio 3.1（推荐）

**GitHub**: https://github.com/pyannote/pyannote-audio

**优势**：
- 业界领先的开源说话人分离系统
- 在 DIHARD III 等基准测试中达到 SOTA 水平（~10% DER）
- 原生支持重叠语音检测（Overlapping Speech Detection）
- 模块化设计，可单独使用 VAD、分割、嵌入等组件
- 支持端到端训练和微调
- 活跃的社区和持续更新

**劣势**：
- 需要 HuggingFace 账户获取预训练模型
- 计算资源需求较高
- 首次加载模型较慢

**安装**：
```bash
pip install pyannote.audio
```

**使用示例**：
```python
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="YOUR_HF_TOKEN"
)

# 说话人分离
diarization = pipeline("audio.wav")

# 输出：谁在什么时间说话
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"{turn.start:.1f}s - {turn.end:.1f}s: {speaker}")
```

#### 2.2.2 NVIDIA NeMo Sortformer

**GitHub**: https://github.com/NVIDIA/NeMo

**优势**：
- 端到端 Transformer 架构，无需后处理
- 在 CALLHOME 数据集上表现优异
- 支持多种语言
- 与 NVIDIA 生态系统深度集成

**劣势**：
- 模型较大，资源需求高
- 主要针对 GPU 优化
- 依赖较多，安装复杂

**安装**：
```bash
pip install nemo_toolkit[asr]
```

#### 2.2.3 WhisperX

**GitHub**: https://github.com/m-bain/whisperX

**优势**：
- 结合 Whisper 转录和说话人分离
- 提供字级别对齐
- 中文支持优秀
- 一站式解决方案

**劣势**：
- 依赖多个模型，资源占用大
- 处理速度较慢
- 主要用于离线处理

**安装**：
```bash
pip install whisperx
```

### 2.3 说话人分离选型结论

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 通用场景 | Pyannote 3.1 | 最佳性能，活跃维护 |
| 需要转录+分离 | WhisperX | 一站式解决方案 |
| 生产环境 GPU | NeMo Sortformer | NVIDIA 优化，稳定性高 |

**最终推荐**：**Pyannote 3.1** 作为主要说话人分离引擎

---

## 3. 说话人识别/嵌入（Speaker Recognition/Embedding）模型选型

### 3.1 候选模型对比

| 模型 | EER (%) | 噪声鲁棒性 | 模型大小 | 推理速度 | 推荐度 |
|------|---------|------------|----------|----------|--------|
| **ECAPA-TDNN** | 0.8-1.2% | 优秀 | ~20MB | 快 | ⭐⭐⭐⭐⭐ |
| TitaNet-Large | 0.6-0.8% | 优秀 | ~85MB | 中等 | ⭐⭐⭐⭐⭐ |
| WavLM-TDNN | 0.5-0.9% | 极好 | ~300MB | 慢 | ⭐⭐⭐⭐ |
| ResNet-TDNN | 1.0-1.5% | 良好 | ~25MB | 快 | ⭐⭐⭐ |
| X-Vector | 2.0-3.0% | 中等 | ~10MB | 很快 | ⭐⭐ |

> EER = Equal Error Rate，越低越好

### 3.2 详细评估

#### 3.2.1 ECAPA-TDNN（推荐）

**论文**: ECAPA-TDNN: Emphasized Channel Attention for Speaker Verification

**优势**：
- VoxCeleb 基准测试 SOTA 模型之一
- 通过通道注意力机制增强说话人特征提取
- 对噪声和信道变化具有很强的鲁棒性
- 模型紧凑，适合部署
- SpeechBrain 和 pyannote 都内置支持

**劣势**：
- 需要足够长的语音片段（建议 > 2秒）
- 对极端噪声场景仍有挑战

**使用示例（SpeechBrain）**：
```python
from speechbrain.inference.speaker import SpeakerRecognition

# 加载预训练模型
verification = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)

# 说话人验证
score, prediction = verification.verify_files("speaker1.wav", "speaker2.wav")
print(f"Same speaker: {prediction}, Score: {score}")

# 提取嵌入向量
embedding = verification.encode_batch(waveform)
```

#### 3.2.2 TitaNet-Large（NVIDIA）

**GitHub**: NVIDIA NeMo

**优势**：
- NVIDIA 开发，性能优异
- 多尺度特征聚合
- 在多个基准测试中达到 SOTA
- 支持多语言

**劣势**：
- 模型较大
- 依赖 NeMo 生态系统

**使用示例**：
```python
import nemo.collections.asr as nemo_asr

speaker_model = nemo_asr.models.EncDecSpeakerLabelModel.from_pretrained(
    "nvidia/speakerverification_en_titanet_large"
)

# 验证两个音频是否为同一说话人
result = speaker_model.verify_speakers(
    "audio1.wav", "audio2.wav"
)
```

#### 3.2.3 WavLM-TDNN

**论文**: WavLM: Large-Scale Self-Supervised Pre-Training for Full Stack Speech Processing

**优势**：
- 自监督预训练，特征表示能力强
- 在噪声环境下表现最佳
- 微软开发，持续更新
- 支持多种下游任务

**劣势**：
- 模型很大（~300MB）
- 推理速度较慢
- 资源需求高

**使用示例**：
```python
from transformers import WavLMForXVector

model = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv")

# 提取说话人嵌入
embeddings = model(audio_input).embeddings
```

### 3.3 说话人识别选型结论

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 通用场景 | ECAPA-TDNN | 平衡性能和效率 |
| 高噪声环境 | WavLM-TDNN | 最强噪声鲁棒性 |
| 生产环境 GPU | TitaNet-Large | NVIDIA 优化 |
| 边缘设备/低资源 | X-Vector | 轻量快速 |

**最终推荐**：**ECAPA-TDNN** 作为主要说话人嵌入模型，配合 **WavLM** 用于高噪声场景

---

## 4. 语音分离（Speech Separation）模型选型

### 4.1 候选模型对比

| 模型 | SI-SNRi (dB) | 实时性 | 模型大小 | 多说话人 | 推荐度 |
|------|--------------|--------|----------|----------|--------|
| **SepFormer** | 22.3 | 非实时 | ~26M | 2-3人 | ⭐⭐⭐⭐⭐ |
| Conv-TasNet | 15.3 | 实时 | ~5M | 2人 | ⭐⭐⭐⭐ |
| DPRNN | 18.8 | 近实时 | ~2.6M | 2人 | ⭐⭐⭐⭐ |
| Sudo rm -rf | 18.9 | 实时 | ~2.5M | 2人 | ⭐⭐⭐⭐ |
| TF-GridNet | 23.5 | 非实时 | ~14M | 2人 | ⭐⭐⭐⭐ |

> SI-SNRi = Scale-Invariant Signal-to-Noise Ratio improvement，越高越好

### 4.2 详细评估

#### 4.2.1 SepFormer（推荐）

**论文**: Attention is All You Need in Speech Separation

**优势**：
- 纯 Transformer 架构
- WSJ0-2mix 上达到 22.3 dB SI-SNRi（SOTA）
- SpeechBrain 官方支持
- 代码清晰，易于修改

**劣势**：
- 计算量较大
- 非实时处理
- 主要针对 2 说话人场景优化

**使用示例（SpeechBrain）**：
```python
from speechbrain.inference.separation import SepformerSeparation

model = SepformerSeparation.from_hparams(
    source="speechbrain/sepformer-wsj02mix",
    savedir="pretrained_models/sepformer-wsj02mix"
)

# 分离混合语音
est_sources = model.separate_file(path="mixed_audio.wav")

# est_sources 包含分离后的各个说话人语音
```

#### 4.2.2 Conv-TasNet

**论文**: Conv-TasNet: Surpassing Ideal Time–Frequency Magnitude Masking for Speech Separation

**优势**：
- 轻量级，适合边缘部署
- 支持实时处理
- 经典模型，稳定可靠
- Asteroid 工具包支持

**劣势**：
- 性能不如 Transformer 模型
- 对噪声敏感

**使用示例（Asteroid）**：
```python
from asteroid.models import ConvTasNet

model = ConvTasNet.from_pretrained("mpariente/ConvTasNet_WHAM!_sepclean")

# 分离语音
separated = model.separate(mixed_audio)
```

#### 4.2.3 Asteroid 工具包

**GitHub**: https://github.com/asteroid-team/asteroid

**优势**：
- 统一接口支持多种分离模型
- 完整的训练和评估流程
- 丰富的预训练模型
- 活跃的社区

**劣势**：
- 需要额外学习 API
- 某些模型可能需要微调

**安装**：
```bash
pip install asteroid
```

### 4.3 语音分离选型结论

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 最佳质量 | SepFormer | SOTA 性能 |
| 实时处理 | Conv-TasNet | 低延迟 |
| 移动/边缘设备 | Sudo rm -rf | 极轻量 |
| 多模型实验 | Asteroid 工具包 | 统一接口 |

**最终推荐**：**SepFormer** 作为主要语音分离引擎，**Conv-TasNet** 作为轻量备选

---

## 5. 重叠语音检测（Overlapping Speech Detection）

### 5.1 方案对比

| 方案 | 描述 | 性能 | 推荐度 |
|------|------|------|--------|
| **Pyannote OSD** | Pyannote 内置重叠检测 | 优秀 | ⭐⭐⭐⭐⭐ |
| PixIT | WavLM + 分离模型 | SOTA | ⭐⭐⭐⭐ |
| DiaPer | 端到端多模态 | 优秀 | ⭐⭐⭐⭐ |

### 5.2 推荐方案

使用 **Pyannote 3.1** 的内置重叠语音检测功能，它已集成在说话人分离 Pipeline 中：

```python
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")

# Pipeline 自动处理重叠语音
diarization = pipeline("audio.wav")

# 检测重叠区域
from pyannote.audio import Pipeline as OSDPipeline
osd_pipeline = Pipeline.from_pretrained("pyannote/overlapped-speech-detection")
overlapped = osd_pipeline("audio.wav")
```

---

## 6. 整体架构设计

### 6.1 新增 Worker 服务

```
                           ┌─────────────────────┐
                           │  Gateway (:8080)    │
                           └─────────┬───────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│ TTS Workers   │          │ New AI Workers │         │ Existing      │
│ (8001-8003)   │          │               │          │               │
├───────────────┤          ├───────────────┤          └───────────────┘
│ XTTS          │          │ Diarization   │  ← Pyannote 3.1
│ OpenVoice     │          │ Worker (:8004)│
│ GPT-SoVITS    │          ├───────────────┤
└───────────────┘          │ Speaker ID    │  ← ECAPA-TDNN
                           │ Worker (:8005)│
                           ├───────────────┤
                           │ Separation    │  ← SepFormer
                           │ Worker (:8006)│
                           └───────────────┘
```

### 6.2 处理流程

```
输入音频
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 1. 预处理 (VAD + 降噪)                               │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 2. 重叠检测 (Pyannote OSD)                          │
│    - 识别是否存在语音重叠                            │
└─────────────────────────────────────────────────────┘
    │
    ├─── 无重叠 ──────────────────────────┐
    │                                      │
    ▼                                      ▼
┌─────────────────────┐          ┌─────────────────────┐
│ 3a. 语音分离        │          │ 3b. 直接分割        │
│ (SepFormer)         │          │                     │
└─────────────────────┘          └─────────────────────┘
    │                                      │
    └──────────────┬───────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ 4. 说话人分离 (Pyannote Diarization)                │
│    - 识别谁在什么时候说话                            │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 5. 说话人嵌入提取 (ECAPA-TDNN)                      │
│    - 为每个说话人生成唯一向量表示                    │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 6. 说话人聚类/匹配                                   │
│    - 跨音频保持说话人身份一致                        │
└─────────────────────────────────────────────────────┘
    │
    ▼
输出：分离的音频 + 说话人标签 + 时间戳
```

---

## 7. 依赖安装

### 7.1 核心依赖

```bash
# PyTorch (CPU 或 CUDA)
pip install torch torchaudio

# 说话人分离
pip install pyannote.audio

# 说话人识别
pip install speechbrain

# 语音分离
pip install asteroid
# 或
pip install speechbrain  # SepFormer

# 其他依赖
pip install librosa soundfile numpy scipy
```

### 7.2 可选依赖

```bash
# WhisperX（转录+分离一体化）
pip install whisperx

# NeMo（NVIDIA 生态）
pip install nemo_toolkit[asr]
```

### 7.3 模型下载

```python
# Pyannote（需要 HuggingFace token）
from pyannote.audio import Pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="YOUR_HF_TOKEN"
)

# SpeechBrain ECAPA-TDNN
from speechbrain.inference.speaker import SpeakerRecognition
model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb"
)

# SepFormer
from speechbrain.inference.separation import SepformerSeparation
model = SepformerSeparation.from_hparams(
    source="speechbrain/sepformer-wsj02mix"
)
```

---

## 8. 最终技术选型汇总

| 功能 | 推荐模型 | 备选模型 | 理由 |
|------|----------|----------|------|
| **说话人分离** | Pyannote 3.1 | WhisperX | SOTA 性能，原生重叠支持 |
| **说话人嵌入** | ECAPA-TDNN | WavLM-TDNN | 平衡性能与效率 |
| **语音分离** | SepFormer | Conv-TasNet | 最佳分离质量 |
| **重叠检测** | Pyannote OSD | PixIT | 与分离 Pipeline 集成 |

### 8.1 技术栈总结

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 音频处理技术栈                         │
├─────────────────────────────────────────────────────────────┤
│  框架层     │  PyTorch + torchaudio                         │
├─────────────┼───────────────────────────────────────────────┤
│  工具包     │  SpeechBrain + Pyannote + Asteroid            │
├─────────────┼───────────────────────────────────────────────┤
│  核心模型   │  Pyannote 3.1 + ECAPA-TDNN + SepFormer        │
├─────────────┼───────────────────────────────────────────────┤
│  部署方式   │  FastAPI Worker + Gateway 架构                 │
└─────────────┴───────────────────────────────────────────────┘
```

---

## 9. 下一步计划

1. **Worker 开发**：基于 `base_worker.py` 模式开发三个新 Worker
2. **模型集成**：下载和集成推荐的预训练模型
3. **API 设计**：设计 RESTful API 接口
4. **测试验证**：使用中文语音数据进行测试
5. **性能优化**：针对 CPU 模式进行推理优化

---

## 10. 参考资料

- [Pyannote Audio Documentation](https://github.com/pyannote/pyannote-audio)
- [SpeechBrain Documentation](https://speechbrain.github.io/)
- [Asteroid Documentation](https://asteroid-team.github.io/)
- [NVIDIA NeMo](https://github.com/NVIDIA/NeMo)
- [WhisperX](https://github.com/m-bain/whisperX)
- [VoxCeleb Dataset](https://www.robots.ox.ac.uk/~vgg/data/voxceleb/)
- [DIHARD Challenge](https://dihardchallenge.github.io/)

---

*文档创建日期：2025-12-03*
*作者：Claude Code Assistant*
