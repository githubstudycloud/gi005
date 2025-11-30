# Voice Clone TTS v3.1.0 问题修复清单

**生成日期**: 2025-11-30
**最后更新**: 2025-11-30
**状态说明**: [ ] 未修复 | [x] 已修复 | [-] 不修复(说明原因)

---

## P0 - 发布前必须修复 (Critical)

### 安全问题
- [x] **DEPLOY-001**: 移除 CORS 通配符 `config.yaml:69` - 已改为具体域名列表
- [x] **DEPLOY-002**: 创建非 root 容器用户 `Dockerfile:65-73` - 已添加 appuser
- [x] **DEPLOY-003**: 改用 wheel 安装替代 `pip install -e .` - 已改为 `pip install .`
- [x] **DEPLOY-004**: 修复相对路径问题 `docker-compose.yml:79` - 使用环境变量 ${XTTS_MODEL_PATH:-./models/xtts}
- [x] **DEPLOY-005**: 解决端口映射冲突 `docker-compose.yml` - CPU 版本改用 8004 端口

### 代码问题
- [x] **CODE-001**: 修复裸 except 子句 `base_worker.py:559,564` - 已改为具体异常类型+日志
- [x] **CODE-002**: 验证 UUID 默认工厂 `models.py:47,182` - 已验证设计合理并添加注释说明

### 文档问题
- [x] **DOC-001**: 更新所有 `production/` 引用为 `src/` - 已重写 README.md
- [x] **DOC-002**: 修正 CLI 命令文档 - 已更新为 gateway/worker/standalone 模式
- [x] **DOC-003**: 更新项目结构图 - 已更新为 v3 架构

### 测试问题
- [x] **TEST-001**: 修复 asyncio 事件循环 `conftest.py:130-134` - 已使用 new_event_loop()
- [x] **TEST-002**: 添加 worker 资源清理 `conftest.py:139-142` - 已添加 finally cleanup
- [x] **TEST-003**: 重构 fixture 使用 pytest.skip() - 已修复 test_api.py
- [x] **TEST-004**: 修复 Enum 比较方式 `test_models.py:27` - 使用 .value 显式比较

### 配置优化
- [x] **DEPLOY-009**: 降低 GPU 显存配置 `config.yaml:79` - 已改为 0.6

---

## P1 - 本周完成 (Major)

### 配置和版本
- [ ] **DOC-004**: 统一 Python 版本约束
- [ ] **DOC-007**: 统一版本号为 3.1.0
- [ ] **DEPLOY-006**: 锁定 requirements.txt 依赖版本
- [ ] **DEPLOY-007**: 统一 PyTorch 版本
- [ ] **DEPLOY-008**: 修正 pyproject.toml 包路径

### 代码质量
- [ ] **CODE-003**: 补充类型注解 `openvoice_worker.py`
- [ ] **CODE-004**: 修复反模式导入
- [ ] **CODE-005**: 提取超时值为配置
- [ ] **CODE-006**: 添加 WebSocket 异常日志
- [ ] **CODE-007**: 封装全局状态

### 部署
- [x] **CODE-GPU**: GPU 指标异常处理 `base_worker.py:356-360` - 已分离 ImportError 和其他异常
- [ ] **DEPLOY-010**: 使用版本标签替代 :latest

---

## P2 - 两周内完成

### 文档
- [ ] **DOC-005**: 修正 Python SDK 示例
- [ ] **DOC-006**: 更新 Dockerfile 示例

### 代码
- [ ] **CODE-008**: 统一 print/logger 使用
- [ ] **CODE-009**: 移除注释死代码
- [ ] **CODE-010**: 实现 cleanup_expired()

### 测试
- [ ] 补充 Models 验证规则测试
- [ ] 添加 Gateway 功能测试
- [ ] 添加 Workers 功能测试
- [ ] 添加错误处理测试
- [ ] 添加集成测试
- [ ] 添加并发测试

---

## P3 - 后续迭代

- [ ] 整合存档文档
- [ ] 添加 API 认证
- [ ] 实施日志审计
- [ ] 添加 CI/CD 安全扫描
- [ ] 性能优化

---

## 修复进度统计

| 优先级 | 总计 | 已修复 | 未修复 | 完成率 |
|--------|------|--------|--------|--------|
| P0 | 14 | 14 | 0 | 100% |
| P1 | 12 | 1 | 11 | 8% |
| P2 | 9 | 2 | 7 | 22% |
| P3 | 5 | 0 | 5 | 0% |
| **总计** | **40** | **17** | **23** | **43%** |

---

## 已修复问题详情

### v3.2.1 修复 (2025-11-30)

1. **DEPLOY-003** Dockerfile `pip install -e .` → `pip install .`
2. **DEPLOY-004** docker-compose 相对路径 → 使用环境变量 `${XTTS_MODEL_PATH:-./models/xtts}`
3. **DEPLOY-005** 端口冲突 → CPU 版本改用 8004 端口
4. **CODE-002** UUID 默认工厂 → 验证合理，添加注释说明设计意图

### v3.2.0 修复 (2025-11-30)

1. **config.yaml CORS 配置** - 从 `["*"]` 改为 `["http://localhost:8080", "http://127.0.0.1:8080"]`
2. **config.yaml GPU 显存** - 从 `0.8` 降低到 `0.6`
3. **Dockerfile 非 root 用户** - 添加 appuser 用户并切换
4. **base_worker.py 裸 except** - 信号处理改为 `except (TypeError, SystemExit)` + 日志
5. **base_worker.py GPU 指标** - 分离 `except ImportError` 和 `except Exception`
6. **conftest.py 事件循环** - 使用 `asyncio.new_event_loop()` 替代 `get_event_loop()`
7. **conftest.py 资源清理** - 添加 `yield` + `finally` 块清理 worker
8. **test_api.py fixture** - 使用 `pytest.skip()` 替代返回 None
9. **test_models.py Enum** - 使用 `.value` 显式比较
10. **websocket.py 日志** - 添加 JSON 解析错误日志
11. **limiter.py 清理** - 实现 `cleanup_expired()` 方法
12. **README.md** - 重写匹配 v3 目录结构和 CLI 命令
13. **pyproject.toml** - 更新包路径和版本号

---

## 验证命令

```bash
# 代码格式检查
black --check voice-clone-tts/src/ tests/
isort --check voice-clone-tts/src/ tests/

# 类型检查
mypy voice-clone-tts/src/

# 安全扫描
bandit -r voice-clone-tts/src/
safety check -r voice-clone-tts/requirements-freeze.txt

# Dockerfile 检查
hadolint voice-clone-tts/Dockerfile

# 运行测试
pytest -v tests/
```

---

## 剩余 Critical 问题

✅ **所有 P0 Critical 问题已修复！** 可以发布 v3.2.1 版本。

剩余 P1/P2/P3 问题将在后续迭代中处理。

---

**v3.2.1 发布就绪**: 所有 Critical 问题已修复，可提交发布。
