# WSL2 自动安装脚本
# Voice Clone TTS 项目
# 版本: 1.0.0
# 说明: 以管理员身份运行此脚本

#Requires -RunAsAdministrator

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

# 检查虚拟化是否启用
function Test-Virtualization {
    Write-ColorOutput "检查虚拟化支持..." -Type "INFO"

    $virt = Get-WmiObject -Class Win32_Processor | Select-Object -ExpandProperty VirtualizationFirmwareEnabled

    if (-not $virt) {
        Write-ColorOutput "虚拟化未启用！请在 BIOS 中启用 Intel VT-x 或 AMD-V" -Type "ERROR"
        return $false
    }

    Write-ColorOutput "虚拟化已启用" -Type "SUCCESS"
    return $true
}

# 检查 WSL 是否已安装
function Test-WSLInstalled {
    $wsl = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
    return $wsl.State -eq "Enabled"
}

# 启用 WSL 功能
function Enable-WSLFeature {
    Write-ColorOutput "启用 WSL 功能..." -Type "INFO"

    try {
        dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
        Write-ColorOutput "WSL 功能启用成功" -Type "SUCCESS"
        return $true
    } catch {
        Write-ColorOutput "WSL 功能启用失败: $_" -Type "ERROR"
        return $false
    }
}

# 启用虚拟机平台
function Enable-VirtualMachinePlatform {
    Write-ColorOutput "启用虚拟机平台..." -Type "INFO"

    try {
        dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
        Write-ColorOutput "虚拟机平台启用成功" -Type "SUCCESS"
        return $true
    } catch {
        Write-ColorOutput "虚拟机平台启用失败: $_" -Type "ERROR"
        return $false
    }
}

# 下载 WSL2 Linux 内核更新包
function Get-WSL2KernelUpdate {
    Write-ColorOutput "下载 WSL2 Linux 内核更新包..." -Type "INFO"

    $url = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
    $output = "$env:TEMP\wsl_update_x64.msi"

    try {
        # 使用代理（如果需要）
        # $proxy = "http://192.168.0.98:10800"
        # Invoke-WebRequest -Uri $url -OutFile $output -Proxy $proxy

        Invoke-WebRequest -Uri $url -OutFile $output
        Write-ColorOutput "下载完成: $output" -Type "SUCCESS"
        return $output
    } catch {
        Write-ColorOutput "下载失败: $_" -Type "ERROR"
        Write-ColorOutput "请手动下载: https://aka.ms/wsl2kernel" -Type "WARN"
        return $null
    }
}

# 安装 WSL2 内核更新
function Install-WSL2Kernel {
    param([string]$InstallerPath)

    Write-ColorOutput "安装 WSL2 内核更新..." -Type "INFO"

    try {
        Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$InstallerPath`" /quiet /norestart" -Wait
        Write-ColorOutput "WSL2 内核更新安装成功" -Type "SUCCESS"
        return $true
    } catch {
        Write-ColorOutput "WSL2 内核更新安装失败: $_" -Type "ERROR"
        return $false
    }
}

# 设置 WSL2 为默认版本
function Set-WSL2Default {
    Write-ColorOutput "设置 WSL2 为默认版本..." -Type "INFO"

    try {
        wsl --set-default-version 2
        Write-ColorOutput "WSL2 已设置为默认版本" -Type "SUCCESS"
        return $true
    } catch {
        Write-ColorOutput "设置默认版本失败: $_" -Type "ERROR"
        return $false
    }
}

# 安装 Ubuntu
function Install-Ubuntu {
    Write-ColorOutput "安装 Ubuntu 22.04..." -Type "INFO"

    try {
        wsl --install -d Ubuntu-22.04
        Write-ColorOutput "Ubuntu 22.04 安装完成" -Type "SUCCESS"
        Write-ColorOutput "首次启动时，请设置 Linux 用户名和密码" -Type "WARN"
        return $true
    } catch {
        Write-ColorOutput "Ubuntu 安装失败: $_" -Type "ERROR"
        Write-ColorOutput "请手动从 Microsoft Store 安装 Ubuntu 22.04" -Type "WARN"
        return $false
    }
}

# 显示已安装的 WSL 发行版
function Show-WSLDistributions {
    Write-ColorOutput "`n已安装的 WSL 发行版:" -Type "INFO"
    wsl --list --verbose
}

# 显示完成信息
function Show-Completion {
    Write-Host "`n======================================"
    Write-ColorOutput "WSL2 安装完成！" -Type "SUCCESS"
    Write-Host "======================================"
    Write-Host ""
    Write-Host "下一步操作:"
    Write-Host "1. 启动 Ubuntu:"
    Write-Host "   wsl"
    Write-Host ""
    Write-Host "2. 在 Ubuntu 中运行配置脚本:"
    Write-Host "   cd /mnt/d/data/PycharmProjects/PythonProject1/scripts"
    Write-Host "   chmod +x wsl2-setup.sh"
    Write-Host "   ./wsl2-setup.sh"
    Write-Host ""
    Write-Host "3. 或者手动克隆项目:"
    Write-Host "   git clone git@github.com:githubstudycloud/gi005.git ~/projects/gi005"
    Write-Host ""
    Write-Host "有用的命令:"
    Write-Host "  wsl --list --verbose          # 查看已安装的发行版"
    Write-Host "  wsl --shutdown                # 关闭 WSL"
    Write-Host "  wsl --set-default Ubuntu-22.04  # 设置默认发行版"
    Write-Host ""
}

# 主函数
function Main {
    Write-Host "======================================"
    Write-Host "  Voice Clone TTS - WSL2 安装脚本"
    Write-Host "======================================"
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
        Write-ColorOutput "Windows 版本不符合要求" -Type "ERROR"
        Read-Host "按 Enter 退出"
        exit 1
    }

    # 检查虚拟化
    if (-not (Test-Virtualization)) {
        Write-ColorOutput "请在 BIOS 中启用虚拟化" -Type "ERROR"
        Read-Host "按 Enter 退出"
        exit 1
    }

    # 检查是否已安装 WSL
    if (Test-WSLInstalled) {
        Write-ColorOutput "WSL 已安装" -Type "INFO"
    } else {
        # 启用 WSL 功能
        if (-not (Enable-WSLFeature)) {
            Read-Host "按 Enter 退出"
            exit 1
        }

        # 启用虚拟机平台
        if (-not (Enable-VirtualMachinePlatform)) {
            Read-Host "按 Enter 退出"
            exit 1
        }

        # 提示重启
        Write-ColorOutput "`n系统需要重启以完成 WSL 安装" -Type "WARN"
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

    # 下载并安装 WSL2 内核更新
    $kernelInstaller = Get-WSL2KernelUpdate
    if ($kernelInstaller) {
        if (-not (Install-WSL2Kernel -InstallerPath $kernelInstaller)) {
            Write-ColorOutput "继续安装可能会失败" -Type "WARN"
        }

        # 删除临时安装文件
        Remove-Item -Path $kernelInstaller -Force -ErrorAction SilentlyContinue
    }

    # 设置 WSL2 为默认
    Set-WSL2Default

    # 安装 Ubuntu
    $confirm = Read-Host "`n是否安装 Ubuntu 22.04? (y/n)"
    if ($confirm -eq "y") {
        Install-Ubuntu
    }

    # 显示已安装的发行版
    Show-WSLDistributions

    # 显示完成信息
    Show-Completion

    Read-Host "`n按 Enter 退出"
}

# 运行主函数
Main
