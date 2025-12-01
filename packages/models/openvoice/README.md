# OpenVoice 模型包

OpenVoice 是 MyShell 开发的开源语音克隆模型。

## 模型结构

```
openvoice/
├── checkpoints_v2/        # OpenVoice v2 检查点
│   ├── converter/         # 声音转换器
│   │   ├── checkpoint.pth
│   │   └── config.json
│   └── base_speakers/     # 基础说话人
│       ├── en/
│       └── zh/
└── checkpoints/           # OpenVoice v1 检查点 (可选)
```

## 分卷格式

```
checkpoints_v2.tar.part_aa  (~100MB)
checkpoints_v2.tar.part_ab  (~26MB)
```

## 还原步骤

```bash
# Linux/macOS/Git Bash
cat checkpoints_v2.tar.part_* | tar -xvf -
```

## 在线下载

```bash
# 设置镜像
export HF_ENDPOINT=https://hf-mirror.com

# 下载
git clone https://huggingface.co/myshell-ai/OpenVoice
```

或访问：https://huggingface.co/myshell-ai/OpenVoice

## 依赖

OpenVoice 需要 MeloTTS 作为基础 TTS：
```bash
pip install git+https://github.com/myshell-ai/MeloTTS.git
```
