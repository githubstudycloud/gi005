#!/bin/bash
# WSL2 环境自动化配置脚本
# Voice Clone TTS 项目
# 版本: 1.0.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在 WSL2 中运行
check_wsl2() {
    log_info "检查 WSL2 环境..."

    if ! grep -qi microsoft /proc/version; then
        log_error "此脚本必须在 WSL2 环境中运行！"
        exit 1
    fi

    log_info "✓ WSL2 环境确认"
}

# 更新系统
update_system() {
    log_info "更新系统包..."

    sudo apt update
    sudo apt upgrade -y

    log_info "✓ 系统更新完成"
}

# 安装基础工具
install_basic_tools() {
    log_info "安装基础开发工具..."

    sudo apt install -y \
        build-essential \
        git \
        curl \
        wget \
        vim \
        ca-certificates \
        software-properties-common \
        net-tools

    log_info "✓ 基础工具安装完成"
}

# 安装 FFmpeg
install_ffmpeg() {
    log_info "安装 FFmpeg..."

    sudo apt install -y ffmpeg

    # 验证
    ffmpeg -version > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "✓ FFmpeg 安装成功: $(ffmpeg -version | head -n1)"
    else
        log_error "FFmpeg 安装失败"
        exit 1
    fi
}

# 安装 Python 3.10 和相关工具
install_python() {
    log_info "安装 Python 3.10..."

    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev

    # 验证
    python3 --version
    pip3 --version

    log_info "✓ Python 安装完成: $(python3 --version)"
}

# 配置 Git
configure_git() {
    log_info "配置 Git..."

    # 检查是否已配置
    if git config --global user.name > /dev/null 2>&1; then
        log_info "Git 用户名已配置: $(git config --global user.name)"
    else
        read -p "输入 Git 用户名: " git_username
        git config --global user.name "$git_username"
    fi

    if git config --global user.email > /dev/null 2>&1; then
        log_info "Git 邮箱已配置: $(git config --global user.email)"
    else
        read -p "输入 Git 邮箱: " git_email
        git config --global user.email "$git_email"
    fi

    log_info "✓ Git 配置完成"
}

# 配置 SSH
configure_ssh() {
    log_info "配置 SSH..."

    if [ -f ~/.ssh/id_ed25519 ]; then
        log_info "SSH 密钥已存在"
    else
        log_info "生成 SSH 密钥..."
        ssh-keygen -t ed25519 -C "$(git config --global user.email)" -f ~/.ssh/id_ed25519 -N ""

        # 启动 ssh-agent
        eval "$(ssh-agent -s)"
        ssh-add ~/.ssh/id_ed25519

        log_info "✓ SSH 密钥生成完成"
        log_warn "请将以下公钥添加到 GitHub (https://github.com/settings/keys):"
        echo ""
        cat ~/.ssh/id_ed25519.pub
        echo ""
        read -p "按 Enter 继续..."
    fi
}

# 克隆项目
clone_project() {
    log_info "克隆项目仓库..."

    PROJECT_DIR="$HOME/projects/gi005"

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

    mkdir -p "$HOME/projects"
    cd "$HOME/projects"

    log_info "正在克隆仓库..."
    git clone git@github.com:githubstudycloud/gi005.git

    if [ $? -eq 0 ]; then
        log_info "✓ 项目克隆完成: $PROJECT_DIR"
    else
        log_error "项目克隆失败"
        log_warn "请检查 SSH 密钥是否已添加到 GitHub"
        exit 1
    fi
}

# 创建虚拟环境
create_venv() {
    log_info "创建 Python 虚拟环境..."

    PROJECT_DIR="$HOME/projects/gi005"
    cd "$PROJECT_DIR"

    if [ -d "venv" ]; then
        log_warn "虚拟环境已存在"
        return
    fi

    python3 -m venv venv

    log_info "✓ 虚拟环境创建完成"
}

# 安装项目依赖
install_dependencies() {
    log_info "安装项目依赖..."

    PROJECT_DIR="$HOME/projects/gi005"
    cd "$PROJECT_DIR"

    # 激活虚拟环境
    source venv/bin/activate

    # 升级 pip
    pip install --upgrade pip

    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_info "✓ 依赖安装完成"
    else
        log_warn "未找到 requirements.txt，跳过依赖安装"
    fi
}

# 恢复模型文件
restore_models() {
    log_info "恢复模型文件..."

    PROJECT_DIR="$HOME/projects/gi005"
    cd "$PROJECT_DIR"

    # XTTS-v2 模型
    if [ -d "packages/models/xtts_v2" ]; then
        log_info "恢复 XTTS-v2 模型..."
        cd packages/models/xtts_v2

        if ls xtts_v2_full.pkg.part_* 1> /dev/null 2>&1; then
            cat xtts_v2_full.pkg.part_* > xtts_v2.tar
            mkdir -p extracted
            tar -xvf xtts_v2.tar -C extracted/
            log_info "✓ XTTS-v2 模型恢复完成"
        else
            log_warn "未找到 XTTS-v2 模型分卷包"
        fi

        cd "$PROJECT_DIR"
    fi

    # OpenVoice 模型
    if [ -d "packages/models/openvoice" ]; then
        log_info "恢复 OpenVoice 模型..."
        cd packages/models/openvoice

        if ls checkpoints_v2.pkg.part_* 1> /dev/null 2>&1; then
            cat checkpoints_v2.pkg.part_* > checkpoints.tar
            mkdir -p extracted
            tar -xvf checkpoints.tar -C extracted/
            log_info "✓ OpenVoice 模型恢复完成"
        else
            log_warn "未找到 OpenVoice 模型分卷包"
        fi

        cd "$PROJECT_DIR"
    fi
}

# 创建启动脚本
create_start_scripts() {
    log_info "创建启动脚本..."

    PROJECT_DIR="$HOME/projects/gi005"
    cd "$PROJECT_DIR"

    # Gateway 启动脚本
    cat > start-gateway.sh <<'EOF'
#!/bin/bash
cd ~/projects/gi005
source venv/bin/activate
python -m src.main gateway --port 8080
EOF
    chmod +x start-gateway.sh

    # XTTS Worker 启动脚本
    cat > start-xtts-worker.sh <<'EOF'
#!/bin/bash
cd ~/projects/gi005
source venv/bin/activate
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load
EOF
    chmod +x start-xtts-worker.sh

    # Standalone 启动脚本
    cat > start-standalone.sh <<'EOF'
#!/bin/bash
cd ~/projects/gi005
source venv/bin/activate
python -m src.main standalone --engine xtts --port 8080
EOF
    chmod +x start-standalone.sh

    log_info "✓ 启动脚本创建完成"
}

# 显示完成信息
show_completion() {
    echo ""
    echo "======================================"
    log_info "WSL2 环境配置完成！"
    echo "======================================"
    echo ""
    echo "项目路径: $HOME/projects/gi005"
    echo ""
    echo "快速启动命令:"
    echo "  cd ~/projects/gi005"
    echo "  ./start-standalone.sh    # 独立模式"
    echo "  ./start-gateway.sh       # Gateway 模式"
    echo "  ./start-xtts-worker.sh   # Worker 模式"
    echo ""
    echo "访问地址:"
    echo "  http://localhost:8080/status"
    echo "  http://localhost:8080/admin"
    echo ""
    echo "激活虚拟环境:"
    echo "  cd ~/projects/gi005"
    echo "  source venv/bin/activate"
    echo ""
}

# 主函数
main() {
    echo "======================================"
    echo "   Voice Clone TTS - WSL2 配置脚本"
    echo "======================================"
    echo ""

    check_wsl2
    update_system
    install_basic_tools
    install_ffmpeg
    install_python
    configure_git
    configure_ssh
    clone_project
    create_venv
    install_dependencies
    restore_models
    create_start_scripts
    show_completion
}

# 运行主函数
main
