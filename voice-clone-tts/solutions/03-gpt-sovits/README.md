# 方案三：GPT-SoVITS 语音克隆

## 简介

[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 是一个强大的少样本语音克隆和 TTS 工具，只需 1 分钟训练数据即可实现高质量克隆。

## 核心特点

- ✅ **极少数据需求**：1分钟数据即可微调
- ✅ **零样本模式**：5秒参考音频即可合成
- ✅ 支持中英日三语
- ✅ 提供 WebUI 和 API
- ✅ 可选微调进一步提升效果

## 工作原理

```
模式1 (零样本): 5秒参考音频 → 直接合成
模式2 (微调): 1分钟数据 → 训练 → 高质量合成
```

## 安装

```bash
# 克隆仓库
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS

# 创建环境
conda create -n gpt-sovits python=3.10
conda activate gpt-sovits

# 安装依赖
pip install -r requirements.txt

# 安装 ffmpeg
# Windows: 下载 ffmpeg.exe 放到根目录
# Linux: sudo apt install ffmpeg
```

## 文件结构

```
03-gpt-sovits/
├── README.md           # 本文档
├── requirements.txt    # 依赖说明
├── voice_cloner.py     # API 调用实现
├── test_clone.py       # 测试代码
└── samples/            # 测试音频
```

## 使用方式

1. **WebUI 模式**: 运行 `python webui.py`
2. **API 模式**: 运行 `python api_v2.py`

## 参考资源

- [GPT-SoVITS GitHub](https://github.com/RVC-Boss/GPT-SoVITS)
- [用户指南](https://github.com/RVC-Boss/GPT-SoVITS/wiki/User-Guide)
- [HuggingFace 模型](https://huggingface.co/lj1995/GPT-SoVITS)
