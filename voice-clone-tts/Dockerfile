# ============================================================
# Voice Clone TTS Docker 镜像
# 支持 XTTS-v2 和 OpenVoice 引擎
# ============================================================

# 基础镜像：NVIDIA CUDA 11.8 + Python 3.10
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 AS base

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建 Python 符号链接
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# 创建工作目录
WORKDIR /app

# ============================================================
# 依赖安装阶段
# ============================================================
FROM base AS dependencies

# 复制依赖文件
COPY requirements.txt requirements-freeze.txt ./

# 安装 PyTorch (CUDA 11.8)
RUN pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118

# 安装其他依赖
RUN pip install -r requirements.txt

# ============================================================
# 最终镜像
# ============================================================
FROM dependencies AS final

# 复制项目代码
COPY . /app/voice-clone-tts

# 设置工作目录
WORKDIR /app/voice-clone-tts

# 安装项目
RUN pip install -e .

# 创建必要的目录
RUN mkdir -p /app/voices /app/outputs /app/logs

# 设置环境变量
ENV VOICE_ENGINE=xtts
ENV VOICE_HOST=0.0.0.0
ENV VOICE_PORT=8000
ENV VOICES_DIR=/app/voices
ENV OUTPUT_DIR=/app/outputs
ENV LOG_DIR=/app/logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "production/main.py", "serve", "--engine", "xtts", "--host", "0.0.0.0", "--port", "8000"]
