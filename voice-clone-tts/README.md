# Voice Clone TTS

企业级语音克隆微服务系统，支持多引擎（XTTS-v2、OpenVoice、GPT-SoVITS）。

## 特性

- **微服务架构** - 网关 + 工作节点，支持水平扩展
- **多引擎支持** - XTTS-v2、OpenVoice、GPT-SoVITS
- **服务注册发现** - 工作节点自动注册到网关
- **负载均衡** - 请求自动分发到可用节点
- **实时监控** - WebSocket 推送节点状态
- **优雅关闭** - 信号处理确保资源正确释放

## 快速开始

### 单机模式

```bash
cd voice-clone-tts
python -m src.main standalone --engine xtts --port 8080
```

访问:
- 状态页面: http://localhost:8080/status
- 管理页面: http://localhost:8080/admin
- API 测试: http://localhost:8080/playground

### 分布式部署

```bash
# 终端 1: 启动网关
python -m src.main gateway --port 8080

# 终端 2: 启动 XTTS 工作节点
python -m src.main worker --engine xtts --port 8001 --gateway http://localhost:8080 --auto-load

# 终端 3: 启动 OpenVoice 工作节点 (可选)
python -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080
```

## 项目结构

```
voice-clone-tts/
├── src/                      # 源代码
│   ├── main.py               # 入口文件
│   ├── common/               # 公共模块
│   │   ├── models.py         # 数据模型
│   │   ├── paths.py          # 路径配置
│   │   ├── exceptions.py     # 异常定义
│   │   └── logging.py        # 日志系统
│   ├── gateway/              # 网关模块
│   │   ├── app.py            # FastAPI 应用
│   │   ├── registry.py       # 服务注册中心
│   │   ├── limiter.py        # 限流器
│   │   └── websocket.py      # WebSocket
│   └── workers/              # 工作节点
│       ├── base_worker.py    # 基类
│       ├── xtts_worker.py    # XTTS-v2
│       ├── openvoice_worker.py
│       └── gpt_sovits_worker.py
├── voices/                   # 音色存储
├── config.yaml               # 配置文件
├── requirements.txt          # 依赖
├── Dockerfile                # Docker 镜像
└── docker-compose.yml        # Docker Compose
```

## API 接口

### 系统接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/status` | GET | 系统状态 |
| `/api/nodes` | GET | 节点列表 |
| `/ws` | WebSocket | 实时状态 |

### 业务接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/synthesize` | POST | 语音合成 |
| `/api/extract_voice` | POST | 提取音色 |
| `/api/voices` | GET | 音色列表 |

### 示例

```bash
# 提取音色
curl -X POST http://localhost:8080/api/extract_voice \
  -F "audio=@reference.wav" \
  -F "voice_name=my_voice"

# 语音合成
curl -X POST http://localhost:8080/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "你好", "voice_id": "my_voice", "language": "zh"}' \
  --output output.wav
```

## 模型配置

模型文件存放在 `packages/models/` 目录:

```bash
# 还原 XTTS-v2 模型
cd packages/models/xtts_v2
cat xtts_v2_full.pkg.part_* > xtts_v2.tar
tar -xvf xtts_v2.tar -C extracted/

# 还原 OpenVoice 模型
cd packages/models/openvoice
cat checkpoints_v2.pkg.part_* > checkpoints.tar
tar -xvf checkpoints.tar -C extracted/
```

## Docker 部署

```bash
# 启动网关 + XTTS 工作节点
docker-compose up -d gateway xtts-worker

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 引擎对比

| 引擎 | 音色提取 | 中文质量 | 参考音频需求 | 推荐场景 |
|------|---------|---------|-------------|---------|
| **XTTS-v2** | ✅ 支持 | ⭐⭐⭐ | 6秒 | 多语言克隆 |
| **OpenVoice** | ✅ 支持 | ⭐⭐⭐⭐ | 3-10秒 | 音色转换 |
| **GPT-SoVITS** | ✅ 支持 | ⭐⭐⭐⭐⭐ | 5秒 | 中文首选 |

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `GATEWAY_PORT` | 网关端口 | 8080 |
| `DEVICE` | 计算设备 | cuda |
| `LOG_LEVEL` | 日志级别 | INFO |
| `GPT_SOVITS_API_URL` | GPT-SoVITS API | http://127.0.0.1:9880 |

## 版本历史

### v3.1 (2025-11-30)
- 添加优雅关闭机制
- 改进信号处理
- 更新文档和配置

### v3.0 (2025-11-29)
- 微服务架构重构
- 服务注册与发现
- WebSocket 实时状态
- 多层限流系统

## 文档

详细文档请查看 [docs/](../docs/) 目录:

| 文档 | 说明 |
|------|------|
| [00-索引](../docs/00-索引.md) | 文档导航 |
| [01-快速开始](../docs/01-快速开始.md) | 5分钟上手 |
| [02-安装部署](../docs/02-安装部署.md) | 详细安装 |
| [03-使用指南](../docs/03-使用指南.md) | CLI/API使用 |
| [04-架构设计](../docs/04-架构设计.md) | 系统架构 |
| [05-API参考](../docs/05-API参考.md) | 接口详情 |
| [06-常见问题](../docs/06-常见问题.md) | FAQ |
| [07-更新日志](../docs/07-更新日志.md) | 版本历史 |

## 许可证

MIT License
