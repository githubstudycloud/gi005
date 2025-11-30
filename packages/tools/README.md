# 工具软件

本目录包含项目运行所需的外部工具软件的分卷包。

## 目录结构

```
tools/
├── extracted/                 # 解压后的可执行文件 (已在 .gitignore)
│   ├── ffmpeg.exe            # FFmpeg 主程序
│   ├── ffplay.exe            # FFmpeg 播放器
│   └── ffprobe.exe           # FFmpeg 探测器
├── ffmpeg.pkg.part_aa        # FFmpeg 分卷包 (100MB)
├── ffmpeg.pkg.part_ab        # FFmpeg 分卷包 (100MB)
├── ffmpeg.pkg.part_ac        # FFmpeg 分卷包 (100MB)
├── ffmpeg.pkg.part_ad        # FFmpeg 分卷包 (100MB)
├── ffmpeg.pkg.part_ae        # FFmpeg 分卷包 (100MB)
├── ffmpeg.pkg.part_af        # FFmpeg 分卷包 (~51MB)
├── python.pkg.part_aa        # Python 安装程序 (~28MB)
└── README.md                 # 本文件
```

**注意**: `extracted/` 目录中的文件已在 `.gitignore` 中，不会被提交到仓库。

## 还原方法

### FFmpeg (约551MB)

```bash
# 合并分卷并解压
cd packages/tools
cat ffmpeg.pkg.part_* > ffmpeg.tar
tar -xvf ffmpeg.tar

# 将文件复制到项目根目录或添加到 PATH
cp ffmpeg.exe ffplay.exe ffprobe.exe ../../

# 清理临时文件
rm ffmpeg.tar
```

### Python 安装程序 (约28MB)

```bash
# 还原安装程序
cd packages/tools
cat python.pkg.part_* > python-3.10.11-amd64.exe

# 运行安装（注意勾选 Add to PATH）
./python-3.10.11-amd64.exe
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
