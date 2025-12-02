# WSL2 部署指南 - Voice Clone TTS

> 在 Windows WSL2 环境中部署 Voice Clone TTS 微服务系统

## 目录

- [系统要求](#系统要求)
- [部署架构](#部署架构)
- [安装步骤](#安装步骤)
  - [阶段 1: WSL2 安装](#阶段-1-wsl2-安装)
  - [阶段 2: Linux 环境配置](#阶段-2-linux-环境配置)
  - [阶段 3: 项目部署](#阶段-3-项目部署)
  - [阶段 4: GPU 支持（可选）](#阶段-4-gpu-支持可选)
- [验证和测试](#验证和测试)
- [常见问题](#常见问题)

---

## 系统要求

### Windows 版本要求

- **Windows 10**: 版本 2004 及更高版本 (Build 19041 及更高版本)
- **Windows 11**: 所有版本
- **架构**: x64 或 ARM64

### 硬件要求

- **CPU**: 支持虚拟化（Intel VT-x 或 AMD-V）
- **内存**: 最低 8GB，推荐 16GB+
- **磁盘**: 至少 20GB 可用空间
- **GPU**（可选）: NVIDIA GPU（用于加速推理）

### 检查当前 Windows 版本

```powershell
# 在 PowerShell 中运行
winver
# 或
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
```

---

## 部署架构

```
Windows 主机
    ├── WSL2 (Ubuntu 22.04)
    │   ├── Python 3.10
    │   ├── FFmpeg
    │   ├── Voice Clone TTS
    │   │   ├── Gateway (端口 8080)
    │   │   └── Workers (端口 8001-8003)
    │   └── Git 仓库 (git@github.com:githubstudycloud/gi005.git)
    └── 端口映射
        ├── localhost:8080 → WSL2:8080 (Gateway)
        ├── localhost:8001 → WSL2:8001 (XTTS Worker)
        └── localhost:8002 → WSL2:8002 (OpenVoice Worker)
```

---

## 安装步骤

### 阶段 1: WSL2 安装

#### 步骤 1.1: 启用 WSL 功能

**方法 1: 自动安装（推荐）**

以管理员身份打开 PowerShell：

```powershell
# 安装 WSL2 和默认 Ubuntu 发行版
wsl --install

# 查看可用的 Linux 发行版
wsl --list --online

# 安装指定发行版（推荐 Ubuntu 22.04）
wsl --install -d Ubuntu-22.04
```

**方法 2: 手动安装**

如果自动安装失败，手动启用功能：

```powershell
# 1. 启用 WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 2. 启用虚拟机平台
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 3. 重启计算机
shutdown /r /t 0
```

#### 步骤 1.2: 下载并安装 WSL2 更新包

```powershell
# 下载 WSL2 Linux 内核更新包
# 访问: https://aka.ms/wsl2kernel
# 或直接下载: https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi

# 运行安装程序（双击下载的 .msi 文件）
```

#### 步骤 1.3: 设置 WSL2 为默认版本

```powershell
wsl --set-default-version 2
```

#### 步骤 1.4: 安装 Ubuntu 22.04

```powershell
# 从 Microsoft Store 安装
wsl --install -d Ubuntu-22.04

# 或从 Microsoft Store 应用手动安装
# 搜索 "Ubuntu 22.04" 并点击安装
```

#### 步骤 1.5: 首次启动和配置

```bash
# 启动 Ubuntu
wsl

# 首次启动会要求创建用户
# 输入用户名（建议使用小写，如: john）
# 输入密码（会隐藏，不显示）
# 确认密码
```

#### 步骤 1.6: 验证 WSL2 安装

在 PowerShell 中：

```powershell
# 检查已安装的发行版和版本
wsl --list --verbose

# 输出示例:
#   NAME            STATE           VERSION
# * Ubuntu-22.04    Running         2
```

---

### 阶段 2: Linux 环境配置

进入 WSL2 Ubuntu 环境：

```bash
wsl
```

#### 步骤 2.1: 更新系统

```bash
# 更新包列表
sudo apt update

# 升级已安装的包
sudo apt upgrade -y
```

#### 步骤 2.2: 安装基础工具

```bash
# 安装开发工具
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    vim \
    ca-certificates \
    software-properties-common

# 安装 FFmpeg（音频处理）
sudo apt install -y ffmpeg

# 验证安装
git --version
ffmpeg -version
```

#### 步骤 2.3: 安装 Python 3.10

```bash
# Ubuntu 22.04 默认带 Python 3.10
python3 --version

# 安装 pip 和 venv
sudo apt install -y python3-pip python3-venv

# 验证
pip3 --version
```

#### 步骤 2.4: 配置 Git

```bash
# 配置用户信息（使用您的 GitHub 信息）
git config --global user.name "githubstudycloud"
git config --global user.email "githubstudycloud@users.noreply.github.com"

# 配置代理（如果需要）
git config --global http.proxy socks5://192.168.0.98:10800
git config --global https.proxy socks5://192.168.0.98:10800

# 验证配置
git config --global --list
```

#### 步骤 2.5: 配置 SSH（用于 GitHub）

```bash
# 生成 SSH 密钥（如果还没有）
ssh-keygen -t ed25519 -C "githubstudycloud@users.noreply.github.com"

# 按 Enter 使用默认路径
# 可选: 输入密码保护密钥

# 启动 SSH agent
eval "$(ssh-agent -s)"

# 添加 SSH 私钥
ssh-add ~/.ssh/id_ed25519

# 查看公钥（需要添加到 GitHub）
cat ~/.ssh/id_ed25519.pub
```

**将公钥添加到 GitHub:**

1. 复制上面命令输出的公钥
2. 访问: https://github.com/settings/keys
3. 点击 "New SSH key"
4. 粘贴公钥，保存

**测试 SSH 连接:**

```bash
ssh -T git@github.com

# 如果成功，会看到:
# Hi githubstudycloud! You've successfully authenticated...
```

---

### 阶段 3: 项目部署

#### 步骤 3.1: 克隆项目仓库

```bash
# 创建项目目录
mkdir -p ~/projects
cd ~/projects

# 克隆仓库
git clone git@github.com:githubstudycloud/gi005.git
cd gi005

# 查看项目结构
ls -la
```

#### 步骤 3.2: 创建 Python 虚拟环境

```bash
# 在项目根目录
cd ~/projects/gi005

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

#### 步骤 3.3: 安装项目依赖

```bash
# 如果有 requirements.txt
pip install -r requirements.txt

# 如果没有，根据 README 安装依赖
# 查看 README
cat README.md
```

#### 步骤 3.4: 恢复模型文件

根据项目文档恢复模型：

```bash
# XTTS-v2 模型
cd packages/models/xtts_v2
cat xtts_v2_full.pkg.part_* > xtts_v2.tar
mkdir -p extracted
tar -xvf xtts_v2.tar -C extracted/

# OpenVoice 模型
cd ../openvoice
cat checkpoints_v2.pkg.part_* > checkpoints.tar
mkdir -p extracted
tar -xvf checkpoints.tar -C extracted/

# 返回项目根目录
cd ~/projects/gi005
```

#### 步骤 3.5: 配置环境变量（如果需要）

```bash
# 创建 .env 文件
cat > .env <<EOF
# Gateway 配置
GATEWAY_PORT=8080

# Worker 配置
WORKER_PORTS=8001,8002

# 模型路径
MODEL_PATH=/home/$(whoami)/projects/gi005/packages/models
EOF
```

#### 步骤 3.6: 测试启动

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试独立模式启动
python -m src.main standalone --engine xtts --port 8080

# 如果启动成功，会看到:
# INFO: Started server process
# INFO: Uvicorn running on http://0.0.0.0:8080
```

---

### 阶段 4: GPU 支持（可选）

如果您有 NVIDIA GPU 并想加速推理：

#### 步骤 4.1: 检查 GPU 兼容性

在 Windows PowerShell 中：

```powershell
# 检查 NVIDIA GPU
nvidia-smi
```

#### 步骤 4.2: 安装 NVIDIA CUDA on WSL2

**在 Windows 上:**

1. 下载并安装 NVIDIA GPU 驱动（WSL 专用）
   - 访问: https://developer.nvidia.com/cuda/wsl
   - 下载并安装最新驱动

**在 WSL2 Ubuntu 中:**

```bash
# 安装 CUDA Toolkit
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-3

# 添加到 PATH
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 验证
nvcc --version
```

#### 步骤 4.3: 安装 PyTorch with CUDA

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装 PyTorch with CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 验证 GPU 可用性
python -c "import torch; print(torch.cuda.is_available())"
# 应该输出: True
```

---

## 验证和测试

### 1. 系统环境验证

```bash
# 在 WSL2 中运行
cd ~/projects/gi005

# 检查 Python 版本
python3 --version  # 应该是 3.10.x

# 检查 FFmpeg
ffmpeg -version

# 检查 Git
git --version

# 检查虚拟环境
source venv/bin/activate
pip list
```

### 2. 服务启动测试

#### 独立模式测试

```bash
# 启动独立服务器
source venv/bin/activate
python -m src.main standalone --engine xtts --port 8080
```

在 Windows 浏览器中访问:
- http://localhost:8080/status
- http://localhost:8080/admin

#### 分布式模式测试

**终端 1 - Gateway:**

```bash
cd ~/projects/gi005
source venv/bin/activate
python -m src.main gateway --port 8080
```

**终端 2 - XTTS Worker:**

```bash
cd ~/projects/gi005
source venv/bin/activate
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load
```

### 3. API 测试

在 Windows PowerShell 或 WSL2 中：

```bash
# 健康检查
curl http://localhost:8080/health

# 查看 worker 列表
curl http://localhost:8080/api/workers

# 测试语音合成（需要先提取语音）
curl -X POST http://localhost:8080/api/synthesize \
    -H "Content-Type: application/json" \
    -d '{"text":"Hello World","language":"en"}' \
    --output output.wav
```

---

## 常见问题

### Q1: WSL2 安装失败，提示"需要启用虚拟化"

**解决方案:**

1. 进入 BIOS 设置
2. 启用 Intel VT-x 或 AMD-V
3. 保存并重启

### Q2: 无法访问 localhost:8080

**检查端口映射:**

```bash
# 在 WSL2 中查看监听端口
netstat -tuln | grep 8080

# 在 Windows PowerShell 中
netstat -ano | findstr :8080
```

**解决方案:**

WSL2 自动端口转发，但有时需要手动配置防火墙：

```powershell
# 以管理员身份运行 PowerShell
New-NetFirewallRule -DisplayName "WSL2 Gateway" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

### Q3: Git clone 速度很慢

**解决方案:**

```bash
# 配置代理
git config --global http.proxy socks5://192.168.0.98:10800
git config --global https.proxy socks5://192.168.0.98:10800

# 或使用 SSH
git clone git@github.com:githubstudycloud/gi005.git
```

### Q4: 如何在 Windows 和 WSL2 之间传输文件？

**Windows 访问 WSL2:**

```
\\wsl$\Ubuntu-22.04\home\<username>\projects\gi005
```

**WSL2 访问 Windows:**

```bash
cd /mnt/d/data/PycharmProjects/PythonProject1
```

### Q5: 虚拟环境激活后，pip 命令找不到

**解决方案:**

```bash
# 确保正确激活虚拟环境
source venv/bin/activate

# 检查 pip 路径
which pip  # 应该指向 venv/bin/pip

# 如果不对，重新创建虚拟环境
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### Q6: CUDA 不可用（torch.cuda.is_available() 返回 False）

**检查清单:**

```bash
# 1. 检查 NVIDIA 驱动
nvidia-smi

# 2. 检查 CUDA Toolkit
nvcc --version

# 3. 检查 PyTorch 版本
python -c "import torch; print(torch.__version__)"

# 4. 重新安装 PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Q7: 模型加载失败

**检查模型路径:**

```bash
# 验证模型文件存在
ls -la packages/models/xtts_v2/extracted/
ls -la packages/models/openvoice/extracted/

# 检查分卷包是否完整
cd packages/models/xtts_v2
ls -la *.pkg.part_*

# 重新解压
cat xtts_v2_full.pkg.part_* > xtts_v2.tar
tar -xvf xtts_v2.tar -C extracted/
```

### Q8: 如何重启 WSL2？

```powershell
# 在 Windows PowerShell 中
wsl --shutdown

# 重新启动
wsl
```

### Q9: WSL2 占用内存过高

**限制 WSL2 内存:**

在 Windows 用户目录创建 `.wslconfig`:

```
C:\Users\<用户名>\.wslconfig
```

内容:

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
```

重启 WSL2:

```powershell
wsl --shutdown
wsl
```

### Q10: 如何访问 Windows 文件系统？

```bash
# Windows C: 盘
cd /mnt/c/

# Windows D: 盘
cd /mnt/d/

# 示例: 访问当前 Windows 项目目录
cd /mnt/d/data/PycharmProjects/PythonProject1
```

---

## 性能优化建议

### 1. 使用 WSL2 原生文件系统

项目文件应存储在 WSL2 文件系统中（`~/projects/`），而不是 Windows 文件系统（`/mnt/d/`），这样性能更好。

### 2. 配置 WSL2 网络

编辑 `/etc/wsl.conf`:

```bash
sudo vim /etc/wsl.conf
```

添加:

```ini
[network]
generateResolvConf = true

[automount]
enabled = true
options = "metadata"
```

### 3. 启用 systemd（Ubuntu 22.04+）

```bash
sudo vim /etc/wsl.conf
```

添加:

```ini
[boot]
systemd=true
```

重启 WSL2:

```powershell
wsl --shutdown
wsl
```

---

## 下一步操作

1. ✅ 完成 WSL2 安装
2. ✅ 配置 Linux 环境
3. ✅ 克隆并部署项目
4. ✅ 验证服务正常运行
5. 📝 编写自动化部署脚本
6. 📝 配置 Docker 容器化部署
7. 📝 设置开发环境热重载

---

## 参考资源

- **WSL 官方文档**: https://learn.microsoft.com/en-us/windows/wsl/
- **Ubuntu WSL**: https://ubuntu.com/wsl
- **NVIDIA CUDA on WSL2**: https://docs.nvidia.com/cuda/wsl-user-guide/
- **项目仓库**: https://github.com/githubstudycloud/gi005

---

**版本**: 1.0.0
**更新时间**: 2025-12-02
**维护者**: Voice Clone TTS 项目团队
