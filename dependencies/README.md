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
