# 开源项目仓库

本目录用于存放项目依赖的开源项目仓库。

## 注意事项

1. 此目录已在 `.gitignore` 中，内容不会被提交到版本控制
2. 需要手动克隆所需的开源项目

## 必需仓库

### GPT-SoVITS (如需使用 GPT-SoVITS 引擎)

```bash
cd packages/repos
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
```

### OpenVoice (可选，通过 pip 安装更方便)

```bash
cd packages/repos
git clone https://github.com/myshell-ai/OpenVoice.git
cd OpenVoice && pip install -e .
```

## 配置代理

如果网络受限，可使用代理：

```bash
# HTTP 代理
git config --global http.proxy http://192.168.0.98:8800
git config --global https.proxy http://192.168.0.98:8800

# 取消代理
git config --global --unset http.proxy
git config --global --unset https.proxy
```

## 目录结构

克隆完成后的结构：

```
repos/
├── GPT-SoVITS/           # GPT-SoVITS 项目
│   ├── GPT_SoVITS/       # 核心代码
│   ├── api_v2.py         # API 服务
│   └── ...
├── OpenVoice/            # OpenVoice 项目 (可选)
│   ├── openvoice/
│   └── ...
└── README.md             # 本文件
```
