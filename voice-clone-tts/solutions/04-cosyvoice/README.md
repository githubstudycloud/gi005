# 方案四：CosyVoice 语音克隆

## 简介

[CosyVoice](https://github.com/FunAudioLLM/CosyVoice) 是阿里通义实验室开源的多语言零样本语音合成模型，基于监督语义标记。

## 核心特点

- ✅ **3秒极速克隆**：只需 3-10 秒参考音频
- ✅ 支持中英日粤韩五种语言
- ✅ 跨语言合成（用中文音频合成英文）
- ✅ 情感/风格控制（使用指令）
- ✅ 15万小时数据训练

## 工作原理

```
模式1 (零样本): 参考音频 → 语义提取 → 合成
模式2 (指令): 指令文本 → 风格控制 → 合成
模式3 (SFT): 预训练角色 → 直接合成
```

## 安装

```bash
# 克隆仓库
git clone https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice

# 创建环境
conda create -n cosyvoice python=3.8
conda activate cosyvoice

# 安装依赖
pip install -r requirements.txt

# 下载模型
# 从 ModelScope 或 HuggingFace 下载
```

## 模型选择

| 模型 | 用途 |
|------|------|
| CosyVoice-300M | 零样本/跨语言 |
| CosyVoice-300M-SFT | 预训练角色 |
| CosyVoice-300M-Instruct | 指令控制 |
| CosyVoice2-0.5B | 最新版本 |

## 文件结构

```
04-cosyvoice/
├── README.md           # 本文档
├── requirements.txt    # 依赖
├── voice_cloner.py     # 核心实现
├── test_clone.py       # 测试代码
└── samples/            # 测试音频
```

## 参考资源

- [CosyVoice GitHub](https://github.com/FunAudioLLM/CosyVoice)
- [论文](https://arxiv.org/abs/2407.05407)
- [HuggingFace](https://huggingface.co/FunAudioLLM)
