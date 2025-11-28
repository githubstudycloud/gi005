# 方案一：OpenVoice 音色克隆

## 简介

[OpenVoice](https://github.com/myshell-ai/OpenVoice) 是由 MIT 和 MyShell 开发的即时语音克隆模型。

## 核心特点

- ✅ **真正的音色克隆**：可从任意音频提取音色
- ✅ 只需几秒参考音频
- ✅ 支持多语言
- ✅ MIT 开源许可，可商用
- ✅ 分离音色和语言/口音控制

## 工作原理

```
参考音频 → SE Extractor → Tone Color Embedding
                                    ↓
文本 → Base TTS → 基础语音 → Tone Color Converter → 目标音色语音
```

## 安装

```bash
# 创建环境
conda create -n openvoice python=3.9
conda activate openvoice

# 克隆仓库
git clone https://github.com/myshell-ai/OpenVoice.git
cd OpenVoice
pip install -e .

# 下载模型检查点
# V2版本: https://huggingface.co/myshell-ai/OpenVoiceV2
```

## 文件结构

```
01-openvoice/
├── README.md           # 本文档
├── requirements.txt    # 依赖
├── voice_cloner.py     # 核心实现
├── test_clone.py       # 测试代码
└── samples/            # 测试音频
```

## 使用方法

详见 `voice_cloner.py` 和 `test_clone.py`

## 参考资源

- [OpenVoice GitHub](https://github.com/myshell-ai/OpenVoice)
- [OpenVoice V2 Hugging Face](https://huggingface.co/myshell-ai/OpenVoiceV2)
- [论文](https://arxiv.org/abs/2312.01479)
