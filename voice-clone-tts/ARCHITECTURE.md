# 🏗️ 项目架构与导航

本文档提供项目整体架构、依赖关系和使用流程的可视化说明。

---

## 📚 文档导航

按以下顺序阅读文档：

| 序号 | 文档 | 说明 | 适合人群 |
|------|------|------|----------|
| 1 | [OFFLINE_QUICKSTART.md](./OFFLINE_QUICKSTART.md) | 🎯 傻瓜式完整部署指南 | **新手必读** |
| 2 | [EXTERNAL_REPOS_SETUP.md](./EXTERNAL_REPOS_SETUP.md) | 外部仓库克隆配置 | 所有用户 |
| 3 | [COMPLETE_REPRODUCTION_GUIDE.md](./COMPLETE_REPRODUCTION_GUIDE.md) | 详细复现指南 | 进阶用户 |
| 4 | [VERIFICATION_REPORT.md](./VERIFICATION_REPORT.md) | 验证报告与问题排查 | 遇到问题时 |
| 5 | [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) | 项目总结 | 了解全貌 |
| 6 | **本文档** | 架构图与流程图 | 理解原理 |

### 其他重要文件

| 目录/文件 | 说明 |
|-----------|------|
| [../dependencies/README.md](../dependencies/README.md) | 前置工具依赖包 |
| [../offline_package/README.md](../offline_package/README.md) | OpenVoice/Whisper 模型 |
| [../tts_model/README.md](../tts_model/README.md) | XTTS-v2 模型 |

---

## 🗂️ 项目目录结构

```mermaid
graph TB
    subgraph "gi005 项目根目录"
        ROOT["/"]

        subgraph "📦 分卷包目录"
            DEP["dependencies/<br/>前置工具分卷"]
            OFF["offline_package/<br/>模型分卷"]
            TTS["tts_model/<br/>XTTS分卷"]
        end

        subgraph "📝 项目代码"
            VCT["voice-clone-tts/<br/>主项目"]
            VCT --> PROD["production/<br/>生产代码"]
            VCT --> SOL["solutions/<br/>各引擎实现"]
            VCT --> EX["examples/<br/>示例代码"]
            VCT --> DOCS["*.md<br/>文档"]
        end

        subgraph "🔧 还原后目录"
            CP2["checkpoints_v2/<br/>OpenVoice模型"]
            XTTS["tts_model/xtts_v2/<br/>XTTS模型"]
            FF["ffmpeg.exe<br/>音频处理"]
        end

        subgraph "📥 需克隆仓库"
            OV["OpenVoice/<br/>音色转换源码"]
            GPT["GPT-SoVITS/<br/>可选"]
        end
    end

    ROOT --> DEP
    ROOT --> OFF
    ROOT --> TTS
    ROOT --> VCT
    ROOT --> CP2
    ROOT --> XTTS
    ROOT --> FF
    ROOT --> OV
```

### 详细目录树

```
gi005/
├── 📦 dependencies/              # 前置工具分卷包
│   ├── README.md
│   └── tools.pkg.part_*         # 7个分卷 (~585MB)
│
├── 📦 offline_package/           # 模型分卷包
│   ├── README.md
│   ├── checkpoints_v2.pkg.part_* # 2个分卷 (~126MB)
│   └── whisper_models.pkg.part_* # 16个分卷 (~1.5GB)
│
├── 📦 tts_model/                 # XTTS 模型分卷包
│   ├── README.md
│   └── xtts_v2_full.pkg.part_*  # 21个分卷 (~2GB)
│
├── 📝 voice-clone-tts/           # 主项目代码
│   ├── production/              # 生产环境代码
│   │   ├── main.py             # 命令行入口
│   │   ├── server.py           # HTTP API 服务
│   │   ├── client.py           # 客户端
│   │   ├── common/             # 公共模块
│   │   └── xtts/               # XTTS 引擎
│   │
│   ├── solutions/               # 各引擎独立实现
│   │   ├── 01-openvoice/
│   │   ├── 02-coqui-xtts/
│   │   ├── 03-gpt-sovits/
│   │   ├── 04-cosyvoice/
│   │   └── 05-fish-speech/
│   │
│   ├── examples/                # 示例代码
│   │
│   └── *.md                     # 文档文件
│
├── 🔧 checkpoints_v2/            # [还原后] OpenVoice 模型
│   ├── converter/
│   │   ├── config.json
│   │   └── checkpoint.pth
│   └── base_speakers/ses/
│       ├── en-us.pth
│       └── zh.pth
│
├── 🔧 tts_model/xtts_v2/         # [还原后] XTTS 模型
│   ├── config.json
│   ├── model.pth
│   ├── dvae.pth
│   ├── vocab.json
│   └── speakers_xtts.pth
│
├── 📥 OpenVoice/                 # [克隆] OpenVoice 源码
│   ├── openvoice/
│   │   ├── api.py
│   │   └── se_extractor.py
│   └── setup.py
│
├── 🔧 ffmpeg.exe                 # [还原后] 音频处理
├── 🔧 ffprobe.exe
├── 🔧 ffplay.exe
│
├── 🐍 venv/                      # Python 虚拟环境
│
├── .gitignore
├── CLAUDE.md
└── README.md
```

---

## 🔗 依赖关系图

### 整体依赖架构

```mermaid
graph TB
    subgraph "🖥️ 系统层"
        WIN[Windows 10/11]
        PY[Python 3.10.11]
        VS[Visual Studio<br/>Build Tools]
        FF[FFmpeg]
    end

    subgraph "🐍 Python 环境"
        TORCH[PyTorch 2.5.1]
        TTS_LIB[TTS 0.22.0]
        TRANS[transformers<br/>&lt;4.50]
        CT2[ctranslate2<br/>4.4.0]
        EDGE[edge-tts]
        LIBS[librosa<br/>soundfile<br/>numpy]
    end

    subgraph "🤖 模型文件"
        XTTS_M[XTTS-v2 模型<br/>~2GB]
        OV_M[OpenVoice 模型<br/>~126MB]
        WH_M[Whisper 模型<br/>~1.5GB<br/>可选]
    end

    subgraph "📦 源码仓库"
        OV_S[OpenVoice 源码]
        GPT_S[GPT-SoVITS 源码<br/>可选]
    end

    subgraph "🎯 功能引擎"
        XTTS_E[XTTS-v2 引擎<br/>端到端克隆]
        OV_E[OpenVoice 引擎<br/>音色转换]
        GPT_E[GPT-SoVITS 引擎<br/>中文优化]
    end

    WIN --> PY
    WIN --> VS
    WIN --> FF

    PY --> TORCH
    VS --> TTS_LIB
    TORCH --> TTS_LIB
    TTS_LIB --> TRANS
    TTS_LIB --> CT2

    TTS_LIB --> XTTS_E
    XTTS_M --> XTTS_E

    TORCH --> OV_S
    OV_S --> OV_E
    OV_M --> OV_E
    EDGE --> OV_E

    FF --> XTTS_E
    FF --> OV_E

    LIBS --> XTTS_E
    LIBS --> OV_E
```

### 模型与代码依赖

```mermaid
graph LR
    subgraph "XTTS-v2 引擎"
        X_CODE[voice-clone-tts/<br/>production/xtts/]
        X_MODEL[tts_model/xtts_v2/]
        X_LIB[TTS 库]

        X_LIB --> X_CODE
        X_MODEL --> X_CODE
    end

    subgraph "OpenVoice 引擎"
        O_CODE[OpenVoice/openvoice/]
        O_MODEL[checkpoints_v2/]
        O_EDGE[edge-tts]

        O_MODEL --> O_CODE
        O_EDGE --> O_CODE
    end

    subgraph "GPT-SoVITS 引擎"
        G_CODE[GPT-SoVITS/]
        G_API[API 服务<br/>:9880]

        G_CODE --> G_API
    end

    subgraph "统一接口"
        MAIN[main.py]
        SERVER[server.py]

        X_CODE --> MAIN
        O_CODE --> MAIN
        G_API --> MAIN
        MAIN --> SERVER
    end
```

---

## 🔄 运行流程

### 安装部署流程

```mermaid
flowchart TD
    START([开始]) --> CLONE[克隆/下载项目]

    CLONE --> RESTORE{还原分卷包}
    RESTORE --> R1[还原 dependencies]
    RESTORE --> R2[还原 offline_package]
    RESTORE --> R3[还原 tts_model]

    R1 --> INSTALL_TOOLS[安装工具]
    INSTALL_TOOLS --> I1[安装 Python 3.10]
    INSTALL_TOOLS --> I2[安装 VS Build Tools]
    INSTALL_TOOLS --> I3[配置 FFmpeg]

    I1 --> VENV[创建虚拟环境]
    I2 --> VENV
    I3 --> VENV

    VENV --> PIP[安装 Python 依赖]
    PIP --> P1[PyTorch]
    PIP --> P2[TTS 库]
    PIP --> P3[其他依赖]

    R2 --> CLONE_OV[克隆 OpenVoice]
    R3 --> READY

    P1 --> CLONE_OV
    P2 --> CLONE_OV
    P3 --> CLONE_OV

    CLONE_OV --> INSTALL_OV[安装 OpenVoice]
    INSTALL_OV --> VERIFY[运行验证脚本]
    VERIFY --> READY([部署完成])

    style START fill:#90EE90
    style READY fill:#90EE90
    style RESTORE fill:#FFE4B5
    style INSTALL_TOOLS fill:#FFE4B5
    style PIP fill:#87CEEB
```

### 音色克隆执行流程

```mermaid
flowchart TD
    subgraph "输入"
        REF[参考音频<br/>3-10秒]
        TEXT[要合成的文本]
    end

    subgraph "XTTS-v2 流程"
        X1[加载 XTTS 模型]
        X2[提取音色特征<br/>get_conditioning_latents]
        X3[文本转语音<br/>inference]
        X4[输出音频]

        REF --> X2
        X1 --> X2
        X2 --> X3
        TEXT --> X3
        X3 --> X4
    end

    subgraph "OpenVoice 流程"
        O1[加载 ToneColorConverter]
        O2[提取目标音色<br/>se_extractor.get_se]
        O3[生成基础语音<br/>edge-tts]
        O4[音色转换<br/>converter.convert]
        O5[输出音频]

        REF --> O2
        O1 --> O2
        TEXT --> O3
        O2 --> O4
        O3 --> O4
        O4 --> O5
    end

    X4 --> OUT[最终输出.wav]
    O5 --> OUT

    style REF fill:#FFB6C1
    style TEXT fill:#FFB6C1
    style OUT fill:#90EE90
```

---

## 🎮 使用流程

### 快速使用流程

```mermaid
flowchart LR
    subgraph "1. 准备"
        A1[准备参考音频] --> A2[3-10秒清晰语音]
        A3[准备文本] --> A4[要合成的内容]
    end

    subgraph "2. 选择引擎"
        B1{选择引擎}
        B1 -->|端到端| B2[XTTS-v2]
        B1 -->|音色转换| B3[OpenVoice]
        B1 -->|中文优化| B4[GPT-SoVITS]
    end

    subgraph "3. 执行"
        C1[运行代码/API]
        C2[等待处理]
        C3[获取输出音频]
    end

    A2 --> B1
    A4 --> B1
    B2 --> C1
    B3 --> C1
    B4 --> C1
    C1 --> C2 --> C3
```

### API 服务使用流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant S as Server<br/>(server.py)
    participant E as 引擎<br/>(XTTS/OpenVoice)
    participant M as 模型文件

    Note over S: 启动服务
    S->>M: 加载模型
    M-->>S: 模型就绪

    Note over U,S: HTTP API 调用
    U->>S: POST /clone<br/>{audio, text, engine}
    S->>E: 调用引擎
    E->>M: 读取模型
    E-->>S: 返回音频
    S-->>U: 返回 audio.wav

    Note over U,S: 提取音色
    U->>S: POST /extract<br/>{audio}
    S->>E: 提取特征
    E-->>S: 返回嵌入
    S-->>U: 返回 voice_id

    Note over U,S: 使用已保存音色
    U->>S: POST /synthesize<br/>{voice_id, text}
    S->>E: 合成语音
    E-->>S: 返回音频
    S-->>U: 返回 audio.wav
```

---

## 🧩 引擎对比

```mermaid
graph TB
    subgraph "XTTS-v2"
        X_IN[输入: 参考音频 + 文本]
        X_PROC[处理: 端到端模型]
        X_OUT[输出: 克隆语音]
        X_IN --> X_PROC --> X_OUT

        X_PROS[✅ 一步完成<br/>✅ 多语言支持<br/>✅ 质量稳定]
        X_CONS[❌ 模型较大 2GB<br/>❌ 速度较慢]
    end

    subgraph "OpenVoice"
        O_IN[输入: 参考音频 + 文本]
        O_TTS[步骤1: edge-tts 生成基础音频]
        O_CONV[步骤2: 音色转换]
        O_OUT[输出: 转换后语音]
        O_IN --> O_TTS --> O_CONV --> O_OUT

        O_PROS[✅ 模型小 126MB<br/>✅ 速度快<br/>✅ 灵活可控]
        O_CONS[❌ 需要两步<br/>❌ 依赖 edge-tts]
    end

    subgraph "GPT-SoVITS"
        G_IN[输入: 参考音频 + 文本]
        G_API[通过 API 调用]
        G_OUT[输出: 高质量中文语音]
        G_IN --> G_API --> G_OUT

        G_PROS[✅ 中文效果最佳<br/>✅ 可微调训练]
        G_CONS[❌ 配置复杂<br/>❌ 需独立部署]
    end
```

---

## 📊 文件大小统计

```mermaid
pie title 分卷包大小分布
    "XTTS-v2 模型 (2GB)" : 2000
    "Whisper 模型 (1.5GB)" : 1500
    "工具依赖 (585MB)" : 585
    "OpenVoice 模型 (126MB)" : 126
```

| 分类 | 文件 | 大小 | 分卷数 |
|------|------|------|--------|
| 模型 | tts_model/xtts_v2_full.pkg.part_* | ~2GB | 21 |
| 模型 | offline_package/whisper_models.pkg.part_* | ~1.5GB | 16 |
| 模型 | offline_package/checkpoints_v2.pkg.part_* | ~126MB | 2 |
| 工具 | dependencies/tools.pkg.part_* | ~585MB | 7 |
| **总计** | | **~4.2GB** | **46** |

---

## 🚀 快速命令参考

### 部署命令速查

```bash
# 1. 克隆项目
git clone https://github.com/githubstudycloud/gi005.git
cd gi005

# 2. 还原分卷包 (Windows CMD)
cd dependencies && copy /b tools.pkg.part_* tools.tar && tar -xvf tools.tar && cd ..
cd offline_package && copy /b checkpoints_v2.pkg.part_* cp.tar && tar -xvf cp.tar && move checkpoints_v2 ..\ && cd ..
cd tts_model && copy /b xtts_v2_full.pkg.part_* xtts.tar && tar -xvf xtts.tar && cd ..

# 3. 创建环境
python -m venv venv
venv\Scripts\activate

# 4. 安装依赖
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
pip install TTS==0.22.0 "transformers<4.50" ctranslate2==4.4.0 edge-tts

# 5. 克隆 OpenVoice
git clone https://github.com/myshell-ai/OpenVoice.git
cd OpenVoice && pip install -e . && cd ..

# 6. 验证
python test_setup.py
```

### 使用命令速查

```bash
# 启动 API 服务
python voice-clone-tts/production/server.py --engine xtts --port 8000

# 命令行使用
python voice-clone-tts/production/main.py clone \
    --engine openvoice \
    --reference voice.wav \
    --text "要合成的文本" \
    --output output.wav
```

---

## 📞 问题反馈

- GitHub Issues: https://github.com/githubstudycloud/gi005/issues
- 查看 [VERIFICATION_REPORT.md](./VERIFICATION_REPORT.md) 了解已知问题

---

*文档版本: 1.0 | 更新日期: 2025-11-28*
