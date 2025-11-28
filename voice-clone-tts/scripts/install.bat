@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================================
echo    音色克隆 TTS 一键安装脚本 (Windows)
echo    Voice Clone TTS One-Click Installer
echo ============================================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 建议以管理员身份运行此脚本
    echo.
)

:: 设置变量
set "PROJECT_ROOT=%~dp0.."
set "VENV_DIR=%PROJECT_ROOT%\venv"
set "PYTHON_VERSION=3.10"

:: 步骤 1: 检查 Python
echo [1/7] 检查 Python 版本...
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10
    echo        下载地址: https://www.python.org/downloads/release/python-31011/
    echo        或从 dependencies 目录还原 python-3.10.11-amd64.exe
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo        当前版本: Python %PYTHON_VER%

echo %PYTHON_VER% | findstr /b "3.10" >nul
if %errorLevel% neq 0 (
    echo [警告] 推荐使用 Python 3.10，当前版本可能存在兼容性问题
)

:: 步骤 2: 检查 FFmpeg
echo.
echo [2/7] 检查 FFmpeg...
where ffmpeg >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 未找到 FFmpeg
    echo        请从 dependencies 目录还原并添加到 PATH
    echo        或将 ffmpeg.exe 放到项目根目录
) else (
    echo        FFmpeg 已安装
)

:: 步骤 3: 创建虚拟环境
echo.
echo [3/7] 创建虚拟环境...
if exist "%VENV_DIR%" (
    echo        虚拟环境已存在，跳过创建
) else (
    python -m venv "%VENV_DIR%"
    if %errorLevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo        虚拟环境创建成功
)

:: 步骤 4: 激活虚拟环境
echo.
echo [4/7] 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorLevel% neq 0 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)
echo        已激活

:: 步骤 5: 升级 pip
echo.
echo [5/7] 升级 pip...
python -m pip install --upgrade pip -q
echo        pip 已升级

:: 步骤 6: 安装依赖
echo.
echo [6/7] 安装依赖包（这可能需要几分钟）...
echo.

:: 先安装 PyTorch (CUDA 11.8)
echo        [6.1] 安装 PyTorch...
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118 -q
if %errorLevel% neq 0 (
    echo [警告] PyTorch CUDA 版本安装失败，尝试 CPU 版本...
    pip install torch==2.5.1 torchaudio==2.5.1 -q
)

:: 安装 TTS 库
echo        [6.2] 安装 TTS 库...
pip install TTS==0.22.0 -q

:: 安装其他依赖
echo        [6.3] 安装其他依赖...
pip install -r "%PROJECT_ROOT%\requirements.txt" -q

:: 安装项目本身
echo        [6.4] 安装项目...
pip install -e "%PROJECT_ROOT%" -q

echo        依赖安装完成

:: 步骤 7: 验证安装
echo.
echo [7/7] 验证安装...

python -c "import torch; print(f'        PyTorch: {torch.__version__}')"
python -c "import TTS; print(f'        TTS: {TTS.__version__}')" 2>nul || echo        TTS: 安装检查
python -c "import librosa; print(f'        librosa: {librosa.__version__}')"
python -c "import fastapi; print(f'        FastAPI: {fastapi.__version__}')"

echo.
echo ============================================================
echo    安装完成！
echo ============================================================
echo.
echo 使用方法:
echo.
echo   1. 激活虚拟环境:
echo      %VENV_DIR%\Scripts\activate
echo.
echo   2. 命令行工具:
echo      python production/main.py --help
echo      python production/main.py quick -a reference.wav -t "测试文本" -o output.wav
echo.
echo   3. 启动 API 服务:
echo      python production/main.py serve --engine xtts --port 8000
echo.
echo   4. 如果使用 OpenVoice，还需要:
echo      - 克隆 OpenVoice 仓库 (参考 EXTERNAL_REPOS_SETUP.md)
echo      - 还原 checkpoints_v2 模型 (参考 offline_package/README.md)
echo.
echo ============================================================

pause
