# 音色克隆与TTS语音生成方案

本项目探究使用 Python 从音频中提取音色特征，并结合 TTS 模型生成语音的技术方案。

## 📋 项目结构

```
voice-clone-tts/
├── README.md                     # 本文档（方案总结）
├── requirements.txt              # 基础依赖
├── examples/                     # 旧版示例代码（已废弃）
└── solutions/                    # 各方案详细实现
    ├── 01-openvoice/            # OpenVoice 音色克隆
    ├── 02-coqui-xtts/           # Coqui XTTS-v2
    ├── 03-gpt-sovits/           # GPT-SoVITS
    ├── 04-cosyvoice/            # CosyVoice (阿里)
    └── 05-fish-speech/          # Fish-Speech
```

---

## 🎯 方案总结对比

| 方案 | 音色提取 | 中文质量 | 参考音频需求 | 安装难度 | 推荐场景 |
|------|---------|---------|-------------|---------|---------|
| **OpenVoice** | ✅ 支持 | ⭐⭐⭐⭐ | 3-10秒 | ⭐⭐⭐ | 音色转换 |
| **Coqui XTTS** | ✅ 支持 | ⭐⭐⭐ | 6秒 | ⭐⭐⭐⭐⭐ | 多语言克隆 |
| **GPT-SoVITS** | ✅ 支持 | ⭐⭐⭐⭐⭐ | 5秒/1分钟微调 | ⭐⭐ | **中文首选** |
| **CosyVoice** | ✅ 支持 | ⭐⭐⭐⭐⭐ | 3-10秒 | ⭐⭐ | 跨语言/指令控制 |
| **Fish-Speech** | ✅ 支持 | ⭐⭐⭐⭐ | 10-30秒 | ⭐⭐⭐ | 低显存/快速推理 |

### 🏆 推荐选择

1. **中文最佳**: GPT-SoVITS 或 CosyVoice
2. **最简单易用**: Coqui XTTS-v2（一行代码）
3. **低显存**: Fish-Speech（仅需 4GB）
4. **音色转换**: OpenVoice（分离音色和内容）
5. **跨语言**: CosyVoice（中文音频说英文）

---

## 📦 各方案简介

### 方案一：OpenVoice

**特点**：音色与内容分离，可将任意语音转换为目标音色

```python
from openvoice import se_extractor
from openvoice.api import ToneColorConverter

# 提取音色
target_se, _ = se_extractor.get_se(reference_audio, converter, vad=True)

# 转换音色
converter.convert(source_audio, src_se, target_se, output_path)
```

**详细文档**: [solutions/01-openvoice/](solutions/01-openvoice/)

---

### 方案二：Coqui XTTS-v2

**特点**：一行代码完成克隆，支持 17 种语言

```python
from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.tts_to_file(text="你好", file_path="out.wav", speaker_wav="ref.wav", language="zh-cn")
```

**详细文档**: [solutions/02-coqui-xtts/](solutions/02-coqui-xtts/)

---

### 方案三：GPT-SoVITS

**特点**：少样本学习，1分钟数据微调达到极佳效果

```python
# 启动 API 服务
# python api_v2.py -a 127.0.0.1 -p 9880

import requests
response = requests.post("http://127.0.0.1:9880/tts", json={
    "text": "你好",
    "ref_audio_path": "reference.wav",
    "text_lang": "zh"
})
```

**详细文档**: [solutions/03-gpt-sovits/](solutions/03-gpt-sovits/)

---

### 方案四：CosyVoice

**特点**：阿里开源，3秒克隆，支持情感/指令控制

```python
from cosyvoice.cli.cosyvoice import CosyVoice

model = CosyVoice("pretrained_models/CosyVoice-300M")

# 零样本克隆
output = model.inference_zero_shot(text, prompt_text, prompt_audio)

# 跨语言（中文音频说英文）
output = model.inference_cross_lingual(english_text, chinese_audio)

# 指令控制
output = model.inference_instruct(text, speaker, "用开心的语气")
```

**详细文档**: [solutions/04-cosyvoice/](solutions/04-cosyvoice/)

---

### 方案五：Fish-Speech

**特点**：低显存(4GB)，快速推理，SOTA 质量

```python
# 本地推理或 API 调用
from fish_speech.inference import inference

# 或使用 Fish Audio API
api = FishSpeechAPI(api_key="your-key")
api.clone(text, reference_audio, output_path)
```

**详细文档**: [solutions/05-fish-speech/](solutions/05-fish-speech/)

---

## ⚠️ 关于 ChatTTS 的说明

**ChatTTS 本身不支持从音频提取音色**。

- ChatTTS 使用 768 维的 speaker embedding
- SpeechBrain 等工具提取的是 192 维 embedding
- 两者维度不兼容，无法直接使用

**ChatTTS 的正确用法**：
1. 使用 `sample_random_speaker()` 随机采样音色
2. 使用 [ChatTTS_Speaker](https://github.com/6drf21e/ChatTTS_Speaker) 预训练音色库
3. 保存满意的音色 `.pt` 文件复用

如需真正的音色克隆，请使用上述 5 个方案。

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- PyTorch 2.0+
- CUDA 11.8+（GPU 加速）
- 显存需求：4GB (Fish-Speech) ~ 8GB (其他)

### 推荐：使用 Coqui XTTS（最简单）

```bash
# 安装
pip install TTS

# 克隆语音
python -c "
from TTS.api import TTS
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2')
tts.tts_to_file('你好世界', 'output.wav', speaker_wav='reference.wav', language='zh-cn')
"
```

### 推荐：使用 GPT-SoVITS（中文最佳）

```bash
# 安装
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS && pip install -r requirements.txt

# 启动 WebUI
python webui.py
```

---

## 📚 参考资源

| 项目 | GitHub | 论文/文档 |
|------|--------|----------|
| OpenVoice | [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice) | [arXiv](https://arxiv.org/abs/2312.01479) |
| Coqui TTS | [coqui-ai/TTS](https://github.com/coqui-ai/TTS) | [HuggingFace](https://huggingface.co/coqui/XTTS-v2) |
| GPT-SoVITS | [RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) | [Wiki](https://github.com/RVC-Boss/GPT-SoVITS/wiki) |
| CosyVoice | [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice) | [arXiv](https://arxiv.org/abs/2407.05407) |
| Fish-Speech | [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) | [arXiv](https://arxiv.org/abs/2411.01156) |

---

## License

本项目代码采用 MIT 许可证。各方案请遵循其原始许可。
