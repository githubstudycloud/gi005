#!/bin/bash
# WSL2 Ubuntu 环境配置脚本
# 包含: CUDA, PyTorch, 常用开发工具, Voice Clone TTS 项目支持
# Voice Clone TTS 项目
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}

log_step() {
    echo -e "${MAGENTA}[STEP]${NC} $1"
}

# 配置
PROJECT_DIR="$HOME/projects/gi005"
CUDA_VERSION="12.1"
PYTORCH_VERSION="2.1.0"

echo "======================================"
echo "  WSL2 Ubuntu 环境配置"
echo "  CUDA + PyTorch + 开发工具"
echo "======================================"
echo ""

# 检查是否在 WSL2 中运行
check_wsl2() {
    log_step "检查 WSL2 环境..."

    if ! grep -qi microsoft /proc/version; then
        log_error "此脚本必须在 WSL2 环境中运行！"
        exit 1
    fi

    log_success "✓ WSL2 环境确认"
}

# 检查是否有 NVIDIA GPU
check_nvidia_gpu() {
    log_step "检查 NVIDIA GPU..."

    if command -v nvidia-smi &> /dev/null; then
        log_info "检测到 NVIDIA GPU:"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
        return 0
    else
        log_warn "未检测到 NVIDIA GPU 或驱动未安装"
        log_info "WSL2 使用 Windows 端的 NVIDIA 驱动"
        log_info "请确保 Windows 已安装最新 NVIDIA 驱动"

        read -p "是否继续安装 CUDA Toolkit? (y/n): " continue_cuda
        if [ "$continue_cuda" != "y" ]; then
            return 1
        fi
        return 0
    fi
}

# 更新系统
update_system() {
    log_step "更新系统包..."

    sudo apt update
    sudo apt upgrade -y

    log_success "✓ 系统更新完成"
}

# 安装基础开发工具
install_basic_tools() {
    log_step "安装基础开发工具..."

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
        screen \
        tree \
        unzip \
        zip \
        p7zip-full \
        net-tools \
        iputils-ping \
        dnsutils \
        ca-certificates \
        gnupg \
        lsb-release \
        software-properties-common

    log_success "✓ 基础工具安装完成"
}

# 安装 Python 环境
install_python() {
    log_step "安装 Python 环境..."

    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        python3-setuptools \
        python3-wheel

    # 更新 pip
    python3 -m pip install --upgrade pip setuptools wheel

    # 安装常用 Python 工具
    pip3 install --user \
        virtualenv \
        pipenv \
        poetry \
        black \
        flake8 \
        pylint \
        mypy \
        pytest \
        ipython \
        jupyter

    log_success "✓ Python 环境安装完成"
    log_info "Python 版本: $(python3 --version)"
    log_info "Pip 版本: $(pip3 --version)"
}

# 安装音视频处理工具
install_av_tools() {
    log_step "安装音视频处理工具..."

    sudo apt install -y \
        ffmpeg \
        libavcodec-dev \
        libavformat-dev \
        libavutil-dev \
        libswscale-dev \
        libswresample-dev \
        libsndfile1 \
        libsndfile1-dev \
        portaudio19-dev \
        libportaudio2 \
        sox \
        libsox-dev \
        libsox-fmt-all

    log_success "✓ 音视频工具安装完成"
    log_info "FFmpeg 版本: $(ffmpeg -version | head -n1)"
}

# 安装 CUDA Toolkit (WSL2 专用)
install_cuda() {
    log_step "安装 CUDA Toolkit ${CUDA_VERSION} (WSL2 版本)..."

    # 删除旧的 CUDA GPG key（如果存在）
    sudo apt-key del 7fa2af80 2>/dev/null || true

    # 安装 CUDA keyring
    wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb -O /tmp/cuda-keyring.deb
    sudo dpkg -i /tmp/cuda-keyring.deb
    rm /tmp/cuda-keyring.deb

    # 更新并安装 CUDA
    sudo apt update
    sudo apt install -y cuda-toolkit-12-1

    # 配置环境变量
    CUDA_ENV='
# CUDA 环境变量
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
'

    if ! grep -q "CUDA_HOME" ~/.bashrc; then
        echo "$CUDA_ENV" >> ~/.bashrc
    fi

    # 立即加载环境变量
    export CUDA_HOME=/usr/local/cuda
    export PATH=$CUDA_HOME/bin:$PATH
    export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

    log_success "✓ CUDA Toolkit 安装完成"

    # 验证 CUDA
    if command -v nvcc &> /dev/null; then
        log_info "CUDA 版本: $(nvcc --version | grep release | awk '{print $6}')"
    fi
}

# 安装 cuDNN
install_cudnn() {
    log_step "安装 cuDNN..."

    sudo apt install -y \
        libcudnn8 \
        libcudnn8-dev

    log_success "✓ cuDNN 安装完成"
}

# 安装 PyTorch with CUDA
install_pytorch() {
    log_step "安装 PyTorch ${PYTORCH_VERSION} with CUDA ${CUDA_VERSION}..."

    # 创建临时虚拟环境测试
    pip3 install --user torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

    log_success "✓ PyTorch 安装完成"

    # 验证 PyTorch
    log_info "验证 PyTorch CUDA 支持..."
    python3 -c "
import torch
print(f'PyTorch 版本: {torch.__version__}')
print(f'CUDA 可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA 版本: {torch.version.cuda}')
    print(f'cuDNN 版本: {torch.backends.cudnn.version()}')
    print(f'GPU 设备: {torch.cuda.get_device_name(0)}')
    print(f'GPU 显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB')
"
}

# 安装其他深度学习工具
install_ml_tools() {
    log_step "安装机器学习工具..."

    pip3 install --user \
        numpy \
        scipy \
        pandas \
        matplotlib \
        seaborn \
        scikit-learn \
        transformers \
        datasets \
        accelerate \
        tensorboard \
        wandb \
        tqdm \
        pyyaml \
        omegaconf \
        hydra-core

    log_success "✓ 机器学习工具安装完成"
}

# 安装 TTS 相关依赖
install_tts_dependencies() {
    log_step "安装 TTS 相关依赖..."

    pip3 install --user \
        librosa \
        soundfile \
        pydub \
        webrtcvad \
        resemblyzer \
        noisereduce \
        pyworld \
        praat-parselmouth

    # 安装 Coqui TTS（XTTS 依赖）
    pip3 install --user TTS

    log_success "✓ TTS 依赖安装完成"
}

# 配置 Git
configure_git() {
    log_step "配置 Git..."

    if git config --global user.name > /dev/null 2>&1; then
        log_info "Git 用户名: $(git config --global user.name)"
    else
        read -p "输入 Git 用户名: " git_username
        git config --global user.name "$git_username"
    fi

    if git config --global user.email > /dev/null 2>&1; then
        log_info "Git 邮箱: $(git config --global user.email)"
    else
        read -p "输入 Git 邮箱: " git_email
        git config --global user.email "$git_email"
    fi

    # 配置 Git LFS
    git lfs install

    # 配置默认分支名
    git config --global init.defaultBranch main

    # 配置换行符处理
    git config --global core.autocrlf input

    log_success "✓ Git 配置完成"
}

# 配置 SSH
configure_ssh() {
    log_step "配置 SSH..."

    if [ -f ~/.ssh/id_ed25519 ]; then
        log_info "SSH 密钥已存在"
    else
        log_info "生成 SSH 密钥..."
        ssh-keygen -t ed25519 -C "$(git config --global user.email)" -f ~/.ssh/id_ed25519 -N ""

        eval "$(ssh-agent -s)"
        ssh-add ~/.ssh/id_ed25519

        log_success "✓ SSH 密钥生成完成"
        log_warn "请将以下公钥添加到 GitHub (https://github.com/settings/keys):"
        echo ""
        cat ~/.ssh/id_ed25519.pub
        echo ""
        read -p "添加完成后按 Enter 继续..."
    fi
}

# 克隆项目
clone_project() {
    log_step "克隆 Voice Clone TTS 项目..."

    mkdir -p "$(dirname "$PROJECT_DIR")"

    if [ -d "$PROJECT_DIR" ]; then
        log_warn "项目目录已存在: $PROJECT_DIR"
        read -p "是否删除并重新克隆? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            rm -rf "$PROJECT_DIR"
        else
            log_info "跳过克隆步骤"
            return
        fi
    fi

    cd "$(dirname "$PROJECT_DIR")"
    git clone git@github.com:githubstudycloud/gi005.git "$(basename "$PROJECT_DIR")"

    if [ $? -eq 0 ]; then
        log_success "✓ 项目克隆完成: $PROJECT_DIR"
    else
        log_error "项目克隆失败"
        log_warn "请检查 SSH 密钥是否已添加到 GitHub"
        exit 1
    fi
}

# 配置项目
setup_project() {
    log_step "配置项目环境..."

    cd "$PROJECT_DIR"

    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "✓ 虚拟环境创建完成"
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 升级 pip
    pip install --upgrade pip setuptools wheel

    # 安装项目依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_info "✓ 项目依赖安装完成"
    else
        log_warn "未找到 requirements.txt"
    fi

    # 安装 PyTorch (如果虚拟环境中没有)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

    deactivate

    log_success "✓ 项目配置完成"
}

# 恢复模型文件
restore_models() {
    log_step "恢复模型文件..."

    cd "$PROJECT_DIR"

    # XTTS-v2
    if [ -d "packages/models/xtts_v2" ]; then
        log_info "恢复 XTTS-v2 模型..."
        cd packages/models/xtts_v2

        if ls xtts_v2_full.pkg.part_* 1> /dev/null 2>&1; then
            cat xtts_v2_full.pkg.part_* > xtts_v2.tar
            mkdir -p extracted
            tar -xvf xtts_v2.tar -C extracted/
            log_success "✓ XTTS-v2 模型恢复完成"
        else
            log_warn "未找到 XTTS-v2 模型分卷包"
        fi

        cd "$PROJECT_DIR"
    fi

    # OpenVoice
    if [ -d "packages/models/openvoice" ]; then
        log_info "恢复 OpenVoice 模型..."
        cd packages/models/openvoice

        if ls checkpoints_v2.pkg.part_* 1> /dev/null 2>&1; then
            cat checkpoints_v2.pkg.part_* > checkpoints.tar
            mkdir -p extracted
            tar -xvf checkpoints.tar -C extracted/
            log_success "✓ OpenVoice 模型恢复完成"
        else
            log_warn "未找到 OpenVoice 模型分卷包"
        fi

        cd "$PROJECT_DIR"
    fi
}

# 创建启动脚本
create_start_scripts() {
    log_step "创建启动脚本..."

    cd "$PROJECT_DIR"

    # Standalone 模式
    cat > start-standalone.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.main standalone --engine xtts --port 8080
EOF
    chmod +x start-standalone.sh

    # Gateway 模式
    cat > start-gateway.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.main gateway --port 8080
EOF
    chmod +x start-gateway.sh

    # Worker 模式
    cat > start-xtts-worker.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load
EOF
    chmod +x start-xtts-worker.sh

    log_success "✓ 启动脚本创建完成"
}

# 创建快捷别名
create_aliases() {
    log_step "创建快捷别名..."

    ALIASES='
# Voice Clone TTS 快捷命令
alias gi005="cd ~/projects/gi005"
alias gi005-start="cd ~/projects/gi005 && ./start-standalone.sh"
alias gi005-gateway="cd ~/projects/gi005 && ./start-gateway.sh"
alias gi005-worker="cd ~/projects/gi005 && ./start-xtts-worker.sh"
alias gi005-venv="cd ~/projects/gi005 && source venv/bin/activate"

# CUDA 相关
alias cuda-info="nvidia-smi"
alias cuda-watch="watch -n 1 nvidia-smi"
'

    if ! grep -q "gi005" ~/.bashrc; then
        echo "$ALIASES" >> ~/.bashrc
        log_success "✓ 别名添加完成"
    else
        log_info "别名已存在"
    fi
}

# 显示系统信息
show_system_info() {
    echo ""
    echo "======================================"
    log_success "系统信息"
    echo "======================================"

    echo ""
    log_info "操作系统: $(lsb_release -d | cut -f2)"
    log_info "内核版本: $(uname -r)"
    log_info "Python 版本: $(python3 --version)"

    if command -v nvcc &> /dev/null; then
        log_info "CUDA 版本: $(nvcc --version | grep release | awk '{print $6}')"
    fi

    if command -v nvidia-smi &> /dev/null; then
        echo ""
        log_info "GPU 信息:"
        nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader
    fi

    echo ""
    log_info "磁盘使用:"
    df -h ~ | tail -n1

    echo ""
}

# 显示完成信息
show_completion() {
    echo ""
    echo "======================================"
    log_success "环境配置完成！"
    echo "======================================"
    echo ""

    log_info "已安装组件:"
    echo "  • 基础开发工具 (build-essential, cmake, git, etc.)"
    echo "  • Python 3 + pip + venv"
    echo "  • 音视频处理工具 (FFmpeg, Sox, PortAudio)"
    echo "  • CUDA Toolkit ${CUDA_VERSION}"
    echo "  • cuDNN"
    echo "  • PyTorch ${PYTORCH_VERSION} with CUDA"
    echo "  • 机器学习工具 (transformers, tensorboard, etc.)"
    echo "  • TTS 相关依赖 (librosa, TTS, etc.)"
    echo ""

    log_info "项目位置: $PROJECT_DIR"
    echo ""

    log_info "快速启动命令:"
    echo "  gi005              # 进入项目目录"
    echo "  gi005-start        # 启动独立模式"
    echo "  gi005-gateway      # 启动 Gateway"
    echo "  gi005-worker       # 启动 Worker"
    echo "  gi005-venv         # 激活虚拟环境"
    echo ""

    log_info "手动启动:"
    echo "  cd ~/projects/gi005"
    echo "  ./start-standalone.sh"
    echo ""

    log_info "访问地址:"
    echo "  http://localhost:8080/status"
    echo "  http://localhost:8080/admin"
    echo ""

    log_warn "重要提示:"
    echo "  • 请运行 'source ~/.bashrc' 或重新打开终端使配置生效"
    echo "  • 首次运行可能需要下载模型文件"
    echo "  • 确保 Windows 已安装最新 NVIDIA 驱动"
    echo ""

    show_system_info
}

# 主函数
main() {
    echo ""

    check_wsl2

    read -p "是否继续安装? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        log_info "操作已取消"
        exit 0
    fi

    echo ""

    # 系统更新
    update_system

    # 安装工具
    install_basic_tools
    install_python
    install_av_tools

    # GPU 和 CUDA
    if check_nvidia_gpu; then
        install_cuda
        install_cudnn
        install_pytorch
    else
        log_warn "跳过 CUDA 安装，将安装 CPU 版本 PyTorch"
        pip3 install --user torch torchvision torchaudio
    fi

    # 其他工具
    install_ml_tools
    install_tts_dependencies

    # Git 和 SSH
    configure_git
    configure_ssh

    # 项目设置
    clone_project
    setup_project
    restore_models
    create_start_scripts
    create_aliases

    # 完成
    show_completion
}

# 运行主函数
main "$@"
