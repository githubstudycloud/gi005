# XTTS-v2 模型包

XTTS-v2 是 Coqui TTS 的多语言语音克隆模型。

## 文件清单

| 文件 | 大小 | 说明 |
|------|------|------|
| config.json | ~2KB | 模型配置 |
| model.pth | ~1.8GB | 模型权重 |
| vocab.json | ~2KB | 词汇表 |
| speakers_xtts.pth | ~500KB | 说话人嵌入 |

## 分卷格式

大文件按 100MB 分卷存储：
```
xtts_v2.tar.part_aa
xtts_v2.tar.part_ab
...
xtts_v2.tar.part_at
```

## 还原步骤

### Windows (PowerShell)

```powershell
# 方式1: 使用 Git Bash
cat xtts_v2.tar.part_* | tar -xvf -

# 方式2: 使用 7-Zip
# 将所有分卷选中，右键 -> 7-Zip -> 解压到当前文件夹
```

### Linux/macOS

```bash
cat xtts_v2.tar.part_* | tar -xvf -
```

## 验证完整性

还原后目录结构应为：
```
xtts_v2/
├── config.json
├── model.pth
├── vocab.json
└── speakers_xtts.pth
```

## 在线下载

如果分卷包不完整，可在线下载：

```bash
# 设置镜像加速
export HF_ENDPOINT=https://hf-mirror.com

# 使用 huggingface-cli
pip install huggingface_hub
huggingface-cli download coqui/XTTS-v2 --local-dir ./xtts_v2
```

或直接访问：https://huggingface.co/coqui/XTTS-v2
