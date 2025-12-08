@echo off
REM NeMo MSDD 安装脚本 - Windows 版本
REM 需要管理员权限安装 ffmpeg

echo =========================================
echo NeMo MSDD Installation Script (Windows)
echo =========================================

REM 检查 Python
echo.
echo [1/4] Checking Python version...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Please install Python 3.8-3.10
    pause
    exit /b 1
)

REM 检查 CUDA
echo.
echo [2/4] Checking CUDA availability...
nvcc --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo CUDA detected
    nvcc --version | findstr "release"
) else (
    echo CUDA not found. Will install CPU version.
)

REM 安装 Python 依赖
echo.
echo [3/4] Installing Python dependencies...
echo Installing Cython...
pip install Cython

echo Checking PyTorch installation...
python -c "import torch" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo PyTorch already installed
    python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
) else (
    echo Installing PyTorch...
    nvcc --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        REM GPU 版本
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
    ) else (
        REM CPU 版本
        pip install torch torchaudio
    )
)

REM 安装 NeMo
echo.
echo [4/4] Installing NeMo toolkit...
echo This may take several minutes...

REM 可选：设置 HuggingFace 镜像（国内加速）
REM set HF_ENDPOINT=https://hf-mirror.com

pip install nemo_toolkit[asr]

REM 验证安装
echo.
echo =========================================
echo Verifying NeMo installation...
echo =========================================

python -c "import nemo; import nemo.collections.asr as nemo_asr; print('NeMo installation successful!'); print(f'NeMo path: {nemo.__file__}')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =========================================
    echo Installation completed successfully!
    echo =========================================
    echo.
    echo Next steps:
    echo 1. Test the installation:
    echo    python examples\test_nemo_msdd.py path\to\audio.wav
    echo.
    echo 2. Read the documentation:
    echo    docs\NEMO-MSDD-SETUP.md
    echo.
    echo 3. For audio processing, install ffmpeg:
    echo    winget install ffmpeg
    echo    or download from: https://ffmpeg.org/download.html
) else (
    echo.
    echo ERROR: Installation verification failed
    echo Please check the error messages above
)

pause
