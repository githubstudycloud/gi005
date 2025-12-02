#!/bin/bash
# WSL2 软链接部署脚本（方案 D - 最佳方案）
# 适用于 C/D 盘在同一物理磁盘（不同分区）
# Voice Clone TTS 项目
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
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

# 配置
WSL2_PROJECT_PATH="$HOME/projects/gi005"  # WSL2 内部路径（软链接）
D_DRIVE_REAL_PATH="/mnt/d/WSL2-Projects/gi005"  # D 盘实际存储路径

echo "======================================"
echo "  WSL2 软链接部署方案"
echo "======================================"
echo ""

log_info "部署方案："
echo "  • WSL2 位置: C 盘（默认）"
echo "  • 项目访问路径: $WSL2_PROJECT_PATH"
echo "  • 实际存储路径: $D_DRIVE_REAL_PATH"
echo "  • 连接方式: 符号链接（软链接）"
echo ""

log_success "优势："
echo "  ✓ WSL2 原生性能（在 C 盘）"
echo "  ✓ 项目数据存储在 D 盘（节省 C 盘空间）"
echo "  ✓ 同一物理磁盘，几乎无性能损失"
echo "  ✓ 访问路径透明，应用无感知"
echo ""

read -p "是否继续? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    log_info "操作已取消"
    exit 0
fi

# 检查 WSL2 环境
check_wsl2() {
    log_info "检查 WSL2 环境..."

    if ! grep -qi microsoft /proc/version; then
        log_error "此脚本必须在 WSL2 环境中运行！"
        exit 1
    fi

    log_success "✓ WSL2 环境确认"
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    sudo apt update
    sudo apt upgrade -y
    log_success "✓ 系统更新完成"
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
        python3-dev \
        ffmpeg \
        net-tools

    log_success "✓ 工具安装完成"
    log_info "Python: $(python3 --version)"
    log_info "FFmpeg: $(ffmpeg -version | head -n1)"
}

# 配置 Git
configure_git() {
    log_info "配置 Git..."

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

    log_success "✓ Git 配置完成"
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

        log_success "✓ SSH 密钥生成完成"
        log_warn "请将以下公钥添加到 GitHub (https://github.com/settings/keys):"
        echo ""
        cat ~/.ssh/id_ed25519.pub
        echo ""
        read -p "按 Enter 继续..."
    fi
}

# 创建 D 盘实际存储目录
create_real_dir() {
    log_info "创建 D 盘实际存储目录..."

    # 检查 D 盘是否可访问
    if [ ! -d "/mnt/d" ]; then
        log_error "无法访问 D 盘！请检查 WSL2 配置"
        exit 1
    fi

    # 创建目录
    mkdir -p "$(dirname "$D_DRIVE_REAL_PATH")"

    log_success "✓ 实际存储目录创建完成: $D_DRIVE_REAL_PATH"
}

# 克隆项目到 D 盘
clone_project() {
    log_info "克隆项目到 D 盘实际存储位置..."

    if [ -d "$D_DRIVE_REAL_PATH" ]; then
        log_warn "项目目录已存在: $D_DRIVE_REAL_PATH"
        read -p "是否删除并重新克隆? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            rm -rf "$D_DRIVE_REAL_PATH"
        else
            log_info "跳过克隆步骤"
            return
        fi
    fi

    cd "$(dirname "$D_DRIVE_REAL_PATH")"
    git clone git@github.com:githubstudycloud/gi005.git "$(basename "$D_DRIVE_REAL_PATH")"

    if [ $? -eq 0 ]; then
        log_success "✓ 项目克隆完成: $D_DRIVE_REAL_PATH"
    else
        log_error "项目克隆失败"
        log_warn "请检查 SSH 密钥是否已添加到 GitHub"
        exit 1
    fi
}

# 创建软链接
create_symlink() {
    log_info "创建软链接..."

    # 确保父目录存在
    mkdir -p "$(dirname "$WSL2_PROJECT_PATH")"

    # 如果已存在软链接或目录，先删除
    if [ -L "$WSL2_PROJECT_PATH" ]; then
        log_warn "软链接已存在，正在更新..."
        rm "$WSL2_PROJECT_PATH"
    elif [ -d "$WSL2_PROJECT_PATH" ]; then
        log_warn "目录已存在，将被替换为软链接"
        read -p "是否继续? (y/n): " confirm
        if [ "$confirm" != "y" ]; then
            log_error "操作已取消"
            exit 1
        fi
        rm -rf "$WSL2_PROJECT_PATH"
    fi

    # 创建软链接
    ln -s "$D_DRIVE_REAL_PATH" "$WSL2_PROJECT_PATH"

    if [ -L "$WSL2_PROJECT_PATH" ]; then
        log_success "✓ 软链接创建成功"
        log_info "访问路径: $WSL2_PROJECT_PATH"
        log_info "实际位置: $D_DRIVE_REAL_PATH"

        # 验证软链接
        if [ -d "$WSL2_PROJECT_PATH" ]; then
            log_success "✓ 软链接验证成功，可正常访问"
        else
            log_error "软链接验证失败"
            exit 1
        fi
    else
        log_error "软链接创建失败"
        exit 1
    fi
}

# 创建虚拟环境
create_venv() {
    log_info "创建 Python 虚拟环境..."

    cd "$WSL2_PROJECT_PATH"

    if [ -d "venv" ]; then
        log_warn "虚拟环境已存在"
        return
    fi

    python3 -m venv venv
    log_success "✓ 虚拟环境创建完成"
}

# 安装依赖
install_dependencies() {
    log_info "安装项目依赖..."

    cd "$WSL2_PROJECT_PATH"
    source venv/bin/activate

    pip install --upgrade pip

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "✓ 依赖安装完成"
    else
        log_warn "未找到 requirements.txt"
    fi
}

# 恢复模型文件
restore_models() {
    log_info "恢复模型文件..."

    cd "$WSL2_PROJECT_PATH"

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

        cd "$WSL2_PROJECT_PATH"
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

        cd "$WSL2_PROJECT_PATH"
    fi
}

# 创建启动脚本
create_start_scripts() {
    log_info "创建启动脚本..."

    cd "$WSL2_PROJECT_PATH"

    # Standalone
    cat > start-standalone.sh <<EOF
#!/bin/bash
cd "$WSL2_PROJECT_PATH"
source venv/bin/activate
python -m src.main standalone --engine xtts --port 8080
EOF
    chmod +x start-standalone.sh

    # Gateway
    cat > start-gateway.sh <<EOF
#!/bin/bash
cd "$WSL2_PROJECT_PATH"
source venv/bin/activate
python -m src.main gateway --port 8080
EOF
    chmod +x start-gateway.sh

    # Worker
    cat > start-xtts-worker.sh <<EOF
#!/bin/bash
cd "$WSL2_PROJECT_PATH"
source venv/bin/activate
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load
EOF
    chmod +x start-xtts-worker.sh

    log_success "✓ 启动脚本创建完成"
}

# 显示磁盘使用情况
show_disk_usage() {
    log_info "磁盘使用情况:"
    echo ""

    # D 盘项目大小
    if [ -d "$D_DRIVE_REAL_PATH" ]; then
        project_size=$(du -sh "$D_DRIVE_REAL_PATH" 2>/dev/null | cut -f1)
        log_info "D 盘项目大小: $project_size"
    fi

    # WSL2 内部空间
    log_info "WSL2 文件系统使用:"
    df -h ~ | tail -n1

    echo ""
}

# 显示完成信息
show_completion() {
    echo ""
    echo "======================================"
    log_success "软链接部署完成！"
    echo "======================================"
    echo ""

    log_info "部署详情:"
    echo "  • 访问路径: $WSL2_PROJECT_PATH"
    echo "  • 实际位置: $D_DRIVE_REAL_PATH"
    echo "  • 连接类型: 符号链接（软链接）"
    echo ""

    log_info "快速启动:"
    echo "  cd ~/projects/gi005"
    echo "  ./start-standalone.sh    # 独立模式"
    echo "  ./start-gateway.sh       # Gateway 模式"
    echo "  ./start-xtts-worker.sh   # Worker 模式"
    echo ""

    log_info "访问地址:"
    echo "  http://localhost:8080/status"
    echo "  http://localhost:8080/admin"
    echo ""

    log_success "验证软链接:"
    echo "  ls -la ~/projects/gi005"
    echo "  readlink ~/projects/gi005"
    echo ""

    show_disk_usage

    log_success "优势总结:"
    echo "  ✓ WSL2 在 C 盘，性能最佳"
    echo "  ✓ 项目数据在 D 盘，节省 C 盘空间"
    echo "  ✓ 同一物理磁盘，无跨盘性能损失"
    echo "  ✓ 访问透明，应用无感知"
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "开始部署..."
    echo ""

    check_wsl2
    update_system
    install_tools
    configure_git
    configure_ssh
    create_real_dir
    clone_project
    create_symlink
    create_venv
    install_dependencies
    restore_models
    create_start_scripts
    show_completion
}

# 运行主函数
main
