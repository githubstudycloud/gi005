# External Repositories

本目录存放外部依赖仓库的源码包。仓库已预打包为分卷文件 (`.pkg.part_*`)，无需单独克隆。

## 源码包

| 文件 | 分卷 | 总大小 | 说明 |
|------|------|--------|------|
| `openvoice_src.pkg.part_*` | 2 | 3.5 MB | OpenVoice 源码 (音色克隆) |
| `gpt_sovits_src.pkg.part_*` | 2 | 2.7 MB | GPT-SoVITS 源码 (中文语音合成) |

**注意**: 源码包不包含预训练模型，模型需要在首次运行时自动下载或手动配置。

## 快速安装

### 方法一：从分卷包还原 (推荐)

```bash
cd packages/repos

# 还原并解压 OpenVoice
cat openvoice_src.pkg.part_* > openvoice_src.pkg && tar -xvf openvoice_src.pkg
pip install -e OpenVoice

# 还原并解压 GPT-SoVITS
cat gpt_sovits_src.pkg.part_* > gpt_sovits_src.pkg && tar -xvf gpt_sovits_src.pkg
pip install -r GPT-SoVITS/requirements.txt
```

### 方法二：从 GitHub 克隆 (需网络)

```bash
cd packages/repos

# OpenVoice
git clone https://github.com/myshell-ai/OpenVoice.git
pip install -e OpenVoice

# GPT-SoVITS
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
pip install -r GPT-SoVITS/requirements.txt
```

## 目录结构

```
packages/repos/
├── README.md                       # 本文件
├── openvoice_src.pkg.part_aa       # OpenVoice 分卷包 1
├── openvoice_src.pkg.part_ab       # OpenVoice 分卷包 2
├── gpt_sovits_src.pkg.part_aa      # GPT-SoVITS 分卷包 1
├── gpt_sovits_src.pkg.part_ab      # GPT-SoVITS 分卷包 2
├── OpenVoice/                      # 解压后的 OpenVoice 目录
└── GPT-SoVITS/                     # 解压后的 GPT-SoVITS 目录
```

## GPT-SoVITS 预训练模型

GPT-SoVITS 需要额外下载预训练模型：

1. 从 [Hugging Face](https://huggingface.co/lj1995/GPT-SoVITS) 下载模型
2. 解压到 `GPT-SoVITS/GPT_SoVITS/pretrained_models/` 目录
3. 下载 G2PW 模型到 `GPT-SoVITS/GPT_SoVITS/text/` 目录

详见 GPT-SoVITS 官方文档。
