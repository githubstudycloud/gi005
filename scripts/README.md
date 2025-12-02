# 自动化部署脚本

Voice Clone TTS 项目的自动化安装和部署脚本集合。

## 文件列表

| 脚本 | 平台 | 用途 |
|------|------|------|
| `install-wsl2.ps1` | Windows PowerShell | 自动安装 WSL2 和 Ubuntu |
| `wsl2-setup.sh` | WSL2/Linux | 自动配置 WSL2 环境并部署项目 |

---

## 使用方法

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

---

### 方式二: 手动安装 WSL2

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
