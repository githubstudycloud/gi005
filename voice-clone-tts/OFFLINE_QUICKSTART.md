# 🎯 完整离线部署指南（傻瓜式）

**本文档面向零基础用户**，一步一步教你从下载到运行音色克隆。

> ⏱️ 预计时间：30-60 分钟（取决于网速和电脑配置）
> 💾 所需空间：约 15GB

---

## 📋 目录

1. [准备工作](#1-准备工作)
2. [下载项目](#2-下载项目)
3. [还原分卷文件](#3-还原分卷文件)
4. [安装工具](#4-安装工具)
5. [创建虚拟环境](#5-创建虚拟环境)
6. [安装依赖](#6-安装依赖)
7. [克隆外部仓库](#7-克隆外部仓库)
8. [验证安装](#8-验证安装)
9. [开始使用](#9-开始使用)
10. [常见错误解决](#10-常见错误解决)

---

## 1. 准备工作

### 1.1 检查电脑配置

| 要求 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 10 | Windows 10/11 |
| 内存 | 8GB | 16GB+ |
| 硬盘空间 | 20GB | 50GB |
| 显卡 | 无（CPU模式） | NVIDIA 4GB+ |

### 1.2 需要的软件

在开始之前，确保你的电脑有：
- ✅ 网络连接（仅下载阶段需要）
- ✅ 解压软件（Windows 自带即可）

---

## 2. 下载项目

### 方法 A：使用 Git（推荐）

```cmd
:: 1. 打开命令提示符（按 Win+R，输入 cmd，回车）

:: 2. 进入你想存放项目的目录（比如 D 盘）
D:
mkdir projects
cd projects

:: 3. 克隆项目
git clone https://github.com/githubstudycloud/gi005.git

:: 4. 进入项目目录
cd gi005
```

### 方法 B：下载 ZIP

1. 打开浏览器，访问：https://github.com/githubstudycloud/gi005
2. 点击绿色的 `Code` 按钮
3. 点击 `Download ZIP`
4. 下载完成后，解压到 `D:\projects\gi005`

### 下载完成后的目录结构

```
D:\projects\gi005\
├── dependencies/          # 工具依赖包
├── offline_package/       # OpenVoice 和 Whisper 模型
├── tts_model/            # XTTS 模型
├── voice-clone-tts/      # 项目代码
├── .gitignore
├── CLAUDE.md
└── README.md
```

---

## 3. 还原分卷文件

### 3.1 打开命令提示符

按 `Win + R`，输入 `cmd`，回车。

### 3.2 还原工具依赖包

```cmd
:: 进入项目目录
cd /d D:\projects\gi005

:: 进入 dependencies 目录
cd dependencies

:: 合并分卷
copy /b tools.pkg.part_* tools.tar

:: 解压
tar -xvf tools.tar

:: 删除临时文件
del tools.tar

:: 将 FFmpeg 移到项目根目录
move ffmpeg.exe ..\
move ffprobe.exe ..\
move ffplay.exe ..\

:: 返回项目目录
cd ..
```

### 3.3 还原 OpenVoice 模型

```cmd
:: 进入 offline_package 目录
cd offline_package

:: 还原 OpenVoice 模型
copy /b checkpoints_v2.pkg.part_* checkpoints_v2.tar
tar -xvf checkpoints_v2.tar
del checkpoints_v2.tar

:: 移动到项目根目录
move checkpoints_v2 ..\

:: 返回项目目录
cd ..
```

### 3.4 还原 Whisper 模型（可选，推荐跳过）

> 💡 **提示**：如果你只使用 OpenVoice 的基本功能，可以跳过这一步。

```cmd
:: 如果需要 Whisper 模型
cd offline_package
copy /b whisper_models.pkg.part_* whisper_models.tar
tar -xvf whisper_models.tar
del whisper_models.tar
move whisper_models ..\
cd ..
```

### 3.5 还原 XTTS 模型

```cmd
:: 进入 tts_model 目录
cd tts_model

:: 合并分卷
copy /b xtts_v2_full.pkg.part_* xtts_v2.tar

:: 解压
tar -xvf xtts_v2.tar

:: 删除临时文件
del xtts_v2.tar

:: 返回项目目录
cd ..
```

### 还原完成后的目录结构

```
D:\projects\gi005\
├── checkpoints_v2/        # ✅ OpenVoice 模型
│   ├── converter/
│   └── base_speakers/
├── tts_model/
│   └── xtts_v2/          # ✅ XTTS 模型
├── ffmpeg.exe            # ✅ FFmpeg
├── ffprobe.exe
├── ffplay.exe
└── ...
```

---

## 4. 安装工具

### 4.1 安装 Python 3.10

> ⚠️ **重要**：必须使用 Python 3.10，不能使用 3.11 或更高版本！

1. 进入 `dependencies` 目录，找到 `python-3.10.11-amd64.exe`
2. 双击运行
3. **务必勾选** ☑️ `Add Python to PATH`
4. 点击 `Install Now`
5. 等待安装完成

**验证安装**：
```cmd
:: 新开一个命令提示符窗口
python --version
```

应该显示：`Python 3.10.11`

### 4.2 安装 Visual Studio Build Tools

1. 进入 `dependencies` 目录，找到 `vs_buildtools.exe`
2. 双击运行
3. 等待加载（需要网络下载组件列表）
4. 在安装界面选择 ☑️ **"使用 C++ 的桌面开发"**
5. 点击安装（会下载约 2-3GB 组件）
6. 等待安装完成

> ⏱️ 这一步可能需要 10-30 分钟

---

## 5. 创建虚拟环境

```cmd
:: 进入项目目录
cd /d D:\projects\gi005

:: 创建虚拟环境
python -m venv venv

:: 激活虚拟环境
venv\Scripts\activate

:: 验证激活成功（命令行前面应该有 (venv) 字样）
```

成功后你会看到：
```
(venv) D:\projects\gi005>
```

---

## 6. 安装依赖

### 6.1 升级 pip

```cmd
:: 确保虚拟环境已激活
python -m pip install --upgrade pip
```

### 6.2 安装 PyTorch

**选项 A：CPU 版本（推荐大多数用户）**
```cmd
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
```

**选项 B：GPU 版本（NVIDIA 显卡用户）**
```cmd
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118
```

### 6.3 安装 TTS 库

```cmd
pip install TTS==0.22.0
```

> ⏱️ 这一步需要较长时间（5-15 分钟）

### 6.4 修复版本冲突

```cmd
pip install "transformers<4.50"
pip install ctranslate2==4.4.0
```

### 6.5 安装其他依赖

```cmd
pip install edge-tts soundfile librosa numpy pydub
```

---

## 7. 克隆外部仓库

### 7.1 克隆 OpenVoice

```cmd
:: 确保在项目根目录
cd /d D:\projects\gi005

:: 克隆 OpenVoice
git clone https://github.com/myshell-ai/OpenVoice.git

:: 进入目录安装
cd OpenVoice
pip install -e .
cd ..
```

**如果 git clone 太慢**，可以：
1. 浏览器访问 https://github.com/myshell-ai/OpenVoice
2. 点击 `Code` -> `Download ZIP`
3. 解压到 `D:\projects\gi005\OpenVoice`
4. 然后运行：
   ```cmd
   cd OpenVoice
   pip install -e .
   cd ..
   ```

---

## 8. 验证安装

### 8.1 创建测试脚本

在项目目录下创建 `test_setup.py`：

```python
import os
import sys

print("=" * 50)
print("环境检测")
print("=" * 50)

# 检查 Python 版本
print(f"Python 版本: {sys.version}")
if sys.version_info[:2] != (3, 10):
    print("⚠️ 警告: 建议使用 Python 3.10")
else:
    print("✅ Python 版本正确")

# 检查 PyTorch
try:
    import torch
    print(f"✅ PyTorch 版本: {torch.__version__}")
    print(f"   CUDA 可用: {torch.cuda.is_available()}")
except ImportError:
    print("❌ PyTorch 未安装")

# 检查 TTS
try:
    import TTS
    print(f"✅ TTS 版本: {TTS.__version__}")
except ImportError:
    print("❌ TTS 未安装")

# 检查 OpenVoice
sys.path.insert(0, 'OpenVoice')
try:
    from openvoice import se_extractor
    from openvoice.api import ToneColorConverter
    print("✅ OpenVoice 导入成功")
except ImportError as e:
    print(f"❌ OpenVoice 导入失败: {e}")

# 检查模型文件
print("\n模型文件检测:")
models = [
    ("checkpoints_v2/converter/config.json", "OpenVoice Converter"),
    ("checkpoints_v2/converter/checkpoint.pth", "OpenVoice Checkpoint"),
    ("tts_model/xtts_v2/config.json", "XTTS Config"),
    ("tts_model/xtts_v2/model.pth", "XTTS Model"),
]

for path, name in models:
    if os.path.exists(path):
        print(f"✅ {name}: 存在")
    else:
        print(f"❌ {name}: 缺失 ({path})")

# 检查 FFmpeg
import shutil
if shutil.which("ffmpeg") or os.path.exists("ffmpeg.exe"):
    print("✅ FFmpeg: 可用")
else:
    print("❌ FFmpeg: 未找到")

print("\n" + "=" * 50)
print("检测完成")
print("=" * 50)
```

### 8.2 运行测试

```cmd
python test_setup.py
```

**期望输出**：
```
==================================================
环境检测
==================================================
Python 版本: 3.10.11 (...)
✅ Python 版本正确
✅ PyTorch 版本: 2.5.1
   CUDA 可用: False
✅ TTS 版本: 0.22.0
✅ OpenVoice 导入成功

模型文件检测:
✅ OpenVoice Converter: 存在
✅ OpenVoice Checkpoint: 存在
✅ XTTS Config: 存在
✅ XTTS Model: 存在
✅ FFmpeg: 可用

==================================================
检测完成
==================================================
```

---

## 9. 开始使用

### 9.1 OpenVoice 音色转换示例

创建 `demo_openvoice.py`：

```python
import sys
import os

# 设置路径
sys.path.insert(0, 'OpenVoice')
os.environ['PATH'] = os.getcwd() + ';' + os.environ['PATH']

from openvoice import se_extractor
from openvoice.api import ToneColorConverter
import torch
import edge_tts
import asyncio

print("步骤 1/4: 加载模型...")
converter = ToneColorConverter('checkpoints_v2/converter/config.json', device='cpu')
converter.load_ckpt('checkpoints_v2/converter/checkpoint.pth')
print("✅ 模型加载完成")

print("步骤 2/4: 生成基础语音...")
async def generate_base():
    tts = edge_tts.Communicate('你好，这是一个音色克隆测试。', 'zh-CN-XiaoxiaoNeural')
    await tts.save('temp_base.wav')
asyncio.run(generate_base())
print("✅ 基础语音生成完成")

print("步骤 3/4: 加载目标音色...")
# 使用预训练的中文音色
target_se = torch.load('checkpoints_v2/base_speakers/ses/zh.pth')
print("✅ 目标音色加载完成")

print("步骤 4/4: 转换音色...")
# 加载源音色
src_se = torch.load('checkpoints_v2/base_speakers/ses/zh.pth')
# 转换
converter.convert(
    audio_src_path='temp_base.wav',
    src_se=src_se,
    tgt_se=target_se,
    output_path='output_demo.wav'
)
print("✅ 音色转换完成")

print("\n🎉 成功！输出文件: output_demo.wav")
print("用播放器打开 output_demo.wav 听听效果吧！")

# 清理临时文件
os.remove('temp_base.wav')
```

运行：
```cmd
python demo_openvoice.py
```

### 9.2 使用自己的声音

如果你想用自己的声音：

```python
import sys
import os
sys.path.insert(0, 'OpenVoice')
os.environ['PATH'] = os.getcwd() + ';' + os.environ['PATH']

from openvoice import se_extractor
from openvoice.api import ToneColorConverter
import torch
import edge_tts
import asyncio

# 加载模型
converter = ToneColorConverter('checkpoints_v2/converter/config.json', device='cpu')
converter.load_ckpt('checkpoints_v2/converter/checkpoint.pth')

# 从你的录音中提取音色
# 注意：录音要求 3-10 秒，清晰的语音，没有背景噪音
your_audio = 'your_voice.wav'  # 替换为你的录音文件
target_se, _ = se_extractor.get_se(your_audio, converter, vad=True)

# 生成基础语音
async def generate():
    tts = edge_tts.Communicate('要说的文字内容', 'zh-CN-XiaoxiaoNeural')
    await tts.save('base.wav')
asyncio.run(generate())

# 转换成你的声音
src_se = torch.load('checkpoints_v2/base_speakers/ses/zh.pth')
converter.convert(
    audio_src_path='base.wav',
    src_se=src_se,
    tgt_se=target_se,
    output_path='output_my_voice.wav'
)

print("完成！输出文件: output_my_voice.wav")
```

---

## 10. 常见错误解决

### 错误 1: python 不是内部或外部命令

**原因**：Python 没有添加到系统 PATH

**解决**：
1. 重新运行 `python-3.10.11-amd64.exe`
2. 选择 "Modify"
3. 勾选 "Add Python to environment variables"
4. 完成后重新打开命令提示符

### 错误 2: Microsoft Visual C++ 14.0 is required

**原因**：没有安装 Visual Studio Build Tools

**解决**：
1. 运行 `dependencies/vs_buildtools.exe`
2. 选择 "使用 C++ 的桌面开发"
3. 安装完成后重试

### 错误 3: ImportError: cannot import name 'BeamSearchScorer'

**原因**：transformers 版本过高

**解决**：
```cmd
pip install "transformers<4.50"
```

### 错误 4: RuntimeError: Library cublas64_12.dll is not found

**原因**：ctranslate2 版本与 CUDA 不匹配

**解决**：
```cmd
pip install ctranslate2==4.4.0
```

### 错误 5: FileNotFoundError: ffmpeg

**原因**：FFmpeg 没有在 PATH 中

**解决**：
1. 确保 `ffmpeg.exe` 在项目根目录
2. 或者将 `ffmpeg.exe` 所在目录添加到系统 PATH

### 错误 6: 内存不足 (Out of Memory)

**原因**：模型太大，内存不够

**解决**：
1. 关闭其他程序
2. 使用 `device='cpu'` 而不是 `device='cuda'`
3. 考虑增加虚拟内存

### 错误 7: 模型文件缺失

**原因**：分卷文件没有正确还原

**解决**：
1. 重新执行第 3 步的还原命令
2. 检查是否有 `.tar` 文件被错误删除
3. 检查分卷文件是否完整（对照 README 中的文件列表）

---

## 📞 获取帮助

如果遇到其他问题：

1. 查看 [VERIFICATION_REPORT.md](./VERIFICATION_REPORT.md) 了解已知问题
2. 查看 [COMPLETE_REPRODUCTION_GUIDE.md](./COMPLETE_REPRODUCTION_GUIDE.md) 获取更详细的说明
3. 在 GitHub Issues 中提问：https://github.com/githubstudycloud/gi005/issues

---

## ✅ 检查清单

完成以下所有步骤后，你就可以开始使用了：

- [ ] 下载并解压项目
- [ ] 还原 dependencies 分卷包
- [ ] 还原 checkpoints_v2 模型
- [ ] 还原 xtts_v2 模型（如果使用 XTTS）
- [ ] 安装 Python 3.10.11
- [ ] 安装 Visual Studio Build Tools
- [ ] 创建并激活虚拟环境
- [ ] 安装 PyTorch 和 TTS
- [ ] 克隆 OpenVoice 仓库
- [ ] 运行 test_setup.py 验证
- [ ] 运行 demo_openvoice.py 测试

🎉 **恭喜你完成了所有设置！**
