#!/bin/bash
# Voice Clone TTS - WSL2 一键启动脚本
# 在 WSL Ubuntu 中运行此脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/mnt/d/data/PycharmProjects/PythonProject1"
VOICE_CLONE_DIR="$PROJECT_DIR/voice-clone-tts"
GPT_SOVITS_DIR="$PROJECT_DIR/packages/GPT-SoVITS"

# 环境变量
export HF_ENDPOINT=https://hf-mirror.com
export GPT_SOVITS_API_URL=http://127.0.0.1:9880
export PYTHONPATH=$GPT_SOVITS_DIR

# 日志目录
LOG_DIR="/tmp/voice-clone-tts"
mkdir -p $LOG_DIR

echo -e "${GREEN}"
echo "========================================"
echo "   Voice Clone TTS - 启动脚本"
echo "========================================"
echo -e "${NC}"

# 检查是否有服务已在运行
check_port() {
    local port=$1
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        return 0  # 端口被占用
    fi
    return 1  # 端口空闲
}

# 等待服务启动
wait_for_service() {
    local port=$1
    local name=$2
    local max_wait=60
    local count=0

    echo -n "  等待 $name 启动"
    while ! check_port $port && [ $count -lt $max_wait ]; do
        echo -n "."
        sleep 1
        count=$((count + 1))
    done

    if check_port $port; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        return 1
    fi
}

# 启动 Gateway
start_gateway() {
    echo -e "${BLUE}[1/5]${NC} 启动 Gateway (端口 8080)..."
    cd $VOICE_CLONE_DIR
    nohup python3 -m src.main gateway --port 8080 > $LOG_DIR/gateway.log 2>&1 &
    echo $! > $LOG_DIR/gateway.pid
    wait_for_service 8080 "Gateway"
}

# 启动 XTTS Worker
start_xtts() {
    echo -e "${BLUE}[2/5]${NC} 启动 XTTS Worker (端口 8001)..."
    cd $VOICE_CLONE_DIR
    nohup python3 -m src.main worker \
        --engine xtts \
        --port 8001 \
        --gateway http://localhost:8080 \
        --device cpu \
        --auto-load > $LOG_DIR/xtts.log 2>&1 &
    echo $! > $LOG_DIR/xtts.pid
    wait_for_service 8001 "XTTS Worker"
}

# 启动 OpenVoice Worker
start_openvoice() {
    echo -e "${BLUE}[3/5]${NC} 启动 OpenVoice Worker (端口 8002)..."
    cd $VOICE_CLONE_DIR
    nohup python3 -m src.main worker \
        --engine openvoice \
        --port 8002 \
        --gateway http://localhost:8080 \
        --device cpu \
        --auto-load > $LOG_DIR/openvoice.log 2>&1 &
    echo $! > $LOG_DIR/openvoice.pid
    wait_for_service 8002 "OpenVoice Worker"
}

# 启动 GPT-SoVITS API
start_gpt_sovits_api() {
    echo -e "${BLUE}[4/5]${NC} 启动 GPT-SoVITS API (端口 9880)..."
    cd $GPT_SOVITS_DIR
    nohup python3 api_v2.py \
        -c GPT_SoVITS/configs/tts_infer_cpu.yaml \
        -a 0.0.0.0 \
        -p 9880 > $LOG_DIR/gpt_sovits_api.log 2>&1 &
    echo $! > $LOG_DIR/gpt_sovits_api.pid

    # GPT-SoVITS 启动较慢，需要更长等待时间
    echo -n "  等待 GPT-SoVITS API 启动"
    local count=0
    while ! check_port 9880 && [ $count -lt 120 ]; do
        echo -n "."
        sleep 1
        count=$((count + 1))
    done

    if check_port 9880; then
        echo -e " ${GREEN}✓${NC}"
    else
        echo -e " ${RED}✗${NC}"
    fi
}

# 启动 GPT-SoVITS Worker
start_gpt_sovits_worker() {
    echo -e "${BLUE}[5/5]${NC} 启动 GPT-SoVITS Worker (端口 8003)..."
    cd $VOICE_CLONE_DIR
    nohup python3 -m src.main worker \
        --engine gpt-sovits \
        --port 8003 \
        --gateway http://localhost:8080 \
        --device cpu \
        --auto-load > $LOG_DIR/gpt_sovits_worker.log 2>&1 &
    echo $! > $LOG_DIR/gpt_sovits_worker.pid
    wait_for_service 8003 "GPT-SoVITS Worker"
}

# 显示状态
show_status() {
    echo ""
    echo -e "${GREEN}========================================"
    echo "   所有服务已启动！"
    echo "========================================${NC}"
    echo ""
    echo "服务地址:"
    echo "  - Gateway:           http://localhost:8080"
    echo "  - XTTS Worker:       http://localhost:8001"
    echo "  - OpenVoice Worker:  http://localhost:8002"
    echo "  - GPT-SoVITS API:    http://localhost:9880"
    echo "  - GPT-SoVITS Worker: http://localhost:8003"
    echo ""
    echo "日志文件:"
    echo "  - Gateway:           $LOG_DIR/gateway.log"
    echo "  - XTTS:              $LOG_DIR/xtts.log"
    echo "  - OpenVoice:         $LOG_DIR/openvoice.log"
    echo "  - GPT-SoVITS API:    $LOG_DIR/gpt_sovits_api.log"
    echo "  - GPT-SoVITS Worker: $LOG_DIR/gpt_sovits_worker.log"
    echo ""
    echo "测试命令:"
    echo "  curl http://localhost:8080/health"
    echo "  curl http://localhost:8080/api/nodes"
}

# 停止所有服务
stop_all() {
    echo -e "${YELLOW}停止所有服务...${NC}"

    for pid_file in $LOG_DIR/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if kill -0 $pid 2>/dev/null; then
                kill $pid 2>/dev/null || true
                echo "  已停止 PID: $pid"
            fi
            rm -f "$pid_file"
        fi
    done

    echo -e "${GREEN}所有服务已停止${NC}"
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            start_gateway
            start_xtts
            start_openvoice
            start_gpt_sovits_api
            start_gpt_sovits_worker
            show_status
            ;;
        stop)
            stop_all
            ;;
        restart)
            stop_all
            sleep 2
            main start
            ;;
        status)
            echo "服务状态:"
            for port in 8080 8001 8002 9880 8003; do
                if check_port $port; then
                    echo -e "  端口 $port: ${GREEN}运行中${NC}"
                else
                    echo -e "  端口 $port: ${RED}未运行${NC}"
                fi
            done
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status}"
            exit 1
            ;;
    esac
}

main "$@"
