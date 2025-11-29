# Whisper 模型包

OpenAI Whisper 语音识别模型，用于音频预处理和转写。

## 模型版本

| 模型 | 大小 | VRAM | 精度 |
|------|------|------|------|
| tiny | 39M | ~1GB | 较低 |
| base | 74M | ~1GB | 一般 |
| small | 244M | ~2GB | 良好 |
| medium | 769M | ~5GB | 较好 |
| large-v3 | 1.5G | ~10GB | 最佳 |

## 推荐配置

- **低配置**: tiny 或 base (CPU 可运行)
- **中等配置**: small 或 medium (需要 GPU)
- **高配置**: large-v3 (需要 10GB+ VRAM)

## 分卷格式

```
whisper_models.tar.part_aa  (~100MB)
whisper_models.tar.part_ab  (~100MB)
...
```

## 还原步骤

```bash
cat whisper_models.tar.part_* | tar -xvf -
```

## 自动下载

Whisper 模型首次使用时会自动下载到缓存目录：
- Windows: `C:\Users\<用户>\.cache\whisper\`
- Linux/macOS: `~/.cache/whisper/`

```python
import whisper
model = whisper.load_model("medium")  # 自动下载
```

## 离线使用

将模型文件放入缓存目录即可离线使用。
