# 05 API 参考

## 基础信息

- **Base URL**: `http://localhost:8080`
- **格式**: JSON
- **认证**: 无 (建议生产环境添加)

---

## 系统接口

### GET /health

健康检查

**响应**:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "uptime_seconds": 3600.5
}
```

### GET /api/status

系统状态

**响应**:
```json
{
  "online_nodes": 2,
  "total_nodes": 3,
  "total_requests": 1500,
  "current_concurrent": 5,
  "engines": {
    "xtts": {"available": true, "node_count": 1},
    "openvoice": {"available": true, "node_count": 1},
    "gpt-sovits": {"available": false, "node_count": 0}
  },
  "announcements": []
}
```

### GET /api/nodes

节点列表

**响应**:
```json
{
  "nodes": [
    {
      "node_id": "xtts-abc123",
      "engine_type": "xtts",
      "host": "localhost",
      "port": 8001,
      "status": "ready",
      "model_loaded": true,
      "current_concurrent": 2
    }
  ],
  "count": 1
}
```

---

## 业务接口

### POST /api/extract_voice

提取音色

**请求** (multipart/form-data):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| audio | file | 是 | 参考音频 (WAV/MP3) |
| voice_name | string | 否 | 音色名称 |
| voice_id | string | 否 | 指定音色 ID |
| engine | string | 否 | 引擎 (xtts/openvoice) |

**示例**:
```bash
curl -X POST http://localhost:8080/api/extract_voice \
  -F "audio=@reference.wav" \
  -F "voice_name=my_voice"
```

**响应**:
```json
{
  "success": true,
  "voice_id": "abc12345",
  "voice_name": "my_voice",
  "engine": "xtts"
}
```

### POST /api/synthesize

语音合成

**请求** (application/json):
```json
{
  "text": "要合成的文本",
  "voice_id": "abc12345",
  "language": "zh",
  "engine": "xtts",
  "speed": 1.0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 合成文本 (1-5000字) |
| voice_id | string | 是 | 音色 ID |
| language | string | 否 | 语言代码，默认 zh |
| engine | string | 否 | 指定引擎 |
| speed | float | 否 | 语速 0.5-2.0 |

**响应**: `audio/wav` 二进制流

**示例**:
```bash
curl -X POST http://localhost:8080/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"你好","voice_id":"abc12345","language":"zh"}' \
  --output output.wav
```

### GET /api/voices

音色列表

**响应**:
```json
{
  "voices": [
    {
      "voice_id": "abc12345",
      "name": "my_voice",
      "engine": "xtts",
      "created_at": 1732934400.0
    }
  ]
}
```

### DELETE /api/voices/{voice_id}

删除音色

**响应**:
```json
{"success": true}
```

---

## 管理接口

### POST /api/nodes/register

注册节点 (Worker 调用)

**请求**:
```json
{
  "engine_type": "xtts",
  "host": "localhost",
  "port": 8001
}
```

### POST /api/nodes/{node_id}/heartbeat

心跳上报

### POST /api/announcements

发布公告

**请求**:
```json
{
  "title": "系统维护",
  "message": "将于今晚进行升级",
  "type": "info"
}
```

---

## WebSocket

### WS /ws

实时状态推送

**消息类型**:
```json
{"type": "system_status", "data": {...}}
{"type": "node_online", "data": {"node_id": "..."}}
{"type": "node_offline", "data": {"node_id": "..."}}
```

**JavaScript 示例**:
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## 错误响应

```json
{
  "error": "error_code",
  "message": "错误描述",
  "detail": "详细信息"
}
```

| 错误码 | HTTP 状态 | 说明 |
|--------|----------|------|
| voice_not_found | 404 | 音色不存在 |
| no_available_node | 503 | 无可用节点 |
| rate_limit_exceeded | 429 | 超出限流 |
| synthesis_failed | 500 | 合成失败 |

---

## 下一步

- 使用方法 → [03-使用指南](03-使用指南.md)
- 常见问题 → [06-常见问题](06-常见问题.md)
