# 工具软件

本目录包含项目运行所需的外部工具软件。

## 目录结构

```
tools/
├── ffmpeg/      # 音视频处理工具
│   ├── ffmpeg.exe
│   ├── ffplay.exe
│   └── ffprobe.exe
└── python/      # Python 安装程序
    └── python-3.10.11-amd64.exe
```

## FFmpeg

FFmpeg 用于音频格式转换和处理。

### 下载地址

- 官方: https://ffmpeg.org/download.html
- Windows 构建: https://github.com/BtbN/FFmpeg-Builds/releases

### 安装方式

**方式1: 复制到项目目录**
```
将 ffmpeg.exe, ffplay.exe, ffprobe.exe 复制到项目根目录
```

**方式2: 添加到系统 PATH**
```powershell
# 添加到用户 PATH
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\path\to\ffmpeg\bin", "User")
```

### 验证安装

```bash
ffmpeg -version
```

## Python

推荐使用 Python 3.10.x 版本。

### 下载地址

- 官方: https://www.python.org/downloads/
- 推荐: python-3.10.11-amd64.exe

### 安装选项

安装时请勾选：
- [x] Add Python to PATH
- [x] Install pip

### 验证安装

```bash
python --version  # 应显示 Python 3.10.x
pip --version     # 应显示 pip 版本
```

## 其他工具

| 工具 | 用途 | 下载地址 |
|------|------|----------|
| CUDA Toolkit | GPU 加速 | https://developer.nvidia.com/cuda-toolkit |
| cuDNN | 深度学习加速 | https://developer.nvidia.com/cudnn |
| Git | 版本控制 | https://git-scm.com/downloads |
