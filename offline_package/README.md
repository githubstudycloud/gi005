# 离线部署包

本目录包含音色克隆 TTS 项目所需的模型文件分卷包。

**注意**：文件使用 `.pkg.part_*` 后缀以避免被 .gitignore 忽略。

## 文件清单

| 文件 | 说明 | 大小 |
|------|------|------|
| `checkpoints_v2.pkg.part_aa` | OpenVoice 模型分卷 1/2 | 95MB |
| `checkpoints_v2.pkg.part_ab` | OpenVoice 模型分卷 2/2 | 30MB |
| `whisper_models.pkg.part_aa` ~ `ap` | Whisper 模型分卷 1-16/16 | 各 95MB |

## 还原方法

### Linux / macOS / Git Bash

```bash
cd offline_package

# 还原 OpenVoice 模型
cat checkpoints_v2.pkg.part_* | tar -xvf -

# 还原 Whisper 模型
cat whisper_models.pkg.part_* | tar -xvf -

# 移动到项目根目录
mv checkpoints_v2 ../
mv whisper_models ../
```

### Windows CMD

```cmd
cd offline_package

:: 还原 OpenVoice 模型
copy /b checkpoints_v2.pkg.part_* checkpoints_v2.tar
tar -xvf checkpoints_v2.tar
del checkpoints_v2.tar

:: 还原 Whisper 模型
copy /b whisper_models.pkg.part_* whisper_models.tar
tar -xvf whisper_models.tar
del whisper_models.tar

:: 移动到项目根目录
move checkpoints_v2 ..\
move whisper_models ..\
```

### Windows PowerShell

```powershell
cd offline_package

# 还原 OpenVoice 模型
Get-Content checkpoints_v2.pkg.part_* -Raw -Encoding Byte | Set-Content checkpoints_v2.tar -Encoding Byte
tar -xvf checkpoints_v2.tar
Remove-Item checkpoints_v2.tar

# 还原 Whisper 模型
Get-Content whisper_models.pkg.part_* -Raw -Encoding Byte | Set-Content whisper_models.tar -Encoding Byte
tar -xvf whisper_models.tar
Remove-Item whisper_models.tar

# 移动到项目根目录
Move-Item checkpoints_v2 ..\
Move-Item whisper_models ..\
```

## 还原后目录结构

```
gi005/
├── checkpoints_v2/          # OpenVoice 模型
│   ├── converter/
│   │   ├── config.json
│   │   └── checkpoint.pth
│   └── base_speakers/
│       └── ses/
│           ├── en-us.pth
│           └── zh.pth
│
└── whisper_models/          # Whisper 模型（可选）
    └── faster-whisper-medium/
        ├── config.json
        ├── model.bin
        ├── tokenizer.json
        └── vocabulary.txt
```

## 注意事项

1. **Whisper 模型是可选的**：如果使用 `vad=True` 参数（推荐），OpenVoice 会使用 silero VAD，不需要 Whisper 模型。

2. **XTTS 模型在另一个目录**：XTTS-v2 模型分卷在 `tts_model/` 目录下。

3. **验证完整性**：还原后检查文件大小是否正确：
   - `checkpoints_v2/` 约 126MB
   - `whisper_models/` 约 1.5GB

## 打包命令参考

```bash
# 打包 OpenVoice 模型（使用 .pkg 后缀避免被忽略）
tar -cvf - checkpoints_v2/ | split -b 95m - checkpoints_v2.pkg.part_

# 打包 Whisper 模型
tar -cvf - whisper_models/ | split -b 95m - whisper_models.pkg.part_
```
