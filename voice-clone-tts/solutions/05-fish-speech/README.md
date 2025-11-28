# 方案五：Fish-Speech 语音克隆

## 简介

[Fish-Speech](https://github.com/fishaudio/fish-speech) 是一个 SOTA 开源 TTS 系统，使用 LLM 技术实现高质量多语言语音合成。

## 核心特点

- ✅ **低显存需求**：仅需 4GB 显存
- ✅ **快速推理**：RTX 4090 达到 1:7 实时率
- ✅ 支持 8 种语言（中英日韩法德阿西）
- ✅ 无需音素依赖
- ✅ 10-30 秒参考音频即可克隆
- ✅ 零样本跨语言合成

## 工作原理

```
参考音频 → VQGAN 编码 → LLM 生成 → 语义 Token → 语音解码
```

使用 Dual-AR（双自回归）架构：
- 快速自回归：生成粗粒度语义
- 慢速自回归：生成细粒度声学特征

## 安装

```bash
# 克隆仓库
git clone https://github.com/fishaudio/fish-speech.git
cd fish-speech

# 创建环境
conda create -n fish-speech python=3.10
conda activate fish-speech

# 安装依赖
pip install -e .

# 下载模型
huggingface-cli download fishaudio/fish-speech-1.5 --local-dir checkpoints/fish-speech-1.5
```

## 文件结构

```
05-fish-speech/
├── README.md           # 本文档
├── requirements.txt    # 依赖
├── voice_cloner.py     # 核心实现
├── test_clone.py       # 测试代码
└── samples/            # 测试音频
```

## 最新版本

Fish Audio S1 是最新发布的前沿 TTS 模型，在 HuggingFace TTS-Arena-V2 排名第一。

## 参考资源

- [Fish-Speech GitHub](https://github.com/fishaudio/fish-speech)
- [论文](https://arxiv.org/abs/2411.01156)
- [HuggingFace](https://huggingface.co/fishaudio)
- [Fish Audio 平台](https://fish.audio/)
