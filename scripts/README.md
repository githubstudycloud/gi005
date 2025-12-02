# 自动化部署脚本

Voice Clone TTS 项目的自动化安装和部署脚本集合。

---

## ⚠️ 重要说明: WSL2 安装位置

### 默认情况
WSL2 **默认安装在 C 盘**，位置：
```
C:\Users\<用户名>\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu22.04onWindows_...\
```

### 方案选择

#### 方案 A: WSL2 在 C 盘，项目在 WSL2 内部（默认）
- ✅ 性能最佳
- ✅ 配置简单
- ❌ 占用 C 盘空间（5-10GB）
- **适合**: C 盘空间充足（>30GB）

#### 方案 B: 迁移 WSL2 到 D 盘
- ✅ 性能最佳
- ✅ 完全不占用 C 盘
- ⚠️ 需要迁移操作（5-10分钟）
- **适合**: C 盘空间不足，彻底迁移

#### 方案 C: WSL2 在 C 盘，项目在 D 盘（跨文件系统）
- ✅ 不占用 WSL2 C 盘空间
- ❌ 性能较差（跨文件系统，下降 50-70%）
- ⚠️ 不推荐用于生产环境
- **适合**: 测试或临时使用

#### 方案 D: 软链接方案（⭐ 强烈推荐，C/D 同盘）
- ⭐ **性能最佳**（WSL2 原生）
- ⭐ **项目数据在 D 盘**（节省 C 盘）
- ⭐ **同盘无性能损失**（C/D 同一物理磁盘）
- ⭐ **配置简单**（自动化脚本）
- ✅ 访问透明，应用无感知
- **适合**: C/D 盘是同一块固态硬盘的不同分区（您的情况）

---

## 文件列表

| 脚本 | 平台 | 用途 | 推荐度 |
|------|------|------|--------|
| `install-wsl2-to-d-drive.ps1` | Windows PowerShell | **直接安装到 D 盘**（推荐新用户） | ⭐⭐⭐⭐⭐ |
| `wsl2-setup-cuda-pytorch.sh` | WSL2/Linux | **CUDA + PyTorch 环境配置** | ⭐⭐⭐⭐⭐ |
| `install-wsl2.ps1` | Windows PowerShell | 自动安装 WSL2 和 Ubuntu（C 盘） | ⭐⭐⭐⭐ |
| `wsl2-setup-with-symlink.sh` | WSL2/Linux | **软链接部署**（C/D 同盘最佳） | ⭐⭐⭐⭐⭐ |
| `wsl2-setup.sh` | WSL2/Linux | 项目部署在 WSL2 内部（C 盘） | ⭐⭐⭐⭐ |
| `move-wsl-to-d-drive.ps1` | Windows PowerShell | 迁移已有 WSL2 到 D 盘 | ⭐⭐⭐⭐ |
| `wsl2-setup-on-d-drive.sh` | WSL2/Linux | 部署到 D 盘（跨文件系统，慢） | ⭐⭐ |

---

## 使用方法

### 方式〇: 直接安装到 D 盘（⭐ 最新推荐）

**适用场景**: 全新安装 WSL2，直接指定安装到 D:\wsl\ubuntu22

**优势**:
- ⭐ 一步到位，无需迁移
- ⭐ 自定义安装路径
- ⭐ 完整 CUDA + PyTorch 支持
- ⭐ 不占用 C 盘空间

#### 步骤 1: 在 Windows 上安装 WSL2 到 D 盘

1. 以**管理员身份**打开 PowerShell
2. 运行安装脚本：

```powershell
cd D:\data\PycharmProjects\PythonProject1\scripts
.\install-wsl2-to-d-drive.ps1
```

3. 按照提示操作，脚本会自动：
   - 启用 WSL 和虚拟机平台功能
   - 下载 Ubuntu 22.04 WSL 镜像
   - 导入到 D:\wsl\ubuntu22
   - 配置默认用户

#### 步骤 2: 在 WSL2 中配置 CUDA、PyTorch 和项目

1. 启动 WSL2：

```powershell
wsl
```

2. 运行环境配置脚本：

```bash
cd /mnt/d/data/PycharmProjects/PythonProject1/scripts
chmod +x wsl2-setup-cuda-pytorch.sh
./wsl2-setup-cuda-pytorch.sh
```

3. 脚本会自动安装：
   - 基础开发工具（build-essential, cmake, git 等）
   - Python 3 + pip + venv
   - 音视频处理工具（FFmpeg, Sox 等）
   - CUDA Toolkit 12.1
   - cuDNN
   - PyTorch 2.1 with CUDA
   - 机器学习工具（transformers, tensorboard 等）
   - TTS 相关依赖
   - 克隆并配置项目

4. 启动服务：

```bash
cd ~/projects/gi005
./start-standalone.sh
```

5. 访问: http://localhost:8080

**详细文档**: `docs/WSL2-D盘安装详细指南.md`

---

### 方式一: 完全自动化（推荐）

#### 步骤 1: 在 Windows 上安装 WSL2

1. 以**管理员身份**打开 PowerShell
2. 运行安装脚本：

```powershell
cd D:\data\PycharmProjects\PythonProject1\scripts
.\install-wsl2.ps1
```

3. 按照提示操作：
   - 如果需要重启，脚本会提示
   - 重启后再次运行脚本完成安装
   - 首次启动 Ubuntu 时设置用户名和密码

#### 步骤 2: 在 WSL2 中配置环境和部署项目

1. 启动 WSL2 Ubuntu：

```bash
wsl
```

2. 访问脚本目录：

```bash
cd /mnt/d/data/PycharmProjects/PythonProject1/scripts
```

3. 赋予执行权限并运行：

```bash
chmod +x wsl2-setup.sh
./wsl2-setup.sh
```

4. 按照提示操作：
   - 输入 Git 用户名和邮箱
   - 将生成的 SSH 公钥添加到 GitHub
   - 等待自动安装完成

5. 完成后启动服务：

```bash
cd ~/projects/gi005
./start-standalone.sh
```

6. 在浏览器访问: http://localhost:8080

**注意**: 此方式项目部署在 WSL2 内部（C 盘），占用约 5-10GB 空间。

---

### 方式一B: 迁移 WSL2 到 D 盘（推荐，如果 C 盘空间不足）

**前提**: 已使用方式一安装了 WSL2

#### 迁移步骤

1. 以**管理员身份**打开 PowerShell

2. 运行迁移脚本：

```powershell
cd D:\data\PycharmProjects\PythonProject1\scripts
.\move-wsl-to-d-drive.ps1
```

3. 按照提示操作：
   - 脚本会导出当前 WSL2 到 D:\WSL2\Backup
   - 注销当前的 Ubuntu
   - 从备份导入到 D:\WSL2\Distros\Ubuntu-22.04
   - 验证安装

4. 迁移完成后，启动 WSL 验证：

```powershell
wsl
# 应该正常进入 Ubuntu
```

5. 项目文件仍在 ~/projects/gi005，无需重新部署

**磁盘使用情况**:
- 迁移后 C 盘释放约 2-5GB
- D 盘占用约 5-10GB（WSL2 系统 + 项目）

---

### 方式一D: 软链接方案（⭐ 强烈推荐，C/D 同盘）

**适用场景**: C 盘和 D 盘是同一块固态硬盘的不同分区

**原理**:
- WSL2 安装在 C 盘（性能最佳）
- 项目实际存储在 D 盘（节省 C 盘空间）
- 使用软链接连接两者（访问透明，无性能损失）

#### 部署步骤

1. 先安装 WSL2（按方式一的步骤 1）

2. 在 WSL2 中运行软链接部署脚本：

```bash
wsl
cd /mnt/d/data/PycharmProjects/PythonProject1/scripts
chmod +x wsl2-setup-with-symlink.sh
./wsl2-setup-with-symlink.sh
```

3. 脚本会自动：
   - 在 D 盘创建 `/mnt/d/WSL2-Projects/gi005`（实际存储）
   - 克隆项目到 D 盘
   - 创建软链接 `~/projects/gi005` → D 盘项目
   - 配置虚拟环境和依赖
   - 恢复模型文件

4. 验证软链接：

```bash
ls -la ~/projects/gi005
# 输出: lrwxrwxrwx ... /home/user/projects/gi005 -> /mnt/d/WSL2-Projects/gi005

readlink ~/projects/gi005
# 输出: /mnt/d/WSL2-Projects/gi005
```

5. 启动服务：

```bash
cd ~/projects/gi005
./start-standalone.sh
```

**优势总结**:
- ⭐ WSL2 性能 100%（在 C 盘）
- ⭐ 项目数据在 D 盘（节省 C 盘 3-8GB）
- ⭐ 同盘无性能损失（同一固态硬盘）
- ⭐ 访问路径不变（对应用透明）

---

### 方式二: 项目部署到 D 盘（性能较慢，不推荐）

**适用场景**: WSL2 在 C 盘，但项目想放在 D 盘（跨文件系统）

#### 步骤

1. 启动 WSL2：

```bash
wsl
```

2. 运行 D 盘部署脚本：

```bash
cd /mnt/d/data/PycharmProjects/PythonProject1/scripts
chmod +x wsl2-setup-on-d-drive.sh
./wsl2-setup-on-d-drive.sh
```

3. 项目将部署到: `/mnt/d/WSL2-Projects/gi005`

4. 使用快捷命令：

```bash
gi005              # 进入项目目录
gi005-start        # 启动服务
```

**性能警告**:
- 跨文件系统访问（WSL2 → Windows）性能下降 50-70%
- 不推荐用于生产环境
- 建议使用方式一B迁移 WSL2 到 D 盘

---

### 方式三: 手动安装 WSL2

如果自动脚本失败，可以手动安装：

#### Windows PowerShell（管理员）

```powershell
# 1. 启用 WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 2. 启用虚拟机平台
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 3. 重启计算机
shutdown /r /t 0

# 4. 下载并安装 WSL2 内核更新
# 访问: https://aka.ms/wsl2kernel

# 5. 设置 WSL2 为默认版本
wsl --set-default-version 2

# 6. 安装 Ubuntu
wsl --install -d Ubuntu-22.04
```

然后继续使用 `wsl2-setup.sh` 脚本配置环境。

---

## 脚本功能说明

### install-wsl2.ps1

**功能:**
- ✅ 检查 Windows 版本和虚拟化支持
- ✅ 启用 WSL 和虚拟机平台功能
- ✅ 下载并安装 WSL2 Linux 内核更新
- ✅ 设置 WSL2 为默认版本
- ✅ 安装 Ubuntu 22.04
- ✅ 显示安装状态和下一步操作

**运行要求:**
- 必须以管理员身份运行
- Windows 10 Build 19041+ 或 Windows 11
- CPU 支持虚拟化（Intel VT-x 或 AMD-V）

### wsl2-setup.sh

**功能:**
- ✅ 更新 Ubuntu 系统包
- ✅ 安装开发工具（Git, FFmpeg, Python 等）
- ✅ 配置 Git 用户信息
- ✅ 生成并配置 SSH 密钥
- ✅ 克隆项目仓库
- ✅ 创建 Python 虚拟环境
- ✅ 安装项目依赖
- ✅ 恢复模型文件
- ✅ 创建启动脚本

**运行要求:**
- 必须在 WSL2 环境中运行
- 需要网络连接
- 需要 GitHub SSH 访问权限

---

## 启动脚本

配置完成后，会在项目根目录生成以下启动脚本：

### start-standalone.sh

独立模式启动（Gateway + Worker 一体）

```bash
cd ~/projects/gi005
./start-standalone.sh
```

**访问:**
- Gateway: http://localhost:8080
- 状态页: http://localhost:8080/status
- 管理页: http://localhost:8080/admin

### start-gateway.sh

仅启动 Gateway 服务

```bash
cd ~/projects/gi005
./start-gateway.sh
```

### start-xtts-worker.sh

启动 XTTS Worker（需要 Gateway 已启动）

```bash
cd ~/projects/gi005
./start-xtts-worker.sh
```

**分布式模式启动顺序:**

```bash
# 终端 1: Gateway
./start-gateway.sh

# 终端 2: XTTS Worker
./start-xtts-worker.sh

# 终端 3: OpenVoice Worker (可选)
python -m src.main worker --engine openvoice --port 8002 --gateway http://localhost:8080
```

---

## 常见问题

### Q1: PowerShell 提示"无法加载文件，因为在此系统上禁止运行脚本"

**解决方案:**

```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或临时允许
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

### Q2: wsl2-setup.sh 提示 "Permission denied"

**解决方案:**

```bash
# 赋予执行权限
chmod +x wsl2-setup.sh

# 然后运行
./wsl2-setup.sh
```

### Q3: Git clone 失败，提示 "Permission denied (publickey)"

**解决方案:**

1. 确保 SSH 密钥已生成：

```bash
ls -la ~/.ssh/id_ed25519.pub
```

2. 将公钥添加到 GitHub：

```bash
cat ~/.ssh/id_ed25519.pub
```

复制输出内容，添加到: https://github.com/settings/keys

3. 测试连接：

```bash
ssh -T git@github.com
```

### Q4: 脚本运行卡在某个步骤

**解决方案:**

按 `Ctrl+C` 中断脚本，然后手动完成后续步骤。脚本设计为幂等性，可以安全地重复运行。

### Q5: 模型文件恢复失败

**解决方案:**

手动恢复模型：

```bash
cd ~/projects/gi005/packages/models/xtts_v2

# 检查分卷包是否完整
ls -la xtts_v2_full.pkg.part_*

# 合并并解压
cat xtts_v2_full.pkg.part_* > xtts_v2.tar
mkdir -p extracted
tar -xvf xtts_v2.tar -C extracted/
```

### Q6: 如何更新脚本？

```bash
# 在 WSL2 中
cd ~/projects/gi005
git pull origin main

# 更新脚本权限
chmod +x scripts/*.sh
chmod +x *.sh
```

### Q7: 如何完全卸载？

**卸载 WSL2:**

```powershell
# Windows PowerShell（管理员）
wsl --unregister Ubuntu-22.04
wsl --shutdown
```

**删除项目:**

```bash
# 在 WSL2 中
rm -rf ~/projects/gi005
```

---

## 脚本定制

### 修改代理设置

编辑 `wsl2-setup.sh`，找到 Git 配置部分：

```bash
# 取消注释并修改代理地址
# git config --global http.proxy socks5://YOUR_PROXY:PORT
# git config --global https.proxy socks5://YOUR_PROXY:PORT
```

### 修改项目路径

默认项目路径: `~/projects/gi005`

修改 `wsl2-setup.sh` 中的 `PROJECT_DIR` 变量：

```bash
PROJECT_DIR="$HOME/your/custom/path"
```

### 跳过某些步骤

注释掉 `main()` 函数中不需要的步骤：

```bash
main() {
    # check_wsl2
    # update_system
    # install_basic_tools
    # ...（注释掉不需要的行）
}
```

---

## 日志和调试

### 启用详细输出

```bash
# 运行脚本时启用调试模式
bash -x wsl2-setup.sh
```

### 查看服务日志

```bash
# 查看 Gateway 日志
cd ~/projects/gi005
source venv/bin/activate
python -m src.main gateway --port 8080 --log-level DEBUG
```

---

## 贡献

如果您发现脚本有问题或有改进建议，请提交 Issue 或 Pull Request。

---

## 许可证

MIT License - 详见项目根目录 LICENSE 文件

---

**版本**: 1.0.0
**更新时间**: 2025-12-02
**维护者**: Voice Clone TTS 项目团队
