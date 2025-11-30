# Voice Clone TTS v3.1.0 问题修复清单

**生成日期**: 2025-11-30
**状态说明**: [ ] 未修复 | [x] 已修复 | [-] 不修复(说明原因)

---

## P0 - 发布前必须修复 (Critical)

### 安全问题
- [ ] **DEPLOY-001**: 移除 CORS 通配符 `config.yaml:69`
- [ ] **DEPLOY-002**: 创建非 root 容器用户 `Dockerfile`
- [ ] **DEPLOY-003**: 改用 wheel 安装替代 `pip install -e .`
- [ ] **DEPLOY-004**: 修复相对路径问题 `docker-compose.yml:79`
- [ ] **DEPLOY-005**: 解决端口映射冲突 `docker-compose.yml`

### 代码问题
- [ ] **CODE-001**: 修复裸 except 子句 `base_worker.py:559,564`
- [ ] **CODE-002**: 验证 UUID 默认工厂 `models.py:47,182`

### 文档问题
- [ ] **DOC-001**: 更新所有 `production/` 引用为 `src/`
- [ ] **DOC-002**: 修正 CLI 命令文档
- [ ] **DOC-003**: 更新项目结构图

### 测试问题
- [ ] **TEST-001**: 修复 asyncio 事件循环 `conftest.py:130`
- [ ] **TEST-002**: 添加 worker 资源清理 `conftest.py:133`
- [ ] **TEST-003**: 重构 fixture 使用 pytest.skip()
- [ ] **TEST-004**: 修复 Enum 比较方式 `test_models.py:27`

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
- [ ] **DEPLOY-009**: 降低 GPU 显存配置
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

**修复完成后**: 更新此清单状态，提交 PR 进行复审
