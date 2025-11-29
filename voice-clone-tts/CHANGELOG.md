# Changelog

本文档记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [2.1.1] - 2025-11-29

### 修复

- **音频预处理参数名冲突**: 修复 `AudioProcessor.process()` 中 `remove_silence` 参数名与同名函数冲突导致的 `'bool' object is not callable` 错误
  - 参数名改为 `do_remove_silence`
  - 创建函数别名 `_remove_silence = remove_silence`
  - 更新 `server.py` 调用处使用新参数名

### 验证

- 流式合成 API (`/synthesize_stream`): ✅ 通过
- 批量合成 API (`/synthesize_batch`): ✅ 通过
- 音频预处理 API (`/preprocess`): ✅ 通过
- GPT-SoVITS 模型: ✅ 全部下载完成

### 模型状态

GPT-SoVITS 预训练模型已完整下载（总计约 3.5GB）：

| 目录 | 文件 | 大小 |
|------|------|------|
| 根目录 | s2Gv3.pth | 734MB |
| gsv-v4-pretrained | s2Gv4.pth, vocoder.pth | 790MB |
| v2Pro | s2Gv2Pro.pth, s2Gv2ProPlus.pth, s2Dv2Pro.pth, s2Dv2ProPlus.pth | 588MB |
| chinese-roberta-wwm-ext-large | pytorch_model.bin | 622MB |
| chinese-hubert-base | pytorch_model.bin | 181MB |

---

## [2.1.0] - 2025-11-28

### 新增

- **流式合成支持**: 新增流式 TTS 合成功能，支持边合成边播放
- **批量合成**: 新增批量文本合成接口，提高处理效率
- **音频预处理**: 新增音频预处理工具，支持去噪、音量归一化
- **OpenAPI 文档**: 新增 `/docs` 端点，提供交互式 API 文档

### 变更

- 更新验证报告至 v2.0，包含完整的引擎验证结果
- 优化依赖版本约束，解决 numpy/pandas/scipy 版本冲突

### 修复

- 修复 NumPy 1.22.0 与 pandas 2.x 的兼容性问题
- 修复 scipy 1.12+ 与 numpy 1.22.0 的不兼容问题
- 修复 OpenVoice 无法找到 FFmpeg 的路径问题

### 验证

- XTTS-v2: ✅ 完整验证通过
- OpenVoice: ✅ 完整验证通过
- GPT-SoVITS: ✅ 代码验证通过，模型文件下载完成

---

## [2.0.0] - 2025-11-28

### 新增

- **工程化支持**: 完整的项目结构和配置文件
- **HTTP API 服务**: FastAPI 实现的 HTTP 服务器
- **Python 客户端**: 易用的 Python 客户端库
- **CLI 工具**: 完整的命令行工具支持
- **环境配置**: Conda 环境配置文件

### 核心功能

- 统一的引擎抽象层 `VoiceClonerBase`
- 三引擎支持：XTTS-v2、OpenVoice、GPT-SoVITS
- 音色提取与保存
- 语音合成
- 音色管理

---

## [1.0.0] - 2025-11-28

### 初始版本

- 基础音色克隆框架
- XTTS-v2 引擎实现
- OpenVoice 引擎实现
- GPT-SoVITS 引擎实现
- 详细的验证报告
- 完整的复现指南

### 文档

- PROJECT_SUMMARY.md: 项目总结
- VERIFICATION_REPORT.md: 验证报告
- COMPLETE_REPRODUCTION_GUIDE.md: 完整复现指南
- ARCHITECTURE.md: 架构文档

---

## 版本说明

### 版本号格式

`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复

### 引擎状态

| 引擎 | 当前状态 | 推荐场景 |
|------|---------|---------|
| XTTS-v2 | 生产就绪 | 多语言、快速部署 |
| OpenVoice | 生产就绪 | 音色转换、低资源 |
| GPT-SoVITS | 需独立部署 | 中文高质量合成 |

### 依赖版本

核心依赖版本（已验证）：

```
Python==3.10.x
torch==2.5.1+cu118
TTS==0.22.0
transformers<4.50
numpy==1.22.0
scipy<1.12
```
