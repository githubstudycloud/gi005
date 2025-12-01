# Windows 启动指南

本文档详细介绍如何在 Windows 系统上启动 Voice Clone TTS 服务，支持 CPU 和 GPU 两种模式。

---

## 目录

1. [环境要求](#环境要求)
2. [GPU 模式启动](#gpu-模式启动)
3. [CPU 模式启动](#cpu-模式启动)
4. [单引擎启动](#单引擎启动)
5. [完整三引擎启动](#完整三引擎启动)
6. [常见问题](#常见问题)

---

## 环境要求

### 基础要求
- **操作系统**: Windows 10/11 64位
- **Python**: 3.10.x (推荐使用 `py -3.10` 启动器)
- **内存**: 最低 16GB，推荐 32GB
- **存储**: 至少 20GB 可用空间

### GPU 要求 (CUDA)
- **显卡**: NVIDIA GPU，显存 >= 6GB (推荐 8GB+)
- **CUDA**: 11.8 或 12.1
- **cuDNN**: 8.x

### 检查环境
```powershell
# 检查 Python 版本
py -3.10 --version

# 检查 CUDA 版本
nvcc --version

# 检查 GPU
nvidia-smi
```

---

## GPU 模式启动

### 1. 安装 GPU 版 PyTorch

```powershell
# CUDA 11.8
py -3.10 -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 或 CUDA 12.1
py -3.10 -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 2. 设置环境变量

```powershell
# 设置设备为 CUDA
set DEVICE=cuda
```

### 3. 启动服务

#### 方式一：Standalone 模式 (单进程)

适合开发测试，只运行单个引擎：

```powershell
cd E:\claudecode\github004\voice-clone-tts

# XTTS 引擎
py -3.10 -m src.main standalone --engine xtts --port 8080

# OpenVoice 引擎
py -3.10 -m src.main standalone --engine openvoice --port 8080

# GPT-SoVITS 引擎 (需要先启动后端 API)
py -3.10 -m src.main standalone --engine gpt-sovits --port 8080
```

#### 方式二：分布式模式 (多进程)

适合生产环境，支持多引擎：

```powershell
# 终端1: 启动 Gateway
cd E:\claudecode\github004\voice-clone-tts
py -3.10 -m src.main gateway --port 8080

# 终端2: 启动 XTTS Worker
py -3.10 -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load

# 终端3: 启动 OpenVoice Worker
py -3.10 -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080 --auto-load

# 终端4: 启动 GPT-SoVITS 后端 API
cd E:\claudecode\github004\packages\repos\GPT-SoVITS
py -3.10 api_v2.py -a 0.0.0.0 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml

# 终端5: 启动 GPT-SoVITS Worker
cd E:\claudecode\github004\voice-clone-tts
py -3.10 -m src.main worker --engine gpt-sovits --port 8003 --gateway http://localhost:8080 --auto-load
```

---

## CPU 模式启动

### 1. 安装 CPU 版 PyTorch

```powershell
py -3.10 -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 2. 设置环境变量

```powershell
# 设置设备为 CPU
set DEVICE=cpu
```

### 3. 启动服务

与 GPU 模式相同的命令，系统会自动使用 CPU。

> **注意**: CPU 模式下推理速度较慢，建议只用于测试或没有 GPU 的环境。

---

## 单引擎启动

### XTTS-v2 (推荐)

最简单的启动方式：

```powershell
cd E:\claudecode\github004\voice-clone-tts

# GPU 模式
set DEVICE=cuda
py -3.10 -m src.main standalone --engine xtts --port 8080

# CPU 模式
set DEVICE=cpu
py -3.10 -m src.main standalone --engine xtts --port 8080
```

访问: http://localhost:8080/docs

### OpenVoice

```powershell
cd E:\claudecode\github004\voice-clone-tts
py -3.10 -m src.main standalone --engine openvoice --port 8080
```

### GPT-SoVITS

GPT-SoVITS 需要先启动后端 API 服务：

```powershell
# 终端1: 启动 GPT-SoVITS API 后端
cd E:\claudecode\github004\packages\repos\GPT-SoVITS
py -3.10 api_v2.py -a 0.0.0.0 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml

# 终端2: 启动 Worker
cd E:\claudecode\github004\voice-clone-tts
py -3.10 -m src.main standalone --engine gpt-sovits --port 8080
```

---

## 完整三引擎启动

### 一键启动脚本

创建批处理文件 `start_all.bat`:

```batch
@echo off
echo Starting Voice Clone TTS v3.2.3...
echo.

:: 设置环境
set DEVICE=cuda
cd /d E:\claudecode\github004\voice-clone-tts

:: 启动 Gateway
echo [1/5] Starting Gateway on port 8080...
start "Gateway" cmd /k "py -3.10 -m src.main gateway --port 8080"
timeout /t 3 /nobreak > nul

:: 启动 XTTS Worker
echo [2/5] Starting XTTS Worker on port 8001...
start "XTTS Worker" cmd /k "py -3.10 -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load"
timeout /t 5 /nobreak > nul

:: 启动 OpenVoice Worker
echo [3/5] Starting OpenVoice Worker on port 8002...
start "OpenVoice Worker" cmd /k "py -3.10 -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080 --auto-load"
timeout /t 3 /nobreak > nul

:: 启动 GPT-SoVITS API
echo [4/5] Starting GPT-SoVITS API on port 9880...
cd /d E:\claudecode\github004\packages\repos\GPT-SoVITS
start "GPT-SoVITS API" cmd /k "py -3.10 api_v2.py -a 0.0.0.0 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml"
timeout /t 10 /nobreak > nul

:: 启动 GPT-SoVITS Worker
echo [5/5] Starting GPT-SoVITS Worker on port 8003...
cd /d E:\claudecode\github004\voice-clone-tts
start "GPT-SoVITS Worker" cmd /k "py -3.10 -m src.main worker --engine gpt-sovits --port 8003 --gateway http://localhost:8080 --auto-load"

echo.
echo All services started!
echo.
echo Gateway:          http://localhost:8080
echo XTTS Worker:      http://localhost:8001
echo OpenVoice Worker: http://localhost:8002
echo GPT-SoVITS API:   http://localhost:9880
echo GPT-SoVITS Worker: http://localhost:8003
echo.
echo API Documentation: http://localhost:8080/docs
pause
```

### 停止所有服务

创建批处理文件 `stop_all.bat`:

```batch
@echo off
echo Stopping all Voice Clone TTS services...

:: 关闭所有 Python 进程 (谨慎使用)
taskkill /f /im python.exe 2>nul
taskkill /f /im py.exe 2>nul

echo All services stopped.
pause
```

---

## 常见问题

### 1. CUDA out of memory

**症状**: `RuntimeError: CUDA out of memory`

**解决方案**:
- 减少批量大小
- 使用 CPU 模式: `set DEVICE=cpu`
- 关闭其他占用 GPU 的程序
- 使用更低精度: 在 config.yaml 中设置 `is_half: true`

### 2. 模型加载失败

**症状**: `FileNotFoundError` 或 `Model not found`

**解决方案**:
1. 确保模型已解压到正确位置
2. XTTS 模型: `packages/models/xtts_v2/extracted/`
3. OpenVoice 模型: `packages/models/openvoice/extracted/`
4. GPT-SoVITS 模型: `packages/repos/GPT-SoVITS/GPT_SoVITS/pretrained_models/`

### 3. GPT-SoVITS 连接失败

**症状**: `Cannot connect to GPT-SoVITS API`

**解决方案**:
1. 确保 GPT-SoVITS API 已启动并监听 9880 端口
2. 检查: `curl http://localhost:9880/docs`
3. 如果使用不同端口，设置环境变量: `set GPT_SOVITS_API_URL=http://127.0.0.1:9880`

### 4. 依赖安装问题

**症状**: `ModuleNotFoundError`

**解决方案**:
```powershell
# 重新安装依赖
cd E:\claudecode\github004\voice-clone-tts
py -3.10 -m pip install -r requirements.txt

# 如果有国内网络问题，使用镜像
py -3.10 -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 5. 端口被占用

**症状**: `Address already in use`

**解决方案**:
```powershell
# 查看占用端口的进程
netstat -ano | findstr :8080

# 关闭进程 (替换 PID)
taskkill /f /pid <PID>
```

---

## 服务端口说明

| 服务 | 默认端口 | 说明 |
|------|----------|------|
| Gateway | 8080 | API 网关，统一入口 |
| XTTS Worker | 8001 | XTTS-v2 引擎 |
| OpenVoice Worker | 8002 | OpenVoice 引擎 |
| GPT-SoVITS Worker | 8003 | GPT-SoVITS 代理 |
| GPT-SoVITS API | 9880 | GPT-SoVITS 后端 |

---

## API 测试

服务启动后，可以通过以下方式测试：

### 健康检查

```powershell
curl http://localhost:8080/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### 查看注册节点

```powershell
curl http://localhost:8080/api/nodes
```

### 语音合成测试

```powershell
curl -X POST "http://localhost:8080/api/synthesize" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"你好，这是测试\", \"voice_id\": \"default\", \"engine\": \"xtts\"}" ^
  --output test.wav
```

---

## 更多资源

- [API 参考文档](05-API参考.md)
- [架构设计](04-架构设计.md)
- [常见问题](06-常见问题.md)
