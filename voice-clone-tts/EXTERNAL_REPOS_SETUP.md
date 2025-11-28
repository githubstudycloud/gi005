# 外部 Git 仓库设置指南

本项目依赖一些外部 Git 仓库的源代码。由于这些仓库较大且更新频繁，我们不将它们直接包含在本仓库中，需要单独克隆。

---

## 一、需要克隆的仓库

| 仓库 | 用途 | 大小（约） | 必需？ |
|------|------|----------|--------|
| OpenVoice | 音色转换引擎 | 50MB | ✅ 是 |
| GPT-SoVITS | 中文音色克隆（高级） | 500MB | ❌ 可选 |

---

## 二、克隆 OpenVoice（必需）

### 2.1 使用 Git 克隆

```bash
# 进入项目根目录
cd gi005

# 克隆 OpenVoice 仓库
git clone https://github.com/myshell-ai/OpenVoice.git

# 如果网络较慢，可以使用代理
git clone --config http.proxy=http://你的代理:端口 https://github.com/myshell-ai/OpenVoice.git
```

### 2.2 验证目录结构

克隆后，目录结构应该如下：

```
gi005/
├── OpenVoice/                    # ← 克隆的仓库
│   ├── openvoice/               # Python 包
│   │   ├── __init__.py
│   │   ├── api.py              # ToneColorConverter 类
│   │   ├── se_extractor.py     # 音色提取
│   │   └── ...
│   ├── requirements.txt
│   └── setup.py
├── checkpoints_v2/              # OpenVoice 模型（从分卷包还原）
├── voice-clone-tts/             # 本项目代码
└── ...
```

### 2.3 安装 OpenVoice 依赖

```bash
# 确保已激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 进入 OpenVoice 目录
cd OpenVoice

# 以开发模式安装（推荐）
pip install -e .

# 或者直接安装依赖
pip install -r requirements.txt

# 返回项目根目录
cd ..
```

### 2.4 安装额外依赖

```bash
# edge-tts 用于生成基础语音
pip install edge-tts

# 如果需要使用代理
pip install --proxy http://你的代理:端口 edge-tts
```

---

## 三、克隆 GPT-SoVITS（可选）

GPT-SoVITS 是一个更强大的中文音色克隆方案，但配置较为复杂。

### 3.1 克隆仓库

```bash
cd gi005
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
```

### 3.2 环境要求

GPT-SoVITS 有特殊的环境要求：

- 建议使用独立的 conda 环境
- 需要下载额外的预训练模型（约 5-10GB）
- 详细配置请参考其官方文档

### 3.3 基本安装（仅供参考）

```bash
# 创建独立环境（推荐）
conda create -n gpt-sovits python=3.10
conda activate gpt-sovits

# 进入目录
cd GPT-SoVITS

# 安装依赖
pip install -r requirements.txt

# 下载预训练模型
# 参考: https://github.com/RVC-Boss/GPT-SoVITS#pretrained-models
```

---

## 四、常见问题

### Q1: git clone 太慢怎么办？

**方案 A：使用代理**
```bash
git clone --config http.proxy=http://127.0.0.1:7890 https://github.com/myshell-ai/OpenVoice.git
```

**方案 B：使用国内镜像**
```bash
# 使用 gitclone.com 镜像
git clone https://gitclone.com/github.com/myshell-ai/OpenVoice.git

# 使用 ghproxy 代理
git clone https://ghproxy.com/https://github.com/myshell-ai/OpenVoice.git
```

**方案 C：下载 ZIP 压缩包**
1. 访问 https://github.com/myshell-ai/OpenVoice
2. 点击 "Code" -> "Download ZIP"
3. 解压到项目目录，重命名为 `OpenVoice`

### Q2: pip install -e . 报错怎么办？

**错误**：`error: Microsoft Visual C++ 14.0 or greater is required`

**解决**：安装 Visual Studio Build Tools
```
1. 运行 dependencies/vs_buildtools.exe（先还原分卷包）
2. 选择 "使用 C++ 的桌面开发" 工作负载
3. 安装完成后重新运行 pip install -e .
```

### Q3: 克隆的仓库在 .gitignore 中被忽略了吗？

是的。`.gitignore` 文件中包含：
```
OpenVoice/
GPT-SoVITS/
```

这是故意的，因为：
1. 这些仓库较大
2. 它们有自己的版本控制
3. 应该通过 git clone 单独获取

### Q4: 如何更新克隆的仓库？

```bash
# 更新 OpenVoice
cd OpenVoice
git pull origin main
cd ..

# 更新 GPT-SoVITS
cd GPT-SoVITS
git pull origin main
cd ..
```

---

## 五、离线环境设置

如果你在完全离线的环境中工作：

### 5.1 提前准备

在有网络的机器上：
```bash
# 克隆仓库
git clone https://github.com/myshell-ai/OpenVoice.git

# 打包
tar -cvf OpenVoice_source.tar OpenVoice/
```

### 5.2 传输到离线机器

将 `OpenVoice_source.tar` 复制到离线机器，然后：
```bash
cd gi005
tar -xvf OpenVoice_source.tar
```

### 5.3 离线安装依赖

```bash
# 在有网络的机器上下载 wheel 包
pip download -d ./wheels openvoice edge-tts

# 复制 wheels 目录到离线机器
# 在离线机器上安装
pip install --no-index --find-links=./wheels openvoice edge-tts
```

---

## 六、仓库信息

| 仓库 | GitHub 地址 | 文档 |
|------|-------------|------|
| OpenVoice | https://github.com/myshell-ai/OpenVoice | [官方文档](https://github.com/myshell-ai/OpenVoice#readme) |
| GPT-SoVITS | https://github.com/RVC-Boss/GPT-SoVITS | [官方文档](https://github.com/RVC-Boss/GPT-SoVITS#readme) |
