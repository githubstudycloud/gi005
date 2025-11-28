# XTTS-v2 模型文件

离线使用的 XTTS-v2 模型文件，支持音色克隆。

**注意**：文件使用 `.pkg.part_*` 后缀以避免被 .gitignore 忽略。

## 模型来源

- 来源: [Hugging Face - coqui/XTTS-v2](https://huggingface.co/coqui/XTTS-v2)
- 许可证: Coqui Public Model License

## 文件说明

### 分卷文件
由于 GitHub 单文件大小限制（100MB），模型文件已打包分卷：

```
xtts_v2_full.pkg.part_aa  (95MB)
xtts_v2_full.pkg.part_ab  (95MB)
...
xtts_v2_full.pkg.part_au  (90MB)
```

总计约 2GB，共 21 个分卷

### 原始模型文件

```
xtts_v2/
├── config.json         # 模型配置
├── model.pth           # 主模型权重 (1.87GB)
├── dvae.pth            # DVAE 模型 (211MB)
├── speakers_xtts.pth   # 说话人嵌入 (7.75MB)
├── mel_stats.pth       # 梅尔统计 (1KB)
└── vocab.json          # 词汇表 (361KB)
```

## 还原方法

### Linux / macOS / Git Bash

```bash
# 进入目录
cd tts_model

# 合并分卷并解压
cat xtts_v2_full.pkg.part_* | tar -xvf -
```

### Windows (PowerShell)

```powershell
# 进入目录
cd tts_model

# 合并分卷
Get-Content xtts_v2_full.pkg.part_* -ReadCount 0 | Set-Content xtts_v2.tar -Encoding Byte

# 解压
tar -xvf xtts_v2.tar
Remove-Item xtts_v2.tar
```

### Windows (CMD)

```cmd
cd tts_model
copy /b xtts_v2_full.pkg.part_* xtts_v2.tar
tar -xvf xtts_v2.tar
del xtts_v2.tar
```

## 使用方法

还原后，在代码中指定模型路径：

```python
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

# 加载配置
config = XttsConfig()
config.load_json("tts_model/xtts_v2/config.json")

# 加载模型
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir="tts_model/xtts_v2/")
model.cuda()  # 或 model.cpu()

# 音色克隆
outputs = model.synthesize(
    "你好，这是测试语音",
    config,
    speaker_wav="reference.wav",
    language="zh-cn"
)
```

## 与生产环境集成

配合 `voice-clone-tts/production/` 使用：

```python
# 修改 xtts/cloner.py 中的模型路径
model_path = "tts_model/xtts_v2"
```

或在启动时指定：

```bash
python main.py serve --engine xtts --model-path tts_model/xtts_v2 --port 8000
```
