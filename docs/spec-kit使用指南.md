# Spec-Kit 使用指南

> 规范驱动开发工具包 - 让规范成为可执行的，直接生成工作实现

## 目录

- [简介](#简介)
- [核心理念](#核心理念)
- [安装](#安装)
- [初始化项目](#初始化项目)
- [核心命令](#核心命令)
- [工作流程](#工作流程)
- [使用示例](#使用示例)
- [常见问题](#常见问题)

---

## 简介

**Spec-Kit** 是 GitHub 开源的规范驱动开发工具包，它颠覆了传统的开发方式：

- 传统方式: 需求 → 代码 → 文档（文档往往滞后或缺失）
- Spec-Kit: 规范 → AI 生成实现（规范即文档，始终同步）

### 特点

- ✅ 技术栈无关，支持任何编程语言和框架
- ✅ 兼容 16+ AI 编码助手（Claude Code, GitHub Copilot, Cursor 等）
- ✅ 适用于新项目、现有项目和迭代开发
- ✅ 规范与代码始终保持同步

---

## 核心理念

Spec-Kit 将开发流程标准化为五个步骤：

```
1. Constitution (宪法) → 定义项目原则和开发指南
2. Specify (规范)     → 描述需求和用户故事 (做什么)
3. Plan (计划)        → 创建技术实现方案 (怎么做)
4. Tasks (任务)       → 生成可执行任务列表
5. Implement (实施)   → 执行所有任务，构建功能
```

每一步都有对应的 AI 命令，确保开发过程可控、可追溯。

---

## 安装

### 前置要求

- Python 3.11+ (Spec-Kit 会自动下载)
- Git (可选，用于版本控制)
- `uv` 包管理器

### 步骤 1: 安装 uv

```bash
pip install uv
```

### 步骤 2: 安装 Spec-Kit CLI

**持久化安装（推荐）：**

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

**一次性使用：**

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <项目名>
```

### 步骤 3: 配置环境变量（可选）

Windows 用户需要将 Spec-Kit 添加到 PATH：

```bash
export PATH="C:\\Users\\<用户名>\\.local\\bin:$PATH"
```

或使用：

```bash
uv tool update-shell
```

---

## 初始化项目

### 新项目

```bash
# 指定 AI 助手（claude, copilot, cursor 等）
specify init my-project --ai claude

# 在当前目录初始化
specify init . --ai claude
```

### 现有项目

```bash
# 强制初始化（覆盖现有文件）
specify init . --ai claude --force

# 跳过 Git 初始化
specify init . --ai claude --no-git
```

### 手动初始化（网络受限时）

如果自动初始化失败，可以手动下载模板文件：

```bash
# 1. 创建目录结构
mkdir -p .claude/commands .speckit/spec .speckit/plan .speckit/tasks

# 2. 下载命令文件
cd .claude/commands
curl -L -O https://raw.githubusercontent.com/github/spec-kit/refs/heads/main/templates/commands/constitution.md
curl -L -O https://raw.githubusercontent.com/github/spec-kit/refs/heads/main/templates/commands/specify.md
curl -L -O https://raw.githubusercontent.com/github/spec-kit/refs/heads/main/templates/commands/plan.md
curl -L -O https://raw.githubusercontent.com/github/spec-kit/refs/heads/main/templates/commands/tasks.md
curl -L -O https://raw.githubusercontent.com/github/spec-kit/refs/heads/main/templates/commands/implement.md
```

### 初始化后的项目结构

```
项目根目录/
├── .claude/
│   └── commands/          # Spec-Kit 命令文件
│       ├── constitution.md
│       ├── specify.md
│       ├── plan.md
│       ├── tasks.md
│       └── implement.md
├── .speckit/
│   ├── spec/              # 规范文档
│   ├── plan/              # 实现计划
│   └── tasks/             # 任务列表
└── CLAUDE.md              # AI 助手指南（可选）
```

---

## 核心命令

### 1. `/speckit.constitution` - 项目宪法

**用途**: 定义项目的核心原则、开发指南和技术决策

**何时使用**:
- 项目启动时
- 更新核心原则时
- 添加新的开发规范时

**示例**:

```
/speckit.constitution

我们的项目原则：
1. 代码质量优先 - 所有代码必须通过测试
2. 性能第一 - 响应时间 < 100ms
3. 用户体验至上 - 界面简洁直观
```

**生成内容**: `memory/constitution.md`

---

### 2. `/speckit.specify` - 功能规范

**用途**: 描述需求、用户故事和功能详细说明（"做什么"）

**何时使用**:
- 开发新功能前
- 需求变更时
- 编写用户故事时

**示例**:

```
/speckit.specify

用户故事：
作为一个用户，我希望能够上传图片并自动识别文字，
这样我就可以快速提取图片中的文本内容。

验收标准：
- 支持 JPG/PNG 格式
- 识别准确率 > 95%
- 处理时间 < 5 秒
```

**生成内容**: `.speckit/spec/功能名.md`

---

### 3. `/speckit.plan` - 实现计划

**用途**: 基于规范创建技术实现方案（"怎么做"）

**何时使用**:
- 编写完规范后
- 需要技术方案评审时
- 选择技术栈时

**示例**:

```
/speckit.plan

请为图片文字识别功能创建实现计划。
技术栈: Python + Tesseract OCR
```

**生成内容**: `.speckit/plan/功能名-plan.md`

---

### 4. `/speckit.tasks` - 任务列表

**用途**: 将实现计划分解为可执行的任务列表

**何时使用**:
- 计划完成后
- 准备开始开发前
- 需要任务分配时

**示例**:

```
/speckit.tasks

请基于实现计划生成详细的任务列表。
```

**生成内容**: `.speckit/tasks/功能名-tasks.md`

**任务格式**:

```markdown
- [ ] 任务 1: 安装 Tesseract OCR
- [ ] 任务 2: 创建图片上传接口
- [ ] 任务 3: 实现 OCR 识别逻辑
- [ ] 任务 4: 添加单元测试
- [ ] 任务 5: 部署到生产环境
```

---

### 5. `/speckit.implement` - 执行实施

**用途**: 按照任务列表执行所有任务，构建功能

**何时使用**:
- 任务列表确认后
- 准备编写代码时

**示例**:

```
/speckit.implement

请开始实施图片文字识别功能。
```

**AI 行为**:
- 逐个完成任务列表中的任务
- 自动生成代码
- 运行测试
- 更新任务完成状态

---

## 工作流程

### 完整开发流程

```mermaid
graph TD
    A[/speckit.constitution] --> B[/speckit.specify]
    B --> C[/speckit.plan]
    C --> D[/speckit.tasks]
    D --> E[/speckit.implement]
    E --> F[功能完成]
```

### 实际操作步骤

#### 第 1 步: 定义项目宪法

```bash
# 在 Claude Code 中执行
/speckit.constitution

项目名称: Voice Clone TTS
核心原则:
1. 微服务架构 - Gateway + Worker 分布式部署
2. 多引擎支持 - XTTS-v2, OpenVoice, GPT-SoVITS
3. 生产就绪 - Docker, 负载均衡, 健康检查
```

#### 第 2 步: 编写功能规范

```bash
/speckit.specify

功能: 添加语音克隆缓存机制

用户故事:
作为系统管理员，我希望克隆的语音模型能被缓存，
这样重复请求时可以避免重复计算，提升响应速度。

需求:
- 缓存已提取的语音特征
- 支持 LRU 淘汰策略
- 缓存大小可配置（默认 100 个模型）
- 提供缓存清理 API
```

#### 第 3 步: 制定实现计划

```bash
/speckit.plan

请为语音克隆缓存机制创建详细的技术实现方案。
技术栈: Python + Redis
```

#### 第 4 步: 生成任务列表

```bash
/speckit.tasks

请基于实现计划生成可执行任务清单。
```

#### 第 5 步: 执行实施

```bash
/speckit.implement

请开始实施语音克隆缓存功能，完成所有任务。
```

---

## 使用示例

### 示例 1: 新功能开发

**场景**: 为项目添加用户认证功能

```bash
# Step 1: 编写规范
/speckit.specify

功能: 用户认证系统

需求:
- 支持邮箱 + 密码登录
- JWT Token 认证
- 刷新 Token 机制
- 密码加密存储（bcrypt）

# Step 2: 创建计划
/speckit.plan

技术栈: FastAPI + JWT + PostgreSQL

# Step 3: 生成任务
/speckit.tasks

# Step 4: 执行实施
/speckit.implement
```

### 示例 2: Bug 修复

**场景**: 修复语音合成超时问题

```bash
# Step 1: 描述问题
/speckit.specify

问题: 长文本合成时超时

复现步骤:
1. 输入超过 500 字的文本
2. 调用合成 API
3. 30 秒后返回超时错误

期望:
- 超时时间增加到 120 秒
- 添加进度反馈
- 支持分片合成

# Step 2-4: 正常流程
/speckit.plan
/speckit.tasks
/speckit.implement
```

### 示例 3: 重构现有代码

```bash
/speckit.specify

重构目标: 将单体应用拆分为微服务

当前架构:
- 单一 FastAPI 应用
- 所有功能耦合在一起

目标架构:
- Gateway 服务 (API 路由)
- Worker 服务 (TTS 引擎)
- 服务注册与发现

/speckit.plan
/speckit.tasks
/speckit.implement
```

---

## 常见问题

### Q1: Spec-Kit 与传统开发的区别？

**传统开发**:
- 需求 → 设计 → 编码 → 测试 → 文档
- 文档往往滞后或缺失
- 需求变更时文档难以同步

**Spec-Kit**:
- 规范 → AI 生成实现
- 规范即文档，始终同步
- 修改规范，自动更新实现

### Q2: 是否必须按顺序执行所有命令？

**建议流程**: constitution → specify → plan → tasks → implement

**灵活使用**:
- 小型修改可跳过 constitution
- 简单任务可直接 specify + implement
- 可以反复迭代任何步骤

### Q3: 如何与现有项目集成？

```bash
# 1. 在现有项目根目录初始化
specify init . --ai claude --force

# 2. 编写当前项目的宪法
/speckit.constitution

# 3. 为现有功能补充规范
/speckit.specify

# 4. 开始新功能开发
```

### Q4: 规范文件存储在哪里？

```
.speckit/
├── spec/              # 功能规范
│   ├── feature-1.md
│   └── feature-2.md
├── plan/              # 实现计划
│   ├── feature-1-plan.md
│   └── feature-2-plan.md
└── tasks/             # 任务列表
    ├── feature-1-tasks.md
    └── feature-2-tasks.md
```

### Q5: 如何更新已有规范？

```bash
# 重新运行命令会更新对应文件
/speckit.specify

更新: 添加多语言支持
- 支持中文、英文、日文
```

### Q6: 网络受限时如何安装？

使用代理：

```bash
# HTTP/HTTPS 代理
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# SOCKS5 代理
export HTTP_PROXY=socks5://proxy:port
export HTTPS_PROXY=socks5://proxy:port

# 然后执行安装
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

或手动下载模板文件（见"手动初始化"章节）。

### Q7: 支持哪些 AI 助手？

- Claude Code
- GitHub Copilot
- Cursor Agent
- Windsurf
- Gemini Code Assist
- Qwen Coder
- 以及其他 10+ AI 编码助手

### Q8: 如何查看 Spec-Kit 版本？

```bash
specify version
```

### Q9: 可以自定义命令吗？

可以！编辑 `.claude/commands/` 下的 Markdown 文件，
自定义提示词和工作流程。

### Q10: 如何卸载 Spec-Kit？

```bash
uv tool uninstall specify-cli

# 删除项目中的 Spec-Kit 文件
rm -rf .claude/commands .speckit
```

---

## 进阶技巧

### 1. 组合命令

```bash
# 一次性完成规范到任务
/speckit.specify
/speckit.plan
/speckit.tasks
```

### 2. 使用模板变量

在规范中使用占位符：

```markdown
项目名称: [PROJECT_NAME]
版本: [VERSION]
```

Spec-Kit 会自动填充这些变量。

### 3. 多人协作

```bash
# 团队成员 A: 编写规范
/speckit.specify

# 团队成员 B: 审核并创建计划
/speckit.plan

# 团队成员 C: 执行实施
/speckit.implement
```

### 4. CI/CD 集成

```yaml
# .github/workflows/spec-kit.yml
name: Spec-Kit Validation

on: [push]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check Spec Sync
        run: |
          # 检查规范与代码是否同步
          specify check
```

---

## 相关资源

- **官方仓库**: https://github.com/github/spec-kit
- **文档**: https://github.com/github/spec-kit/blob/main/README.md
- **问题反馈**: https://github.com/github/spec-kit/issues
- **社区讨论**: https://github.com/github/spec-kit/discussions

---

## 总结

Spec-Kit 将开发流程从"代码优先"转变为"规范优先"：

✅ **规范即文档** - 不再需要单独维护文档
✅ **AI 驱动开发** - 从规范自动生成实现
✅ **始终保持同步** - 规范和代码永不脱节
✅ **提高开发效率** - 减少沟通成本和返工

开始使用 Spec-Kit，体验规范驱动开发的威力！

---

**版本**: 1.0.0
**更新时间**: 2025-12-02
**维护者**: Voice Clone TTS 项目团队
