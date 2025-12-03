@echo off
chcp 65001 >nul
echo ========================================
echo   Voice Clone TTS - 一键启动脚本
echo ========================================
echo.

echo [1/5] 启动 Gateway (端口 8080)...
start "Gateway :8080" cmd /k "wsl -d Ubuntu-22.04 -u user -e bash -c 'cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts && python3 -m src.main gateway --port 8080'"

echo 等待 Gateway 启动...
timeout /t 5 /nobreak >nul

echo [2/5] 启动 XTTS Worker (端口 8001)...
start "XTTS Worker :8001" cmd /k "wsl -d Ubuntu-22.04 -u user -e bash -c 'export HF_ENDPOINT=https://hf-mirror.com && cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts && python3 -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --device cpu --auto-load'"

echo [3/5] 启动 OpenVoice Worker (端口 8002)...
start "OpenVoice Worker :8002" cmd /k "wsl -d Ubuntu-22.04 -u user -e bash -c 'export HF_ENDPOINT=https://hf-mirror.com && cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts && python3 -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080 --device cpu --auto-load'"

echo [4/5] 启动 GPT-SoVITS API (端口 9880)...
start "GPT-SoVITS API :9880" cmd /k "wsl -d Ubuntu-22.04 -u user -e bash -c 'export HF_ENDPOINT=https://hf-mirror.com && export PYTHONPATH=/mnt/d/data/PycharmProjects/PythonProject1/packages/GPT-SoVITS && cd /mnt/d/data/PycharmProjects/PythonProject1/packages/GPT-SoVITS && python3 api_v2.py -c GPT_SoVITS/configs/tts_infer_cpu.yaml -a 0.0.0.0 -p 9880'"

echo 等待 GPT-SoVITS API 启动...
timeout /t 15 /nobreak >nul

echo [5/5] 启动 GPT-SoVITS Worker (端口 8003)...
start "GPT-SoVITS Worker :8003" cmd /k "wsl -d Ubuntu-22.04 -u user -e bash -c 'export HF_ENDPOINT=https://hf-mirror.com && export GPT_SOVITS_API_URL=http://127.0.0.1:9880 && cd /mnt/d/data/PycharmProjects/PythonProject1/voice-clone-tts && python3 -m src.main worker --engine gpt-sovits --port 8003 --gateway http://localhost:8080 --device cpu --auto-load'"

echo.
echo ========================================
echo   所有服务已启动！
echo ========================================
echo.
echo   服务地址:
echo   - Gateway:           http://localhost:8080
echo   - XTTS Worker:       http://localhost:8001
echo   - OpenVoice Worker:  http://localhost:8002
echo   - GPT-SoVITS API:    http://localhost:9880
echo   - GPT-SoVITS Worker: http://localhost:8003
echo.
echo   测试命令:
echo   curl http://localhost:8080/health
echo   curl http://localhost:8080/api/nodes
echo.
echo   按任意键退出此窗口（服务将继续运行）...
pause >nul
