# 前置依赖工具包

本目录包含项目运行所需的前置工具，已打包为分卷文件。

**注意**：文件使用 `.pkg.part_*` 后缀以避免被 .gitignore 忽略。

## 文件清单

| 分卷文件 | 大小 |
|---------|------|
| `tools.pkg.part_aa` | 95MB |
| `tools.pkg.part_ab` | 95MB |
| `tools.pkg.part_ac` | 95MB |
| `tools.pkg.part_ad` | 95MB |
| `tools.pkg.part_ae` | 95MB |
| `tools.pkg.part_af` | 95MB |
| `tools.pkg.part_ag` | 14MB |

**总计**: 约 585MB，共 7 个分卷

## 包含的工具

| 文件 | 版本 | 说明 | 大小 |
|------|------|------|------|
| `ffmpeg.exe` | latest | 音视频处理工具 | 184MB |
| `ffprobe.exe` | latest | 音视频信息查看 | 183MB |
| `ffplay.exe` | latest | 音视频播放器 | 186MB |
| `python-3.10.11-amd64.exe` | 3.10.11 | Python 安装程序 | 28MB |
| `vs_buildtools.exe` | 2022 | Visual Studio 构建工具 | 4.3MB |

## 工具与引擎/功能对应关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          工具依赖关系图                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  python-3.10.11-amd64.exe                                                   │
│  ├── 所有引擎的运行环境                                                      │
│  │   ├── XTTS-v2      (TTS 库依赖 Python 3.10)                              │
│  │   ├── OpenVoice    (PyTorch 模型)                                        │
│  │   └── GPT-SoVITS   (可选，高级中文克隆)                                   │
│  └── 注意：必须是 3.10 版本，3.11+ 不兼容 TTS 库                             │
│                                                                             │
│  vs_buildtools.exe                                                          │
│  ├── 编译 Python C++ 扩展                                                   │
│  │   ├── librosa      (音频分析库，XTTS/OpenVoice 都需要)                    │
│  │   ├── PyTorch      (深度学习框架)                                        │
│  │   └── soundfile    (音频读写)                                            │
│  └── 首次 pip install 时需要，编译完成后可卸载                               │
│                                                                             │
│  ffmpeg.exe / ffprobe.exe / ffplay.exe                                      │
│  ├── XTTS-v2 引擎                                                           │
│  │   └── 音频格式转换、重采样（TTS 库内部调用）                               │
│  ├── OpenVoice 引擎                                                         │
│  │   └── 音频预处理、VAD 切分、格式转换                                      │
│  ├── Whisper 模型（语音识别）                                               │
│  │   └── 音频解码、采样率转换                                               │
│  └── edge-tts 基础语音                                                      │
│      └── 输出音频后处理                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 详细说明

#### 1. FFmpeg 系列（音频处理核心）

| 工具 | 被谁调用 | 具体用途 |
|------|----------|----------|
| `ffmpeg.exe` | XTTS-v2, OpenVoice, Whisper | 音频格式转换（mp3→wav）、重采样（统一到 22050Hz/16000Hz）、声道转换（立体声→单声道） |
| `ffprobe.exe` | TTS 库, librosa | 获取音频元信息（时长、采样率、声道数），用于预处理判断 |
| `ffplay.exe` | 开发调试 | 快速播放生成的音频文件，验证输出质量 |

**缺少 FFmpeg 的错误示例**：
```
FileNotFoundError: [WinError 2] 系统找不到指定的文件: 'ffmpeg'
RuntimeError: ffmpeg not found in PATH
```

#### 2. Python 3.10.11（运行环境）

| 依赖它的组件 | 原因 |
|--------------|------|
| TTS 库 (Coqui) | 官方仅支持 Python 3.9-3.10，3.11 存在兼容性问题 |
| PyTorch 2.x | 需要 Python 3.8-3.11 |
| transformers | XTTS 模型加载需要 |
| OpenVoice | 基于 PyTorch 的音色转换模型 |

**版本限制原因**：
- Python 3.11+ 修改了部分内部 API，导致 TTS 库编译失败
- 一些依赖包（如 `webrtcvad`）尚未适配 Python 3.12

#### 3. Visual Studio Build Tools（编译工具）

| 被谁需要 | 编译什么 |
|----------|----------|
| `pip install TTS` | 编译 `phonemizer`、`gruut` 等音素处理库 |
| `pip install librosa` | 编译 `numba`、`llvmlite` 等数值计算库 |
| `pip install PyTorch` | 可能需要编译自定义 CUDA 算子（GPU 版本） |
| `pip install webrtcvad` | 编译 VAD（语音活动检测）C 扩展 |

**缺少 Build Tools 的错误示例**：
```
error: Microsoft Visual C++ 14.0 or greater is required
error: command 'cl.exe' failed: No such file or directory
```

## 各引擎的工具依赖汇总

| 引擎 | FFmpeg | Python 3.10 | VS Build Tools |
|------|--------|-------------|----------------|
| XTTS-v2 | 必需 | 必需 | 首次安装需要 |
| OpenVoice | 必需 | 必需 | 首次安装需要 |
| GPT-SoVITS | 必需 | 必需 | 首次安装需要 |
| edge-tts（基础 TTS） | 可选 | 必需 | 不需要 |

## 还原方法

### Linux / macOS / Git Bash

```bash
cd dependencies

# 合并分卷并解压
cat tools.pkg.part_* | tar -xvf -

# 文件会解压到当前目录
ls -la *.exe
```

### Windows CMD

```cmd
cd dependencies

:: 合并分卷
copy /b tools.pkg.part_* tools.tar

:: 解压
tar -xvf tools.tar

:: 清理
del tools.tar
```

### Windows PowerShell

```powershell
cd dependencies

# 合并分卷
Get-Content tools.pkg.part_* -Raw -Encoding Byte | Set-Content tools.tar -Encoding Byte

# 解压
tar -xvf tools.tar

# 清理
Remove-Item tools.tar
```

## 安装说明

### 1. Python 3.10.11

**重要**：必须使用 Python 3.10，不支持 3.11 或更高版本！

```cmd
:: 解压后运行安装程序
python-3.10.11-amd64.exe

:: 安装时务必勾选：
:: ✅ Add Python to PATH
:: ✅ Install for all users (可选)
```

验证安装：
```cmd
python --version
:: 应该显示: Python 3.10.11
```

### 2. Visual Studio Build Tools

这是编译 Python C++ 扩展所必需的。

```cmd
:: 解压后运行
vs_buildtools.exe

:: 在安装界面中选择：
:: ✅ "使用 C++ 的桌面开发" 工作负载
:: 或至少选择：
::   ✅ MSVC v143 - VS 2022 C++ x64/x86 生成工具
::   ✅ Windows 10/11 SDK
```

**注意**：这只是一个在线安装器，运行后会下载约 2-3GB 的组件。

### 3. FFmpeg

FFmpeg 是音频处理必需的工具。

**方法 A：放到项目目录（推荐）**
```cmd
:: 解压后，将 exe 文件移动到项目根目录
move ffmpeg.exe ..\
move ffprobe.exe ..\
move ffplay.exe ..\
```

**方法 B：添加到系统 PATH**
```cmd
:: 1. 将 exe 文件放到固定目录，如 C:\ffmpeg\
mkdir C:\ffmpeg
move ffmpeg.exe C:\ffmpeg\
move ffprobe.exe C:\ffmpeg\
move ffplay.exe C:\ffmpeg\

:: 2. 添加到系统环境变量 PATH
:: 控制面板 -> 系统 -> 高级系统设置 -> 环境变量
:: 在 Path 中添加: C:\ffmpeg
```

验证安装：
```cmd
ffmpeg -version
```

## 工具来源

| 工具 | 下载地址 |
|------|----------|
| Python 3.10.11 | https://www.python.org/downloads/release/python-31011/ |
| FFmpeg | https://github.com/BtbN/FFmpeg-Builds/releases |
| VS Build Tools | https://visualstudio.microsoft.com/visual-cpp-build-tools/ |

## 打包命令参考

```bash
# 如果需要重新打包
tar -cvf - ffmpeg.exe ffplay.exe ffprobe.exe python-3.10.11-amd64.exe vs_buildtools.exe | split -b 95m - tools.pkg.part_
```
