# WSL2 Ubuntu 22.04 D 盘安装详细指南

Voice Clone TTS 项目的 WSL2 + CUDA + PyTorch 完整安装指南。

**版本**: 1.0.0
**更新日期**: 2025-12-02
**目标安装路径**: `D:\wsl\ubuntu22`

---

## 📋 目录

1. [系统要求](#系统要求)
2. [安装概述](#安装概述)
3. [第一阶段：Windows 端准备](#第一阶段windows-端准备)
4. [第二阶段：WSL2 安装](#第二阶段wsl2-安装)
5. [第三阶段：Ubuntu 环境配置](#第三阶段ubuntu-环境配置)
6. [第四阶段：CUDA 和 PyTorch](#第四阶段cuda-和-pytorch)
7. [第五阶段：项目部署](#第五阶段项目部署)
8. [常用命令速查](#常用命令速查)
9. [故障排除](#故障排除)
10. [性能优化](#性能优化)

---

## 系统要求

### Windows 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 版本 2004 (Build 19041) 或更高版本，或 Windows 11 |
| CPU | 支持虚拟化 (Intel VT-x / AMD-V) |
| 内存 | 16GB 或更高（推荐 32GB） |
| 磁盘 | SSD，D 盘可用空间 50GB 以上 |
| GPU | NVIDIA GTX 1060 或更高（推荐 RTX 3060 或更高） |

### NVIDIA 驱动要求

- **驱动版本**: 525.60.13 或更高
- **支持的 CUDA 版本**: 12.0+
- **下载地址**: https://www.nvidia.com/Download/index.aspx

> ⚠️ **重要**: WSL2 使用 Windows 端的 NVIDIA 驱动，**不要**在 WSL2 内部安装 NVIDIA 驱动！

---

## 安装概述

### 安装流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    第一阶段：Windows 端准备                   │
├─────────────────────────────────────────────────────────────┤
│  1. 检查 Windows 版本和虚拟化                                │
│  2. 安装/更新 NVIDIA 驱动（Windows 端）                       │
│  3. 启用 WSL 和虚拟机平台功能                                 │
│  4. 安装 WSL2 Linux 内核更新                                  │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    第二阶段：WSL2 安装                        │
├─────────────────────────────────────────────────────────────┤
│  1. 下载 Ubuntu 22.04 WSL 镜像                               │
│  2. 导入到 D:\wsl\ubuntu22                                   │
│  3. 配置默认用户                                             │
│  4. 验证安装                                                 │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  第三阶段：Ubuntu 环境配置                    │
├─────────────────────────────────────────────────────────────┤
│  1. 更新系统包                                               │
│  2. 安装开发工具（build-essential, cmake, git 等）           │
│  3. 安装 Python 3 + pip + venv                               │
│  4. 安装音视频工具（FFmpeg, Sox 等）                          │
│  5. 配置 Git 和 SSH                                          │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  第四阶段：CUDA 和 PyTorch                    │
├─────────────────────────────────────────────────────────────┤
│  1. 安装 CUDA Toolkit 12.1 (WSL2 版本)                       │
│  2. 安装 cuDNN                                               │
│  3. 安装 PyTorch 2.1 with CUDA                               │
│  4. 验证 GPU 支持                                            │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    第五阶段：项目部署                         │
├─────────────────────────────────────────────────────────────┤
│  1. 克隆项目仓库                                             │
│  2. 创建虚拟环境并安装依赖                                    │
│  3. 恢复模型文件                                             │
│  4. 创建启动脚本                                             │
│  5. 启动服务                                                 │
└─────────────────────────────────────────────────────────────┘
```

### 预计时间

| 阶段 | 预计时间 | 网络需求 |
|------|----------|----------|
| 第一阶段 | 10-15 分钟 | 中等 |
| 第二阶段 | 15-30 分钟 | 高（下载 ~500MB） |
| 第三阶段 | 10-20 分钟 | 高 |
| 第四阶段 | 20-40 分钟 | 高（下载 ~3GB） |
| 第五阶段 | 10-30 分钟 | 高 |
| **总计** | **1-2 小时** | - |

---

## 第一阶段：Windows 端准备

### 步骤 1.1：检查 Windows 版本

打开 PowerShell，运行：

```powershell
winver
```

确保版本为 **Windows 10 版本 2004** 或更高，或 **Windows 11**。

### 步骤 1.2：检查虚拟化支持

打开任务管理器（Ctrl + Shift + Esc）→ 性能 → CPU，确认"虚拟化"显示为"已启用"。

如果未启用，需要在 BIOS 中启用：
- Intel CPU: 启用 Intel VT-x
- AMD CPU: 启用 AMD-V / SVM Mode

### 步骤 1.3：安装 NVIDIA 驱动（Windows 端）

1. 访问 https://www.nvidia.com/Download/index.aspx
2. 选择您的 GPU 型号
3. 下载并安装最新驱动（推荐 Game Ready 或 Studio 驱动）
4. 重启计算机

验证驱动安装：

```powershell
nvidia-smi
```

应显示驱动版本和 CUDA 版本。

### 步骤 1.4：启用 WSL 功能

以**管理员身份**打开 PowerShell，运行：

```powershell
# 启用 WSL 功能
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 启用虚拟机平台
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

**重启计算机**。

### 步骤 1.5：安装 WSL2 内核更新

1. 下载内核更新包：https://aka.ms/wsl2kernel
2. 运行安装程序
3. 设置 WSL2 为默认版本：

```powershell
wsl --set-default-version 2
```

---

## 第二阶段：WSL2 安装

### 方式 A：使用自动脚本（推荐）

1. 以**管理员身份**打开 PowerShell
2. 运行安装脚本：

```powershell
cd D:\data\PycharmProjects\PythonProject1\scripts
.\install-wsl2-to-d-drive.ps1
```

3. 按照脚本提示操作

### 方式 B：手动安装

#### 步骤 2.1：下载 Ubuntu 镜像

```powershell
# 创建临时目录
mkdir C:\Temp\wsl-install -Force

# 下载 Ubuntu 22.04 WSL 镜像
$url = "https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-wsl.rootfs.tar.gz"
Invoke-WebRequest -Uri $url -OutFile "C:\Temp\wsl-install\ubuntu-22.04.tar.gz"
```

或使用浏览器下载：
https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-wsl.rootfs.tar.gz

#### 步骤 2.2：创建安装目录

```powershell
mkdir D:\wsl\ubuntu22 -Force
```

#### 步骤 2.3：导入发行版

```powershell
wsl --import Ubuntu-22.04 D:\wsl\ubuntu22 C:\Temp\wsl-install\ubuntu-22.04.tar.gz
```

#### 步骤 2.4：验证安装

```powershell
wsl --list --verbose
```

应显示：

```
  NAME            STATE           VERSION
* Ubuntu-22.04    Stopped         2
```

#### 步骤 2.5：启动并配置用户

```powershell
# 启动 WSL
wsl -d Ubuntu-22.04

# 在 WSL 内创建用户（替换 yourusername 为您的用户名）
useradd -m -s /bin/bash yourusername
passwd yourusername
usermod -aG sudo yourusername

# 创建配置文件设置默认用户
cat > /etc/wsl.conf << EOF
[user]
default=yourusername

[boot]
systemd=true

[interop]
appendWindowsPath=true
EOF

# 退出 WSL
exit
```

```powershell
# 重启 WSL 使配置生效
wsl --shutdown
wsl -d Ubuntu-22.04
```

---

## 第三阶段：Ubuntu 环境配置

### 方式 A：使用自动脚本（推荐）

在 WSL Ubuntu 中运行：

```bash
cd /mnt/d/data/PycharmProjects/PythonProject1/scripts
chmod +x wsl2-setup-cuda-pytorch.sh
./wsl2-setup-cuda-pytorch.sh
```

### 方式 B：手动配置

#### 步骤 3.1：更新系统

```bash
sudo apt update
sudo apt upgrade -y
```

#### 步骤 3.2：安装基础开发工具

```bash
sudo apt install -y \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    git \
    git-lfs \
    curl \
    wget \
    vim \
    nano \
    htop \
    tmux \
    tree \
    unzip \
    zip \
    net-tools \
    ca-certificates \
    gnupg \
    lsb-release
```

#### 步骤 3.3：安装 Python 环境

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev

# 更新 pip
python3 -m pip install --upgrade pip setuptools wheel
```

#### 步骤 3.4：安装音视频工具

```bash
sudo apt install -y \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libsndfile1 \
    libsndfile1-dev \
    portaudio19-dev \
    sox \
    libsox-dev
```

#### 步骤 3.5：配置 Git

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main
git config --global core.autocrlf input
git lfs install
```

#### 步骤 3.6：配置 SSH

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your.email@example.com" -f ~/.ssh/id_ed25519 -N ""

# 启动 ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 显示公钥
cat ~/.ssh/id_ed25519.pub
```

将公钥添加到 GitHub: https://github.com/settings/keys

---

## 第四阶段：CUDA 和 PyTorch

### 步骤 4.1：验证 GPU 可见性

```bash
nvidia-smi
```

如果显示 GPU 信息，说明 WSL2 已正确识别 GPU。

### 步骤 4.2：安装 CUDA Toolkit

```bash
# 安装 CUDA keyring
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
rm cuda-keyring_1.1-1_all.deb

# 更新并安装 CUDA
sudo apt update
sudo apt install -y cuda-toolkit-12-1

# 配置环境变量
echo '
# CUDA 环境变量
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
' >> ~/.bashrc

source ~/.bashrc
```

### 步骤 4.3：安装 cuDNN

```bash
sudo apt install -y libcudnn8 libcudnn8-dev
```

### 步骤 4.4：安装 PyTorch

```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 步骤 4.5：验证安装

```bash
python3 -c "
import torch
print(f'PyTorch 版本: {torch.__version__}')
print(f'CUDA 可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA 版本: {torch.version.cuda}')
    print(f'cuDNN 版本: {torch.backends.cudnn.version()}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"
```

预期输出：

```
PyTorch 版本: 2.1.0+cu121
CUDA 可用: True
CUDA 版本: 12.1
cuDNN 版本: 8902
GPU: NVIDIA GeForce RTX 3060
```

---

## 第五阶段：项目部署

### 步骤 5.1：克隆项目

```bash
mkdir -p ~/projects
cd ~/projects
git clone git@github.com:githubstudycloud/gi005.git
cd gi005
```

### 步骤 5.2：创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### 步骤 5.3：安装项目依赖

```bash
# 安装 PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装项目依赖
pip install -r requirements.txt
```

### 步骤 5.4：恢复模型文件

```bash
# XTTS-v2 模型
cd packages/models/xtts_v2
cat xtts_v2_full.pkg.part_* > xtts_v2.tar
mkdir -p extracted
tar -xvf xtts_v2.tar -C extracted/
cd ~/projects/gi005

# OpenVoice 模型（如果存在）
cd packages/models/openvoice
cat checkpoints_v2.pkg.part_* > checkpoints.tar
mkdir -p extracted
tar -xvf checkpoints.tar -C extracted/
cd ~/projects/gi005
```

### 步骤 5.5：创建启动脚本

```bash
# Standalone 模式
cat > start-standalone.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.main standalone --engine xtts --port 8080
EOF
chmod +x start-standalone.sh

# Gateway 模式
cat > start-gateway.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.main gateway --port 8080
EOF
chmod +x start-gateway.sh

# Worker 模式
cat > start-xtts-worker.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load
EOF
chmod +x start-xtts-worker.sh
```

### 步骤 5.6：启动服务

```bash
# 独立模式
./start-standalone.sh

# 或分布式模式
# 终端 1: ./start-gateway.sh
# 终端 2: ./start-xtts-worker.sh
```

### 步骤 5.7：访问服务

- 状态页: http://localhost:8080/status
- 管理页: http://localhost:8080/admin
- API 文档: http://localhost:8080/docs

---

## 常用命令速查

### WSL 管理

```powershell
# 启动 Ubuntu
wsl -d Ubuntu-22.04

# 关闭所有 WSL
wsl --shutdown

# 查看已安装的发行版
wsl --list --verbose

# 设置默认发行版
wsl --set-default Ubuntu-22.04

# 卸载发行版
wsl --unregister Ubuntu-22.04

# 导出发行版
wsl --export Ubuntu-22.04 D:\backup\ubuntu-22.04.tar

# 导入发行版
wsl --import Ubuntu-22.04 D:\wsl\ubuntu22 D:\backup\ubuntu-22.04.tar
```

### GPU 监控

```bash
# 查看 GPU 状态
nvidia-smi

# 实时监控 GPU
watch -n 1 nvidia-smi

# 查看 CUDA 版本
nvcc --version
```

### 项目快捷命令

```bash
# 添加到 ~/.bashrc
alias gi005="cd ~/projects/gi005"
alias gi005-start="cd ~/projects/gi005 && ./start-standalone.sh"
alias gi005-gateway="cd ~/projects/gi005 && ./start-gateway.sh"
alias gi005-worker="cd ~/projects/gi005 && ./start-xtts-worker.sh"
alias gi005-venv="cd ~/projects/gi005 && source venv/bin/activate"
```

### 虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 退出虚拟环境
deactivate

# 安装依赖
pip install -r requirements.txt

# 导出依赖
pip freeze > requirements.txt
```

---

## 故障排除

### 问题 1：nvidia-smi 显示 "command not found"

**原因**: Windows NVIDIA 驱动未正确安装或版本过低

**解决方案**:
1. 在 Windows 中更新 NVIDIA 驱动到最新版本
2. 重启计算机
3. 重启 WSL: `wsl --shutdown`

### 问题 2：CUDA 可用显示 False

**原因**: PyTorch 未正确安装 CUDA 版本

**解决方案**:
```bash
# 卸载当前 PyTorch
pip uninstall torch torchvision torchaudio

# 安装 CUDA 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 问题 3：WSL 启动缓慢

**解决方案**:
1. 确保使用 WSL2（非 WSL1）
2. 在 `%USERPROFILE%\.wslconfig` 中限制内存：

```ini
[wsl2]
memory=8GB
processors=4
swap=4GB
```

### 问题 4：Git clone 失败 "Permission denied"

**解决方案**:
1. 检查 SSH 密钥: `ls -la ~/.ssh/`
2. 测试 SSH 连接: `ssh -T git@github.com`
3. 重新添加公钥到 GitHub

### 问题 5：磁盘空间不足

**解决方案**:
```bash
# 清理 apt 缓存
sudo apt clean
sudo apt autoremove

# 清理 pip 缓存
pip cache purge

# 查看大文件
du -sh * | sort -hr | head -20
```

### 问题 6：WSL2 无法访问网络

**解决方案**:
```powershell
# 重启 WSL
wsl --shutdown

# 重置网络
netsh winsock reset
netsh int ip reset

# 重启计算机
```

---

## 性能优化

### 1. 内存配置

创建 `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
memory=16GB          # 限制最大内存
processors=8         # 限制 CPU 核心数
swap=8GB            # 交换空间大小
localhostForwarding=true
```

### 2. 磁盘 I/O 优化

项目文件应放在 WSL 文件系统内（`~/projects`），而非 `/mnt/c` 或 `/mnt/d`，以获得最佳 I/O 性能。

### 3. GPU 内存优化

```python
# 在代码中限制 GPU 内存
import torch
torch.cuda.set_per_process_memory_fraction(0.8)  # 限制使用 80% GPU 内存
```

### 4. 模型加载优化

```python
# 使用 half precision
model = model.half()  # FP16

# 或使用 8-bit 量化
# pip install bitsandbytes
model = model.load_in_8bit()
```

---

## 附录

### A. 已安装组件清单

| 类别 | 组件 | 版本 |
|------|------|------|
| 系统 | Ubuntu | 22.04 LTS |
| 编译器 | GCC | 11.x |
| 构建工具 | CMake | 3.x |
| 版本控制 | Git | 2.x |
| Python | Python | 3.10 |
| CUDA | CUDA Toolkit | 12.1 |
| 深度学习 | PyTorch | 2.1.0 |
| 深度学习 | cuDNN | 8.x |
| 音频处理 | FFmpeg | 4.x |
| 音频处理 | Sox | 14.x |
| TTS | Coqui TTS | latest |

### B. 环境变量

```bash
# ~/.bashrc 中应包含

# CUDA
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Python
export PATH=$HOME/.local/bin:$PATH

# 项目
export GI005_HOME=$HOME/projects/gi005
```

### C. 文件结构

```
D:\wsl\ubuntu22\
└── ext4.vhdx              # WSL2 虚拟磁盘

~/projects/gi005/          # 项目目录
├── venv/                  # Python 虚拟环境
├── src/                   # 源代码
├── packages/
│   └── models/
│       ├── xtts_v2/       # XTTS 模型
│       └── openvoice/     # OpenVoice 模型
├── start-standalone.sh    # 独立模式启动脚本
├── start-gateway.sh       # Gateway 启动脚本
├── start-xtts-worker.sh   # Worker 启动脚本
└── requirements.txt       # Python 依赖
```

---

**文档版本**: 1.0.0
**创建日期**: 2025-12-02
**维护者**: Voice Clone TTS 项目团队
