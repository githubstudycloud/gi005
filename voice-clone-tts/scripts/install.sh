#!/bin/bash
# 音色克隆 TTS 一键安装脚本 (Linux/macOS)
# Voice Clone TTS One-Click Installer

set -e

echo "============================================================"
echo "   音色克隆 TTS 一键安装脚本 (Linux/macOS)"
echo "   Voice Clone TTS One-Click Installer"
echo "============================================================"
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"

# 函数：打印带颜色的消息
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 步骤 1: 检查 Python
echo "[1/7] 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    print_error "未找到 Python3，请先安装 Python 3.10"
    echo "       Ubuntu/Debian: sudo apt install python3.10 python3.10-venv"
    echo "       macOS: brew install python@3.10"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "       当前版本: Python $PYTHON_VERSION"

if [[ ! "$PYTHON_VERSION" =~ ^3\.10 ]]; then
    print_warning "推荐使用 Python 3.10，当前版本可能存在兼容性问题"
fi

# 步骤 2: 检查 FFmpeg
echo
echo "[2/7] 检查 FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    print_warning "未找到 FFmpeg"
    echo "       Ubuntu/Debian: sudo apt install ffmpeg"
    echo "       macOS: brew install ffmpeg"
    echo "       或从 dependencies 目录还原"
else
    print_status "FFmpeg 已安装"
fi

# 步骤 3: 创建虚拟环境
echo
echo "[3/7] 创建虚拟环境..."
if [ -d "$VENV_DIR" ]; then
    echo "       虚拟环境已存在，跳过创建"
else
    python3 -m venv "$VENV_DIR"
    print_status "虚拟环境创建成功"
fi

# 步骤 4: 激活虚拟环境
echo
echo "[4/7] 激活虚拟环境..."
source "$VENV_DIR/bin/activate"
print_status "已激活"

# 步骤 5: 升级 pip
echo
echo "[5/7] 升级 pip..."
pip install --upgrade pip -q
print_status "pip 已升级"

# 步骤 6: 安装依赖
echo
echo "[6/7] 安装依赖包（这可能需要几分钟）..."
echo

# 检测是否有 NVIDIA GPU
HAS_CUDA=false
if command -v nvidia-smi &> /dev/null; then
    HAS_CUDA=true
    echo "       检测到 NVIDIA GPU"
fi

# 安装 PyTorch
echo "       [6.1] 安装 PyTorch..."
if [ "$HAS_CUDA" = true ]; then
    pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118 -q
else
    pip install torch==2.5.1 torchaudio==2.5.1 -q
fi

# 安装 TTS 库
echo "       [6.2] 安装 TTS 库..."
pip install TTS==0.22.0 -q

# 安装其他依赖
echo "       [6.3] 安装其他依赖..."
pip install -r "$PROJECT_ROOT/requirements.txt" -q

# 安装项目本身
echo "       [6.4] 安装项目..."
pip install -e "$PROJECT_ROOT" -q

print_status "依赖安装完成"

# 步骤 7: 验证安装
echo
echo "[7/7] 验证安装..."

python -c "import torch; print(f'       PyTorch: {torch.__version__}')"
python -c "import TTS; print(f'       TTS: {TTS.__version__}')" 2>/dev/null || echo "       TTS: 安装检查"
python -c "import librosa; print(f'       librosa: {librosa.__version__}')"
python -c "import fastapi; print(f'       FastAPI: {fastapi.__version__}')"

echo
echo "============================================================"
echo "   安装完成！"
echo "============================================================"
echo
echo "使用方法:"
echo
echo "  1. 激活虚拟环境:"
echo "     source $VENV_DIR/bin/activate"
echo
echo "  2. 命令行工具:"
echo "     python production/main.py --help"
echo "     python production/main.py quick -a reference.wav -t \"测试文本\" -o output.wav"
echo
echo "  3. 启动 API 服务:"
echo "     python production/main.py serve --engine xtts --port 8000"
echo
echo "  4. 如果使用 OpenVoice，还需要:"
echo "     - 克隆 OpenVoice 仓库 (参考 EXTERNAL_REPOS_SETUP.md)"
echo "     - 还原 checkpoints_v2 模型 (参考 offline_package/README.md)"
echo
echo "============================================================"
