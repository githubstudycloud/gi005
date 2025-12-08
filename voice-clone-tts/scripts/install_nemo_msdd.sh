#!/bin/bash
# NeMo MSDD 安装脚本
# 适用于 Ubuntu / WSL2

set -e

echo "========================================="
echo "NeMo MSDD Installation Script"
echo "========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo -e "\n${YELLOW}[1/5] Checking Python version...${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# 检查 CUDA
echo -e "\n${YELLOW}[2/5] Checking CUDA availability...${NC}"
if command -v nvcc &> /dev/null; then
    cuda_version=$(nvcc --version | grep "release" | awk '{print $6}' | cut -c2-)
    echo "CUDA version: $cuda_version"
else
    echo "CUDA not found. Will install CPU version."
fi

# 安装系统依赖
echo -e "\n${YELLOW}[3/5] Installing system dependencies...${NC}"
echo "This requires sudo privileges..."
sudo apt-get update
sudo apt-get install -y sox libsndfile1 ffmpeg

# 验证系统依赖
echo -e "\n${GREEN}Verifying installations:${NC}"
sox --version | head -n 1
ffmpeg -version | head -n 1

# 安装 Python 依赖
echo -e "\n${YELLOW}[4/5] Installing Python dependencies...${NC}"

# 先安装 Cython（NeMo 依赖）
echo "Installing Cython..."
pip install Cython

# 安装 PyTorch（如果需要）
echo "Checking PyTorch installation..."
if python -c "import torch" 2>/dev/null; then
    echo "PyTorch already installed"
    python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
else
    echo "Installing PyTorch..."
    if command -v nvcc &> /dev/null; then
        # GPU 版本
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        # CPU 版本
        pip install torch torchaudio
    fi
fi

# 安装 NeMo
echo -e "\n${YELLOW}[5/5] Installing NeMo toolkit...${NC}"
echo "This may take several minutes..."

# 设置 HuggingFace 镜像（可选，国内加速）
# export HF_ENDPOINT=https://hf-mirror.com

pip install nemo_toolkit[asr]

# 验证安装
echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Verifying NeMo installation...${NC}"
echo -e "${GREEN}=========================================${NC}"

python -c "
import nemo
import nemo.collections.asr as nemo_asr
print('✓ NeMo installation successful!')
print(f'NeMo path: {nemo.__file__}')
"

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${GREEN}=========================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Test the installation:"
echo "   python examples/test_nemo_msdd.py path/to/audio.wav"
echo ""
echo "2. Read the documentation:"
echo "   docs/NEMO-MSDD-SETUP.md"
echo ""
echo "3. For GPU acceleration, ensure CUDA is properly configured"
