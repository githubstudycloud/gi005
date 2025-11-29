# Voice Clone TTS v3.0 - 企业级微服务架构

v3 版本采用微服务架构，提供服务注册与发现、多节点负载均衡、状态监控、管理控制等企业级功能。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Gateway (网关)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ 状态页面  │  │ 管理页面  │  │ 测试页面  │  │ API 路由 + 限流  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┤
│  │              服务注册中心 (Service Registry)                   │
│  └───────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ XTTS Worker  │     │OpenVoice    │     │GPT-SoVITS   │
│    :8001     │     │Worker :8002 │     │Worker :8003 │
└──────────────┘     └──────────────┘     └──────────────┘
```

## 快速开始

### 1. 启动网关

```bash
cd voice-clone-tts
python -m v3.main gateway --port 8080
```

访问:
- 状态页面: http://localhost:8080/status
- 管理页面: http://localhost:8080/admin
- 测试页面: http://localhost:8080/playground

### 2. 启动工作节点

```bash
# XTTS 节点
python -m v3.main worker --engine xtts --port 8001 --gateway http://localhost:8080

# OpenVoice 节点 (开发中)
python -m v3.main worker --engine openvoice --port 8002 --gateway http://localhost:8080

# GPT-SoVITS 节点 (开发中)
python -m v3.main worker --engine gpt-sovits --port 8003 --gateway http://localhost:8080
```

### 3. 单机测试模式

```bash
# 启动网关 + XTTS 工作节点
python -m v3.main standalone --engine xtts --port 8080
```

## 目录结构

```
v3/
├── __init__.py               # 版本信息
├── main.py                   # 入口文件
├── README.md                 # 本文档
│
├── common/                   # 公共模块
│   ├── __init__.py
│   ├── models.py             # 数据模型
│   ├── exceptions.py         # 异常定义
│   └── logging.py            # 日志系统（彩色控制台+JSON格式+文件轮转）
│
├── gateway/                  # 网关模块
│   ├── __init__.py
│   ├── app.py                # 网关应用（含HTML页面）
│   ├── registry.py           # 服务注册中心
│   ├── limiter.py            # 限流器
│   └── websocket.py          # WebSocket 实时状态推送
│
└── workers/                  # 工作节点模块
    ├── __init__.py
    ├── base_worker.py        # 工作节点基类
    ├── xtts_worker.py        # XTTS 工作节点
    ├── openvoice_worker.py   # OpenVoice 工作节点
    └── gpt_sovits_worker.py  # GPT-SoVITS 工作节点
```

## 功能特性

### 状态页面 (`/status`)

- 系统概览：在线节点数、请求统计、并发数
- 引擎状态：各引擎（XTTS/OpenVoice/GPT-SoVITS）的可用性
- 节点列表：详细的节点信息（CPU、内存、请求数）
- 公告展示：系统公告和维护通知

### 管理页面 (`/admin`)

- 节点控制：激活/待机/移除节点
- 模型管理：加载/卸载模型（不需重启服务）
- 公告管理：发布/删除系统公告

### API 测试页面 (`/playground`)

- 语音合成测试：填写参数、选择引擎、试听结果
- 音色提取测试：上传音频、提取音色
- API 文档：接口说明和参数示例

### 限流系统

- 全局限流：每分钟最大请求数
- IP 限流：单 IP 每分钟最大请求数
- 并发限制：同时处理的最大请求数
- 接口限流：单接口的请求限制

### WebSocket 实时状态

- 实时连接指示器：页面右上角显示连接状态（绿色=在线，红色=离线）
- 自动重连：断线后自动重连（3秒间隔）
- 支持的事件类型：
  - `system_status`: 系统状态更新（每2秒推送）
  - `node_online`: 节点上线通知
  - `node_offline`: 节点离线通知
  - `node_status_changed`: 节点状态变更
  - `announcement`: 系统公告推送

```javascript
// WebSocket 客户端示例
const ws = new WebSocket('ws://localhost:8080/ws');
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log(msg.type, msg.data);
};
```

### 企业级日志系统

- 彩色控制台输出（按级别着色）
- JSON 格式日志（便于 ELK 等日志系统集成）
- 自动文件轮转（按大小/时间轮转）
- 请求 ID 追踪（全链路追踪支持）
- FastAPI 请求日志中间件

```bash
# 日志配置示例
python -m v3.main gateway --port 8080 \
    --log-level DEBUG \
    --log-dir ./logs \
    --json-logs
```

## API 接口

### 系统接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/status` | GET | 系统状态 |
| `/api/nodes` | GET | 节点列表 |
| `/api/nodes/{id}` | GET | 节点详情 |
| `/api/nodes/register` | POST | 注册节点 |
| `/api/nodes/{id}/command` | POST | 发送控制命令 |
| `/ws` | WebSocket | 实时状态推送 |

### 业务接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/synthesize` | POST | 语音合成 |
| `/api/extract_voice` | POST | 提取音色 |
| `/api/batch_synthesize` | POST | 批量合成 |

### 请求示例

```bash
# 语音合成
curl -X POST http://localhost:8080/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是测试",
    "voice_id": "default",
    "language": "zh"
  }' \
  --output output.wav

# 提取音色
curl -X POST http://localhost:8080/api/extract_voice \
  -F "audio=@reference.wav" \
  -F "voice_name=我的音色"
```

## 节点状态说明

| 状态 | 说明 |
|------|------|
| `standby` | 待机状态，模型未加载 |
| `loading` | 加载中，正在加载模型 |
| `ready` | 就绪状态，可接受请求 |
| `busy` | 繁忙状态，正在处理请求 |
| `error` | 错误状态，发生异常 |
| `offline` | 离线状态，无心跳 |

## 部署架构

### 单机部署

```bash
# 启动网关
python -m v3.main gateway --port 8080 &

# 启动一个 XTTS 节点
python -m v3.main worker --engine xtts --port 8001 --gateway http://localhost:8080
```

### 多节点部署

```bash
# 机器 A: 网关
python -m v3.main gateway --port 8080

# 机器 B: XTTS 节点 1
python -m v3.main worker --engine xtts --port 8001 --gateway http://机器A:8080

# 机器 C: XTTS 节点 2
python -m v3.main worker --engine xtts --port 8001 --gateway http://机器A:8080

# 机器 D: OpenVoice 节点
python -m v3.main worker --engine openvoice --port 8002 --gateway http://机器A:8080
```

### Nginx 反向代理

```nginx
upstream voice_clone_gateway {
    server 192.168.1.10:8080;
    server 192.168.1.11:8080 backup;
}

server {
    listen 80;
    server_name tts.example.com;

    location / {
        proxy_pass http://voice_clone_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 配置说明

### 网关配置

```python
SystemConfig(
    global_rpm=1000,      # 全局每分钟请求数
    ip_rpm=100,           # 单IP每分钟请求数
    concurrent_limit=50,  # 并发限制
    default_engine="xtts",# 默认引擎
    heartbeat_interval=10,# 心跳间隔（秒）
    dead_threshold=30,    # 节点死亡阈值（秒）
)
```

### 工作节点配置

```bash
python -m v3.main worker \
    --engine xtts \
    --port 8001 \
    --gateway http://localhost:8080 \
    --device cuda \
    --voices-dir ./voices \
    --auto-load  # 启动时自动加载模型
```

## 开发指南

### 添加新引擎

1. 创建工作节点类，继承 `BaseWorker`：

```python
# v3/workers/my_engine_worker.py
from .base_worker import BaseWorker

class MyEngineWorker(BaseWorker):
    async def load_model(self) -> bool:
        # 加载模型逻辑
        pass

    async def unload_model(self) -> bool:
        # 卸载模型逻辑
        pass

    async def synthesize(self, text, voice_id, language, **kwargs) -> bytes:
        # 合成语音逻辑
        pass

    async def extract_voice(self, audio_data, voice_id, voice_name, **kwargs) -> VoiceInfo:
        # 提取音色逻辑
        pass
```

2. 在 `main.py` 中注册新引擎

## 版本历史

- v3.0.0 (2025-11-29)
  - 微服务架构重构
  - 服务注册与发现
  - 状态监控页面（/status）
  - 管理控制页面（/admin）
  - API 测试页面（/playground）
  - 多层限流系统
  - WebSocket 实时状态推送
  - 企业级日志系统（彩色控制台+JSON格式+文件轮转）
  - 三引擎支持：XTTS、OpenVoice、GPT-SoVITS
