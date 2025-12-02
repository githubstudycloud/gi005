# WSL2 迁移到 D 盘脚本
# Voice Clone TTS 项目
# 版本: 1.0.0

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

# 配置
$DistroName = "Ubuntu-22.04"
$BackupPath = "D:\WSL2\Backup"
$InstallPath = "D:\WSL2\Distros\Ubuntu-22.04"

Write-Host "======================================"
Write-Host "  WSL2 迁移到 D 盘"
Write-Host "======================================"
Write-Host ""

# 检查管理员权限
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-ColorOutput "请以管理员身份运行此脚本！" -Type "ERROR"
    exit 1
}

# 显示当前 WSL 发行版
Write-ColorOutput "当前已安装的 WSL 发行版:" -Type "INFO"
wsl --list --verbose
Write-Host ""

# 确认操作
Write-ColorOutput "此脚本将:" -Type "WARN"
Write-Host "1. 导出 $DistroName 到 $BackupPath"
Write-Host "2. 注销当前的 $DistroName"
Write-Host "3. 从备份导入到 $InstallPath"
Write-Host ""
$confirm = Read-Host "是否继续? (y/n)"

if ($confirm -ne "y") {
    Write-ColorOutput "操作已取消" -Type "INFO"
    exit 0
}

# 创建备份目录
Write-ColorOutput "创建备份目录..." -Type "INFO"
if (-not (Test-Path $BackupPath)) {
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
}

# 关闭 WSL
Write-ColorOutput "关闭 WSL..." -Type "INFO"
wsl --shutdown
Start-Sleep -Seconds 3

# 导出发行版
Write-ColorOutput "导出 $DistroName（这可能需要几分钟）..." -Type "INFO"
$backupFile = Join-Path $BackupPath "$DistroName.tar"

try {
    wsl --export $DistroName $backupFile
    Write-ColorOutput "导出完成: $backupFile" -Type "SUCCESS"
} catch {
    Write-ColorOutput "导出失败: $_" -Type "ERROR"
    exit 1
}

# 获取导出文件大小
$fileSize = (Get-Item $backupFile).Length / 1GB
Write-ColorOutput "备份文件大小: $([math]::Round($fileSize, 2)) GB" -Type "INFO"

# 注销当前发行版
Write-ColorOutput "注销当前的 $DistroName..." -Type "WARN"
$confirm2 = Read-Host "确认注销? (y/n)"

if ($confirm2 -ne "y") {
    Write-ColorOutput "操作已取消，备份文件保留在: $backupFile" -Type "INFO"
    exit 0
}

try {
    wsl --unregister $DistroName
    Write-ColorOutput "$DistroName 已注销" -Type "SUCCESS"
} catch {
    Write-ColorOutput "注销失败: $_" -Type "ERROR"
    exit 1
}

# 创建安装目录
Write-ColorOutput "创建安装目录..." -Type "INFO"
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}

# 导入到新位置
Write-ColorOutput "导入 $DistroName 到 $InstallPath（这可能需要几分钟）..." -Type "INFO"

try {
    wsl --import $DistroName $InstallPath $backupFile
    Write-ColorOutput "导入完成" -Type "SUCCESS"
} catch {
    Write-ColorOutput "导入失败: $_" -Type "ERROR"
    Write-ColorOutput "可以从备份恢复: wsl --import $DistroName C:\WSL2 $backupFile" -Type "WARN"
    exit 1
}

# 设置默认用户（如果不是 root）
Write-ColorOutput "设置默认用户..." -Type "INFO"
$username = Read-Host "输入您的 Linux 用户名（如果是 root 请留空）"

if ($username) {
    # 创建配置文件
    $wslConfigPath = Join-Path $InstallPath "wsl.conf"
    @"
[user]
default=$username
"@ | Out-File -FilePath $wslConfigPath -Encoding utf8

    Write-ColorOutput "默认用户已设置为: $username" -Type "SUCCESS"
}

# 验证安装
Write-ColorOutput "`n验证安装..." -Type "INFO"
wsl --list --verbose
Write-Host ""

# 测试启动
Write-ColorOutput "测试启动 WSL..." -Type "INFO"
wsl -d $DistroName -- uname -a

if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput "WSL 启动成功！" -Type "SUCCESS"
} else {
    Write-ColorOutput "WSL 启动失败" -Type "ERROR"
}

# 显示磁盘使用情况
Write-ColorOutput "`nD 盘使用情况:" -Type "INFO"
Get-PSDrive D | Select-Object @{Name="Drive";Expression={$_.Name}}, @{Name="Used(GB)";Expression={[math]::Round($_.Used/1GB,2)}}, @{Name="Free(GB)";Expression={[math]::Round($_.Free/1GB,2)}}, @{Name="Total(GB)";Expression={[math]::Round(($_.Used+$_.Free)/1GB,2)}}

# 完成信息
Write-Host "`n======================================"
Write-ColorOutput "迁移完成！" -Type "SUCCESS"
Write-Host "======================================"
Write-Host ""
Write-Host "新位置:"
Write-Host "  WSL 安装路径: $InstallPath"
Write-Host "  备份文件: $backupFile"
Write-Host ""
Write-Host "启动 WSL:"
Write-Host "  wsl -d $DistroName"
Write-Host "  或直接: wsl"
Write-Host ""
Write-Host "项目位置（在 WSL 内）:"
Write-Host "  ~/projects/gi005"
Write-Host ""
Write-Host "如果一切正常，可以删除备份文件:"
Write-Host "  Remove-Item '$backupFile'"
Write-Host ""

# 是否删除备份
$deleteBackup = Read-Host "是否删除备份文件? (y/n)"
if ($deleteBackup -eq "y") {
    Remove-Item $backupFile -Force
    Write-ColorOutput "备份文件已删除" -Type "INFO"
} else {
    Write-ColorOutput "备份文件保留在: $backupFile" -Type "INFO"
}

Read-Host "`n按 Enter 退出"
