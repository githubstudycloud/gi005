# 音色克隆 TTS 项目总结

本文档记录项目的需求分析、方案选型、问题解决过程，方便后续人机协作。

---

## 一、项目背景与需求

### 1.1 核心需求

用户需要实现**音色克隆 TTS**功能：
- 从一段参考音频中提取说话人的音色特征
- 使用提取的音色合成任意文本的语音
- 支持离线部署，无需联网
- 提供 HTTP API 便于集成

### 1.2 技术要求

- 中文语音质量要好
- 支持多语言（至少中英文）
- 部署简单，依赖少
- 显存需求合理（4-8GB）

---

## 二、方案调研与选型

### 2.1 调研的方案

共调研了 **5 种**开源音色克隆方案：

| 方案 | 来源 | 特点 | 中文质量 |
|------|------|------|---------|
| **XTTS-v2** | Coqui AI | 安装简单，17种语言 | ⭐⭐⭐ |
| **OpenVoice** | MyShell AI | 音色与内容分离 | ⭐⭐⭐⭐ |
| **GPT-SoVITS** | RVC-Boss | 中文效果最佳 | ⭐⭐⭐⭐⭐ |
| **CosyVoice** | 阿里通义 | 3秒克隆，跨语言 | ⭐⭐⭐⭐⭐ |
| **Fish-Speech** | Fish Audio | 低显存，快速推理 | ⭐⭐⭐⭐ |

### 2.2 最终方案

采用**多引擎统一封装**架构：

```
生产环境 (production/)
├── 统一 HTTP API (server.py)
├── 统一命令行 (main.py)
├── 统一客户端 (client.py)
└── 多引擎支持
    ├── XTTS-v2    → 推荐：快速部署
    ├── OpenVoice  → 推荐：音色转换
    └── GPT-SoVITS → 推荐：中文首选
```

### 2.3 选型理由

1. **XTTS-v2 作为默认引擎**
   - 安装最简单：`pip install TTS`
   - 模型自动下载
   - 离线模型已打包到仓库

2. **GPT-SoVITS 作为中文首选**
   - 中文效果最佳
   - 支持微调
   - 需要独立服务

3. **OpenVoice 作为补充**
   - 音色转换能力强
   - 可与其他 TTS 结合

---

## 三、实现过程

### 3.1 代码架构设计

```
voice-clone-tts/
├── production/           # 生产环境代码
│   ├── common/
│   │   ├── base.py      # VoiceClonerBase 基类
│   │   └── utils.py     # 工具函数
│   ├── xtts/
│   │   └── cloner.py    # XTTSCloner
│   ├── openvoice/
│   │   └── cloner.py    # OpenVoiceCloner
│   ├── gpt-sovits/
│   │   └── cloner.py    # GPTSoVITSCloner
│   ├── server.py        # FastAPI 服务
│   ├── main.py          # CLI 入口
│   └── client.py        # Python 客户端
│
├── solutions/            # 独立方案实现
│   ├── 04-cosyvoice/    # CosyVoice
│   └── 05-fish-speech/  # Fish-Speech
│
└── examples/             # 示例代码
```

### 3.2 核心接口设计

```python
# 基类定义
class VoiceClonerBase:
    def load_model(self): ...
    def extract_voice(self, audio_path, voice_id, ...) -> VoiceEmbedding: ...
    def synthesize(self, text, voice, output_path, ...) -> str: ...

# 音色数据类
@dataclass
class VoiceEmbedding:
    voice_id: str
    name: str
    source_audio: str
    embedding_path: str
    engine: str
    metadata: dict
```

### 3.3 HTTP API 设计

```
POST /extract_voice     - 提取音色
POST /synthesize        - 合成语音
POST /synthesize_direct - 直接克隆（不保存音色）
GET  /voices            - 列出音色
GET  /voices/{id}       - 获取音色详情
DELETE /voices/{id}     - 删除音色
GET  /health            - 健康检查
```

---

## 四、问题解决记录

### 4.1 模型文件过大无法直接上传 GitHub

**问题**：XTTS-v2 模型约 2GB，超过 GitHub 单文件 100MB 限制

**解决方案**：
```bash
# 使用 tar + split 分卷
tar -cvf - xtts_v2 | split -b 95m - xtts_v2.tar.part_

# 生成 21 个分卷文件 (aa ~ au)
```

**还原方法**：
```bash
cat xtts_v2.tar.part_* | tar -xvf -
```

### 4.2 Git 推送大文件失败

**问题**：一次推送 21 个 95MB 文件（约 2GB）导致连接超时

**解决方案**：
1. 分批推送，每批 4 个文件
2. 配置代理加速：
   ```bash
   git config --global http.proxy http://192.168.0.98:8800
   git config --global https.proxy http://192.168.0.98:8800
   ```

**推送批次**：
- 批次 1/6: aa-ad ✅
- 批次 2/6: ae-ah ✅
- 批次 3/6: ai-al ✅
- 批次 4/6: am-ap ✅
- 批次 5/6: aq-at ✅
- 批次 6/6: au ✅

### 4.3 离线部署依赖问题

**问题**：离线环境无法安装 Python 依赖

**解决方案**：
```bash
# 在有网机器上下载
pip download -r requirements.txt -d ./packages/

# 在离线机器上安装
pip install --no-index --find-links=./packages/ -r requirements.txt
```

### 4.4 XTTS 模型自动下载问题

**问题**：XTTS 默认会自动下载模型，离线环境无法使用

**解决方案**：
```python
# 使用本地模型路径
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

config = XttsConfig()
config.load_json("tts_model/xtts_v2/config.json")

model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir="tts_model/xtts_v2/")
```

### 4.5 GPT-SoVITS 需要参考文本

**问题**：GPT-SoVITS 提取音色时必须提供参考音频对应的文本

**解决方案**：
```python
# 在 extract_voice 中添加 reference_text 参数
def extract_voice(
    self,
    audio_path: str,
    voice_id: str = None,
    reference_text: str = ""  # GPT-SoVITS 必需
) -> VoiceEmbedding:
```

---

## 五、配置与部署

### 5.1 环境要求

- Python 3.8-3.10
- PyTorch 2.0+
- CUDA 11.7+ (GPU 加速)
- 显存 4GB+ (XTTS)

### 5.2 快速部署

```bash
# 1. 克隆仓库
git clone https://github.com/githubstudycloud/gi004.git
cd gi004

# 2. 还原模型
cd tts_model && cat xtts_v2.tar.part_* | tar -xvf - && cd ..

# 3. 安装依赖
pip install -r voice-clone-tts/production/requirements.txt

# 4. 启动服务
cd voice-clone-tts/production
python main.py serve --engine xtts --port 8000
```

### 5.3 使用示例

```python
from client import VoiceCloneClient

client = VoiceCloneClient("http://localhost:8000")

# 提取音色
voice = client.extract_voice("reference.wav", voice_name="我的声音")

# 合成语音
client.synthesize_to_file("你好世界", voice["voice_id"], "output.wav")
```

---

## 六、文件清单

### 6.1 核心代码文件

| 文件 | 说明 | 行数 |
|------|------|------|
| `production/common/base.py` | 基类定义 | ~230 |
| `production/common/utils.py` | 工具函数 | ~150 |
| `production/xtts/cloner.py` | XTTS 实现 | ~260 |
| `production/openvoice/cloner.py` | OpenVoice 实现 | ~280 |
| `production/gpt-sovits/cloner.py` | GPT-SoVITS 实现 | ~295 |
| `production/server.py` | HTTP 服务 | ~450 |
| `production/main.py` | CLI 入口 | ~310 |
| `production/client.py` | Python 客户端 | ~370 |

### 6.2 配置文件

| 文件 | 说明 |
|------|------|
| `production/requirements.txt` | 主依赖 |
| `production/environment.yml` | Conda 环境 |
| `tts_model/README.md` | 模型说明 |
| `OFFLINE_DEPLOYMENT.md` | 离线部署指南 |

### 6.3 模型文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `tts_model/xtts_v2.tar.part_*` | ~2GB | XTTS-v2 模型分卷 |

---

## 七、后续计划

### 7.1 待优化

- [ ] 添加流式合成支持
- [ ] 添加音频预处理（降噪、增强）
- [ ] 添加批量合成接口
- [ ] 添加 WebSocket 实时合成

### 7.2 待添加引擎

- [ ] 将 CosyVoice 集成到 production
- [ ] 将 Fish-Speech 集成到 production
- [ ] 添加 ChatTTS 支持

### 7.3 文档完善

- [ ] 添加 API 文档 (OpenAPI/Swagger)
- [ ] 添加性能测试报告
- [ ] 添加各引擎对比评测

---

## 八、参考资源

### 8.1 官方仓库

- [Coqui TTS (XTTS)](https://github.com/coqui-ai/TTS)
- [OpenVoice](https://github.com/myshell-ai/OpenVoice)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice)
- [Fish-Speech](https://github.com/fishaudio/fish-speech)

### 8.2 模型下载

- [XTTS-v2](https://huggingface.co/coqui/XTTS-v2)
- [OpenVoiceV2](https://huggingface.co/myshell-ai/OpenVoiceV2)
- [GPT-SoVITS](https://huggingface.co/lj1995/GPT-SoVITS)
- [CosyVoice-300M](https://modelscope.cn/models/iic/CosyVoice-300M)
- [Fish-Speech-1.5](https://huggingface.co/fishaudio/fish-speech-1.5)

---

## 九、协作记录

### 9.1 对话历史摘要

1. **需求分析**：用户需要音色克隆 TTS，支持从音频提取音色并合成语音
2. **方案调研**：调研了 5 种开源方案，分析优缺点
3. **代码实现**：设计统一架构，实现 3 个核心引擎
4. **模型处理**：将 XTTS-v2 模型打包分卷上传
5. **问题解决**：解决大文件推送、离线部署等问题
6. **文档编写**：编写离线部署指南和项目总结

### 9.2 关键决策

| 决策 | 原因 |
|------|------|
| 选择 XTTS 作为默认引擎 | 安装简单，无需额外服务 |
| 采用统一基类设计 | 便于扩展新引擎 |
| 模型分卷存储 | 绕过 GitHub 文件大小限制 |
| 提供 HTTP API | 便于各种语言集成 |

### 9.3 遗留问题

- CosyVoice 和 Fish-Speech 尚未集成到 production 目录
- 未添加音频预处理功能
- 未进行完整的性能测试

---

## 十、引擎验证结果（2025-11-28）

### 10.1 验证环境

- 操作系统: Windows 10
- Python: 3.10.11
- PyTorch: 2.5.1+cu118
- CUDA: 11.8

### 10.2 XTTS-v2 验证 ✅

| 项目 | 结果 |
|------|------|
| 模型加载 | 成功（本地模型） |
| 音色提取 | 成功（embedding shape: gpt_cond_latent + speaker_embedding） |
| 语音合成 | 成功（output: 333904 bytes） |
| 测试文本 | "This is a test of voice cloning with XTTS." |

### 10.3 OpenVoice 验证 ✅

| 项目 | 结果 |
|------|------|
| 模型加载 | 成功（converter checkpoint） |
| 音色提取 | 成功（SE shape: torch.Size([1, 256, 1])） |
| 语音合成 | 成功（output: 530988 bytes） |
| VAD 模式 | 使用 silero VAD，跳过 whisper 依赖 |

### 10.4 GPT-SoVITS 验证 ⚠️

| 项目 | 结果 |
|------|------|
| 代码导入 | 成功 |
| Cloner 实例化 | 成功 |
| API 服务 | 需要独立配置和运行 |
| 备注 | 需要额外下载 5-10GB 预训练模型 |

### 10.5 下载的模型

| 模型 | 大小 | 位置 |
|------|------|------|
| XTTS-v2 | ~2GB | tts_model/xtts_v2/ |
| OpenVoice Converter | ~150MB | checkpoints_v2/converter/ |
| OpenVoice Base Speakers | ~50MB | checkpoints_v2/base_speakers/ |
| faster-whisper-medium | ~1.5GB | whisper_models/faster-whisper-medium/ |

---

## 版本信息

- 文档版本: 1.1
- 创建日期: 2025-11-27
- 更新日期: 2025-11-28
- 仓库地址: https://github.com/githubstudycloud/gi005
- 维护者: Claude Code + User
