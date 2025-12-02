#!/bin/bash
# WSL2 在 D 盘部署脚本（不迁移 WSL2 系统）
# 直接在 Windows D 盘上克隆和运行项目
# Voice Clone TTS 项目
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 配置
D_DRIVE_PATH="/mnt/d/WSL2-Projects/gi005"

echo "======================================"
echo "  在 D 盘部署 Voice Clone TTS"
echo "======================================"
echo ""

log_info "项目将部署到: $D_DRIVE_PATH"
log_warn "注意: 跨文件系统性能较慢，建议迁移 WSL2 到 D 盘以获得最佳性能"
echo ""

read -p "是否继续? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    log_info "操作已取消"
    exit 0
fi

# 检查是否在 WSL2 中
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
install_tools() {
    log_info "安装开发工具..."

    sudo apt install -y \
        build-essential \
        git \
        curl \
        wget \
        vim \
        python3 \
        python3-pip \
        python3-venv \
        ffmpeg

    log_info "✓ 工具安装完成"
}

# 配置 Git
configure_git() {
    log_info "配置 Git..."

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

        eval "$(ssh-agent -s)"
        ssh-add ~/.ssh/id_ed25519

        log_info "✓ SSH 密钥生成完成"
        log_warn "请将以下公钥添加到 GitHub:"
        echo ""
        cat ~/.ssh/id_ed25519.pub
        echo ""
        read -p "按 Enter 继续..."
    fi
}

# 创建 D 盘项目目录
create_project_dir() {
    log_info "创建项目目录..."

    # 确保 D 盘可访问
    if [ ! -d "/mnt/d" ]; then
        log_error "无法访问 D 盘！请检查 WSL2 配置"
        exit 1
    fi

    # 创建目录
    mkdir -p "$(dirname "$D_DRIVE_PATH")"

    log_info "✓ 项目目录创建完成"
}

# 克隆项目到 D 盘
clone_project() {
    log_info "克隆项目到 D 盘..."

    if [ -d "$D_DRIVE_PATH" ]; then
        log_warn "项目目录已存在: $D_DRIVE_PATH"
        read -p "是否删除并重新克隆? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            rm -rf "$D_DRIVE_PATH"
        else
            log_info "跳过克隆步骤"
            return
        fi
    fi

    cd "$(dirname "$D_DRIVE_PATH")"
    git clone git@github.com:githubstudycloud/gi005.git "$(basename "$D_DRIVE_PATH")"

    if [ $? -eq 0 ]; then
        log_info "✓ 项目克隆完成: $D_DRIVE_PATH"
    else
        log_error "项目克隆失败"
        exit 1
    fi
}

# 创建虚拟环境
create_venv() {
    log_info "创建 Python 虚拟环境..."

    cd "$D_DRIVE_PATH"

    if [ -d "venv" ]; then
        log_warn "虚拟环境已存在"
        return
    fi

    python3 -m venv venv
    log_info "✓ 虚拟环境创建完成"
}

# 安装依赖
install_dependencies() {
    log_info "安装项目依赖..."

    cd "$D_DRIVE_PATH"
    source venv/bin/activate

    pip install --upgrade pip

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_info "✓ 依赖安装完成"
    else
        log_warn "未找到 requirements.txt"
    fi
}

# 恢复模型文件
restore_models() {
    log_info "恢复模型文件..."

    cd "$D_DRIVE_PATH"

    # XTTS-v2
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

        cd "$D_DRIVE_PATH"
    fi

    # OpenVoice
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

        cd "$D_DRIVE_PATH"
    fi
}

# 创建启动脚本
create_start_scripts() {
    log_info "创建启动脚本..."

    cd "$D_DRIVE_PATH"

    # Standalone
    cat > start-standalone.sh <<EOF
#!/bin/bash
cd "$D_DRIVE_PATH"
source venv/bin/activate
python -m src.main standalone --engine xtts --port 8080
EOF
    chmod +x start-standalone.sh

    # Gateway
    cat > start-gateway.sh <<EOF
#!/bin/bash
cd "$D_DRIVE_PATH"
source venv/bin/activate
python -m src.main gateway --port 8080
EOF
    chmod +x start-gateway.sh

    # Worker
    cat > start-xtts-worker.sh <<EOF
#!/bin/bash
cd "$D_DRIVE_PATH"
source venv/bin/activate
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load
EOF
    chmod +x start-xtts-worker.sh

    log_info "✓ 启动脚本创建完成"
}

# 创建快捷访问别名
create_aliases() {
    log_info "创建快捷别名..."

    # 添加到 .bashrc
    if ! grep -q "gi005" ~/.bashrc; then
        cat >> ~/.bashrc <<EOF

# Voice Clone TTS 项目别名
alias gi005="cd $D_DRIVE_PATH"
alias gi005-start="cd $D_DRIVE_PATH && ./start-standalone.sh"
alias gi005-gateway="cd $D_DRIVE_PATH && ./start-gateway.sh"
alias gi005-worker="cd $D_DRIVE_PATH && ./start-xtts-worker.sh"
EOF
        log_info "✓ 别名添加完成"
        log_info "使用 'source ~/.bashrc' 或重新打开终端生效"
    else
        log_info "别名已存在"
    fi
}

# 显示完成信息
show_completion() {
    echo ""
    echo "======================================"
    log_info "D 盘部署完成！"
    echo "======================================"
    echo ""
    echo "项目路径: $D_DRIVE_PATH"
    echo ""
    echo "快速命令:"
    echo "  gi005              # 进入项目目录"
    echo "  gi005-start        # 启动独立模式"
    echo "  gi005-gateway      # 启动 Gateway"
    echo "  gi005-worker       # 启动 Worker"
    echo ""
    echo "或手动启动:"
    echo "  cd $D_DRIVE_PATH"
    echo "  ./start-standalone.sh"
    echo ""
    echo "访问地址:"
    echo "  http://localhost:8080/status"
    echo "  http://localhost:8080/admin"
    echo ""
    log_warn "性能提示:"
    echo "  跨文件系统（WSL2 访问 Windows 磁盘）性能较慢"
    echo "  建议使用 'move-wsl-to-d-drive.ps1' 迁移 WSL2 到 D 盘"
    echo ""
}

# 主函数
main() {
    check_wsl2
    update_system
    install_tools
    configure_git
    configure_ssh
    create_project_dir
    clone_project
    create_venv
    install_dependencies
    restore_models
    create_start_scripts
    create_aliases
    show_completion
}

main
