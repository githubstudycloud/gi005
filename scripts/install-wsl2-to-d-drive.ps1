# WSL2 直接安装到 D 盘脚本
# Voice Clone TTS 项目
# 版本: 1.0.0
# 说明: 以管理员身份运行此脚本

#Requires -RunAsAdministrator

# 配置
$InstallPath = "D:\wsl\ubuntu22"
$DistroName = "Ubuntu-22.04"
$TempDir = "$env:TEMP\wsl-install"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        [Parameter(Mandatory=$false)]
        [string]$Type = "INFO"
    )

    switch ($Type) {
        "INFO"    { Write-Host "[INFO] $Message" -ForegroundColor Green }
        "WARN"    { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
        "ERROR"   { Write-Host "[ERROR] $Message" -ForegroundColor Red }
        "SUCCESS" { Write-Host "[SUCCESS] $Message" -ForegroundColor Cyan }
        "STEP"    { Write-Host "[STEP] $Message" -ForegroundColor Magenta }
    }
}

# 检查管理员权限
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 检查 Windows 版本
function Test-WindowsVersion {
    Write-ColorOutput "检查 Windows 版本..." -Type "INFO"

    $version = [System.Environment]::OSVersion.Version

    if ($version.Major -lt 10) {
        Write-ColorOutput "Windows 版本过低，需要 Windows 10 版本 2004 或更高" -Type "ERROR"
        return $false
    }

    if ($version.Major -eq 10 -and $version.Build -lt 19041) {
        Write-ColorOutput "Windows 10 Build 版本过低，需要 Build 19041 或更高" -Type "ERROR"
        Write-ColorOutput "当前 Build: $($version.Build)" -Type "WARN"
        return $false
    }

    Write-ColorOutput "Windows 版本符合要求: $($version.Major).$($version.Minor) Build $($version.Build)" -Type "SUCCESS"
    return $true
}

# 检查虚拟化
function Test-Virtualization {
    Write-ColorOutput "检查虚拟化支持..." -Type "INFO"

    try {
        $virt = Get-WmiObject -Class Win32_Processor | Select-Object -ExpandProperty VirtualizationFirmwareEnabled

        if (-not $virt) {
            Write-ColorOutput "虚拟化未启用！请在 BIOS 中启用 Intel VT-x 或 AMD-V" -Type "ERROR"
            return $false
        }

        Write-ColorOutput "虚拟化已启用" -Type "SUCCESS"
        return $true
    } catch {
        Write-ColorOutput "无法检测虚拟化状态，继续安装..." -Type "WARN"
        return $true
    }
}

# 检查 WSL 功能状态
function Test-WSLFeatures {
    Write-ColorOutput "检查 WSL 功能状态..." -Type "INFO"

    $wsl = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
    $vmp = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform

    $result = @{
        WSLEnabled = $wsl.State -eq "Enabled"
        VMPEnabled = $vmp.State -eq "Enabled"
    }

    Write-ColorOutput "WSL 功能: $(if($result.WSLEnabled){'已启用'}else{'未启用'})" -Type "INFO"
    Write-ColorOutput "虚拟机平台: $(if($result.VMPEnabled){'已启用'}else{'未启用'})" -Type "INFO"

    return $result
}

# 启用 WSL 功能
function Enable-WSLFeatures {
    param([hashtable]$CurrentState)

    $needsRestart = $false

    if (-not $CurrentState.WSLEnabled) {
        Write-ColorOutput "启用 WSL 功能..." -Type "STEP"
        dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
        $needsRestart = $true
    }

    if (-not $CurrentState.VMPEnabled) {
        Write-ColorOutput "启用虚拟机平台..." -Type "STEP"
        dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
        $needsRestart = $true
    }

    return $needsRestart
}

# 下载 WSL2 内核更新
function Get-WSL2KernelUpdate {
    Write-ColorOutput "下载 WSL2 Linux 内核更新包..." -Type "STEP"

    if (-not (Test-Path $TempDir)) {
        New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    }

    $url = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
    $output = "$TempDir\wsl_update_x64.msi"

    try {
        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
        Write-ColorOutput "下载完成: $output" -Type "SUCCESS"
        return $output
    } catch {
        Write-ColorOutput "下载失败，请手动下载: https://aka.ms/wsl2kernel" -Type "ERROR"
        return $null
    }
}

# 安装 WSL2 内核更新
function Install-WSL2Kernel {
    param([string]$InstallerPath)

    Write-ColorOutput "安装 WSL2 内核更新..." -Type "STEP"

    try {
        Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$InstallerPath`" /quiet /norestart" -Wait
        Write-ColorOutput "WSL2 内核更新安装成功" -Type "SUCCESS"
        return $true
    } catch {
        Write-ColorOutput "内核更新安装失败: $_" -Type "ERROR"
        return $false
    }
}

# 下载 Ubuntu 发行版
function Get-UbuntuDistro {
    Write-ColorOutput "下载 Ubuntu 22.04 发行版..." -Type "STEP"

    if (-not (Test-Path $TempDir)) {
        New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    }

    $url = "https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-wsl.rootfs.tar.gz"
    $output = "$TempDir\ubuntu-22.04.tar.gz"

    # 检查是否已下载
    if (Test-Path $output) {
        Write-ColorOutput "发现已下载的文件: $output" -Type "INFO"
        $redownload = Read-Host "是否重新下载? (y/n)"
        if ($redownload -ne "y") {
            return $output
        }
    }

    Write-ColorOutput "正在下载 Ubuntu 22.04（约 500MB，请耐心等待）..." -Type "INFO"

    try {
        # 使用 BITS 下载（更稳定）
        Start-BitsTransfer -Source $url -Destination $output -DisplayName "下载 Ubuntu 22.04"
        Write-ColorOutput "下载完成: $output" -Type "SUCCESS"
        return $output
    } catch {
        Write-ColorOutput "BITS 下载失败，尝试 WebRequest..." -Type "WARN"

        try {
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
            Write-ColorOutput "下载完成: $output" -Type "SUCCESS"
            return $output
        } catch {
            Write-ColorOutput "下载失败: $_" -Type "ERROR"
            Write-ColorOutput "请手动下载 Ubuntu WSL 镜像到: $output" -Type "WARN"
            Write-ColorOutput "下载地址: $url" -Type "INFO"
            return $null
        }
    }
}

# 安装 Ubuntu 到指定目录
function Install-UbuntuToPath {
    param([string]$TarPath)

    Write-ColorOutput "安装 Ubuntu 22.04 到 $InstallPath..." -Type "STEP"

    # 确保目录存在
    if (-not (Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    }

    # 检查是否已安装同名发行版
    $existing = wsl --list --quiet 2>&1 | Where-Object { $_ -match $DistroName }
    if ($existing) {
        Write-ColorOutput "发现已安装的 $DistroName" -Type "WARN"
        $remove = Read-Host "是否先卸载? (y/n)"
        if ($remove -eq "y") {
            Write-ColorOutput "卸载现有发行版..." -Type "INFO"
            wsl --unregister $DistroName
        } else {
            Write-ColorOutput "跳过安装" -Type "INFO"
            return $false
        }
    }

    try {
        # 设置 WSL2 为默认版本
        wsl --set-default-version 2

        # 导入发行版到指定目录
        Write-ColorOutput "正在导入发行版（这可能需要几分钟）..." -Type "INFO"
        wsl --import $DistroName $InstallPath $TarPath

        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Ubuntu 22.04 安装成功到: $InstallPath" -Type "SUCCESS"
            return $true
        } else {
            Write-ColorOutput "安装失败，退出码: $LASTEXITCODE" -Type "ERROR"
            return $false
        }
    } catch {
        Write-ColorOutput "安装失败: $_" -Type "ERROR"
        return $false
    }
}

# 配置默认用户
function Set-DefaultUser {
    Write-ColorOutput "配置默认用户..." -Type "STEP"

    Write-Host ""
    Write-Host "Ubuntu 已以 root 用户安装。建议创建普通用户。"
    Write-Host ""

    $createUser = Read-Host "是否创建普通用户? (y/n)"

    if ($createUser -eq "y") {
        $username = Read-Host "输入用户名"

        if ($username) {
            Write-ColorOutput "创建用户 $username..." -Type "INFO"

            # 在 WSL 中创建用户
            wsl -d $DistroName -- bash -c "useradd -m -s /bin/bash $username"
            wsl -d $DistroName -- bash -c "usermod -aG sudo $username"

            Write-ColorOutput "设置用户密码..." -Type "INFO"
            wsl -d $DistroName -- passwd $username

            # 创建 /etc/wsl.conf 设置默认用户
            $wslConf = @"
[user]
default=$username

[boot]
systemd=true

[interop]
appendWindowsPath=true
"@

            # 写入配置
            wsl -d $DistroName -- bash -c "echo '$wslConf' > /etc/wsl.conf"

            Write-ColorOutput "用户 $username 创建成功，已设为默认用户" -Type "SUCCESS"
            Write-ColorOutput "需要重启 WSL 使配置生效" -Type "WARN"

            # 重启 WSL
            wsl --shutdown
            Start-Sleep -Seconds 2
        }
    } else {
        Write-ColorOutput "保持 root 用户为默认用户" -Type "INFO"
    }
}

# 验证安装
function Test-Installation {
    Write-ColorOutput "验证安装..." -Type "STEP"

    Write-Host ""
    Write-ColorOutput "已安装的 WSL 发行版:" -Type "INFO"
    wsl --list --verbose

    Write-Host ""
    Write-ColorOutput "测试 Ubuntu 启动:" -Type "INFO"
    wsl -d $DistroName -- uname -a

    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "安装验证成功！" -Type "SUCCESS"
        return $true
    } else {
        Write-ColorOutput "安装验证失败" -Type "ERROR"
        return $false
    }
}

# 显示磁盘使用情况
function Show-DiskUsage {
    Write-ColorOutput "磁盘使用情况:" -Type "INFO"

    # D 盘使用情况
    $drive = Get-PSDrive D -ErrorAction SilentlyContinue
    if ($drive) {
        $used = [math]::Round($drive.Used / 1GB, 2)
        $free = [math]::Round($drive.Free / 1GB, 2)
        $total = [math]::Round(($drive.Used + $drive.Free) / 1GB, 2)
        Write-Host "  D 盘: 已用 ${used}GB / 可用 ${free}GB / 总计 ${total}GB"
    }

    # WSL 安装目录大小
    if (Test-Path $InstallPath) {
        $size = (Get-ChildItem $InstallPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
        Write-Host "  WSL 安装目录: $([math]::Round($size, 2))GB"
    }
}

# 显示完成信息
function Show-Completion {
    Write-Host ""
    Write-Host "======================================"
    Write-ColorOutput "WSL2 Ubuntu 22.04 安装完成！" -Type "SUCCESS"
    Write-Host "======================================"
    Write-Host ""
    Write-Host "安装位置: $InstallPath"
    Write-Host ""
    Write-Host "下一步操作:"
    Write-Host ""
    Write-Host "1. 启动 WSL Ubuntu:"
    Write-Host "   wsl -d $DistroName"
    Write-Host ""
    Write-Host "2. 运行环境配置脚本（安装 CUDA、PyTorch 等）:"
    Write-Host "   cd /mnt/d/data/PycharmProjects/PythonProject1/scripts"
    Write-Host "   chmod +x wsl2-setup-cuda-pytorch.sh"
    Write-Host "   ./wsl2-setup-cuda-pytorch.sh"
    Write-Host ""
    Write-Host "3. 或使用别名快速启动:"
    Write-Host "   wsl"
    Write-Host ""
    Show-DiskUsage
    Write-Host ""
}

# 清理临时文件
function Clear-TempFiles {
    $cleanup = Read-Host "是否清理临时下载文件? (y/n)"
    if ($cleanup -eq "y") {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-ColorOutput "临时文件已清理" -Type "INFO"
    } else {
        Write-ColorOutput "临时文件保留在: $TempDir" -Type "INFO"
    }
}

# 主函数
function Main {
    Write-Host "======================================"
    Write-Host "  WSL2 Ubuntu 22.04 直接安装到 D 盘"
    Write-Host "======================================"
    Write-Host ""
    Write-Host "目标安装路径: $InstallPath"
    Write-Host ""

    # 检查管理员权限
    if (-not (Test-Administrator)) {
        Write-ColorOutput "请以管理员身份运行此脚本！" -Type "ERROR"
        Write-Host "右键点击脚本，选择 '以管理员身份运行'"
        Read-Host "按 Enter 退出"
        exit 1
    }

    # 检查 Windows 版本
    if (-not (Test-WindowsVersion)) {
        Read-Host "按 Enter 退出"
        exit 1
    }

    # 检查虚拟化
    Test-Virtualization | Out-Null

    # 检查 WSL 功能状态
    $featureState = Test-WSLFeatures

    # 启用 WSL 功能（如果需要）
    if (-not ($featureState.WSLEnabled -and $featureState.VMPEnabled)) {
        $needsRestart = Enable-WSLFeatures -CurrentState $featureState

        if ($needsRestart) {
            Write-ColorOutput "系统需要重启以完成 WSL 功能启用" -Type "WARN"
            $restart = Read-Host "是否现在重启? (y/n)"

            if ($restart -eq "y") {
                Write-ColorOutput "重启后，请再次运行此脚本继续安装" -Type "INFO"
                shutdown /r /t 10 /c "重启以完成 WSL 安装"
                exit 0
            } else {
                Write-ColorOutput "请手动重启后再次运行此脚本" -Type "WARN"
                Read-Host "按 Enter 退出"
                exit 0
            }
        }
    }

    # 下载并安装 WSL2 内核更新
    $kernelInstaller = Get-WSL2KernelUpdate
    if ($kernelInstaller) {
        Install-WSL2Kernel -InstallerPath $kernelInstaller | Out-Null
    }

    # 下载 Ubuntu 发行版
    $ubuntuTar = Get-UbuntuDistro
    if (-not $ubuntuTar) {
        Write-ColorOutput "无法获取 Ubuntu 发行版，安装终止" -Type "ERROR"
        Read-Host "按 Enter 退出"
        exit 1
    }

    # 安装 Ubuntu 到 D 盘
    if (-not (Install-UbuntuToPath -TarPath $ubuntuTar)) {
        Write-ColorOutput "Ubuntu 安装失败" -Type "ERROR"
        Read-Host "按 Enter 退出"
        exit 1
    }

    # 配置默认用户
    Set-DefaultUser

    # 验证安装
    Test-Installation | Out-Null

    # 显示完成信息
    Show-Completion

    # 清理临时文件
    Clear-TempFiles

    Read-Host "`n按 Enter 退出"
}

# 运行主函数
Main
