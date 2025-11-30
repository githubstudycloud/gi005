# External Repositories

本目录用于存放外部依赖仓库。这些仓库需要用户自行克隆，不包含在主仓库中。

## 必需仓库

### 1. OpenVoice (音色克隆)

```bash
cd packages/repos
git clone https://github.com/myshell-ai/OpenVoice.git
cd OpenVoice
pip install -e .
```

### 2. GPT-SoVITS (中文语音合成)

```bash
cd packages/repos
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS
pip install -r requirements.txt
```

**注意**: GPT-SoVITS 需要额外下载预训练模型，请参考其官方文档。

## 目录结构

```
packages/repos/
├── README.md          # 本文件
├── OpenVoice/         # OpenVoice 仓库 (需克隆)
└── GPT-SoVITS/        # GPT-SoVITS 仓库 (需克隆)
```

## 快速安装脚本

```bash
# Windows
cd packages/repos
git clone https://github.com/myshell-ai/OpenVoice.git
git clone https://github.com/RVC-Boss/GPT-SoVITS.git

# 安装依赖
pip install -e OpenVoice
pip install -r GPT-SoVITS/requirements.txt
```
