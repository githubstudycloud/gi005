# 方案二：Coqui XTTS-v2 语音克隆

## 简介

[Coqui TTS](https://github.com/coqui-ai/TTS) 是功能最全面的开源 TTS 工具包，XTTS-v2 是其中支持零样本语音克隆的模型。

## 核心特点

- ✅ **端到端语音克隆**：直接从音频提取音色并生成语音
- ✅ 只需 6 秒参考音频
- ✅ 支持 17 种语言（包括中文）
- ✅ 内置 Speaker Encoder
- ✅ 一行代码完成克隆

## 工作原理

```
参考音频 + 文本 → XTTS-v2 → 克隆语音
        ↓
  Speaker Embedding
  GPT Conditioning
```

## 安装

```bash
pip install TTS

# 或从源码安装
git clone https://github.com/coqui-ai/TTS
cd TTS
pip install -e .
```

## 文件结构

```
02-coqui-xtts/
├── README.md           # 本文档
├── requirements.txt    # 依赖
├── voice_cloner.py     # 核心实现
├── test_clone.py       # 测试代码
└── samples/            # 测试音频
```

## 支持的语言

en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko

## 参考资源

- [Coqui TTS GitHub](https://github.com/coqui-ai/TTS)
- [XTTS-v2 Hugging Face](https://huggingface.co/coqui/XTTS-v2)
