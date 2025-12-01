# GPT-SoVITS 预训练模型

GPT-SoVITS 语音合成系统的预训练模型文件，用于离线部署。

## 模型文件

| 文件 | 分卷数 | 总大小 | 说明 |
|------|--------|--------|------|
| `pretrained_models.pkg.part_*` | 88 | 4,352 MB | GPT-SoVITS 预训练模型 |
| `g2pw_model.pkg.part_*` | 12 | 562 MB | G2PW 中文注音模型 |
| **总计** | **100** | **~4.9 GB** | |

## 还原方法

### Windows (PowerShell)

```powershell
cd packages\models\gpt_sovits

# 还原预训练模型
Get-Content pretrained_models.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content pretrained_models.zip -Encoding Byte

# 还原 G2PW 模型
Get-Content g2pw_model.pkg.part_* -Encoding Byte -ReadCount 0 | Set-Content g2pw_model.zip -Encoding Byte

# 解压到目标目录
Expand-Archive -Path pretrained_models.zip -DestinationPath ..\..\repos\GPT-SoVITS\GPT_SoVITS\ -Force
Expand-Archive -Path g2pw_model.zip -DestinationPath ..\..\repos\GPT-SoVITS\GPT_SoVITS\text\ -Force
```

### Linux/macOS

```bash
cd packages/models/gpt_sovits

# 还原预训练模型
cat pretrained_models.pkg.part_* > pretrained_models.zip

# 还原 G2PW 模型
cat g2pw_model.pkg.part_* > g2pw_model.zip

# 解压到目标目录
unzip pretrained_models.zip -d ../../repos/GPT-SoVITS/GPT_SoVITS/
unzip g2pw_model.zip -d ../../repos/GPT-SoVITS/GPT_SoVITS/text/
```

## 目标目录结构

解压后的目录结构：

```
packages/repos/GPT-SoVITS/GPT_SoVITS/
├── pretrained_models/
│   ├── chinese-roberta-wwm-ext-large/
│   ├── chinese-hubert-base/
│   ├── gsv-v2final-pretrained/
│   │   ├── s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt
│   │   └── s2G2333k.pth
│   ├── s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
│   └── s2G488k.pth
└── text/
    └── G2PWModel/
        └── ... (G2PW 模型文件)
```

## 模型说明

- **chinese-roberta-wwm-ext-large**: BERT 文本编码模型
- **chinese-hubert-base**: 中文语音特征提取模型
- **gsv-v2final-pretrained**: GPT-SoVITS v2 预训练权重
- **G2PWModel**: 中文文本转拼音模型（支持多音字）

## 注意事项

1. 确保有足够的磁盘空间（解压后约 5GB）
2. 解压后可删除 .zip 文件以节省空间
3. 首次运行 GPT-SoVITS 需要这些模型才能正常工作
