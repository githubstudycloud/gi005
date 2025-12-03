# WSL2 Installation Script - Install to D:\wsl\ubuntu22
# Run as Administrator

$InstallPath = "D:\wsl\ubuntu22"
$DistroName = "Ubuntu-22.04"
$TempDir = "$env:TEMP\wsl-install"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  WSL2 Ubuntu 22.04 -> D:\wsl\ubuntu22" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check Admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] Please run as Administrator!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Windows version
$build = [System.Environment]::OSVersion.Version.Build
Write-Host "[INFO] Windows Build: $build" -ForegroundColor Green
if ($build -lt 19041) {
    Write-Host "[ERROR] Windows 10 Build 19041+ required" -ForegroundColor Red
    exit 1
}

# Check WSL features
Write-Host "[INFO] Checking WSL features..." -ForegroundColor Green
$wsl = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
$vmp = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform

if ($wsl.State -ne "Enabled" -or $vmp.State -ne "Enabled") {
    Write-Host "[INFO] Enabling WSL features..." -ForegroundColor Yellow
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    Write-Host "[WARN] Please restart and run this script again!" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 0
}

Write-Host "[OK] WSL features enabled" -ForegroundColor Green

# Create temp dir
if (-not (Test-Path $TempDir)) {
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
}

# Download WSL2 kernel update
$kernelUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$kernelPath = "$TempDir\wsl_update_x64.msi"

if (-not (Test-Path $kernelPath)) {
    Write-Host "[INFO] Downloading WSL2 kernel update..." -ForegroundColor Green
    try {
        Invoke-WebRequest -Uri $kernelUrl -OutFile $kernelPath -UseBasicParsing
        Write-Host "[OK] Download complete" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Download failed, please download manually: https://aka.ms/wsl2kernel" -ForegroundColor Yellow
    }
}

if (Test-Path $kernelPath) {
    Write-Host "[INFO] Installing WSL2 kernel update..." -ForegroundColor Green
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$kernelPath`" /quiet /norestart" -Wait
}

# Set WSL2 as default
wsl --set-default-version 2

# Download Ubuntu
$ubuntuUrl = "https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-wsl.rootfs.tar.gz"
$ubuntuPath = "$TempDir\ubuntu-22.04.tar.gz"

if (-not (Test-Path $ubuntuPath)) {
    Write-Host "[INFO] Downloading Ubuntu 22.04 (~500MB)..." -ForegroundColor Green
    Write-Host "[INFO] This may take a while..." -ForegroundColor Yellow
    try {
        Start-BitsTransfer -Source $ubuntuUrl -Destination $ubuntuPath -DisplayName "Downloading Ubuntu"
        Write-Host "[OK] Download complete" -ForegroundColor Green
    } catch {
        Write-Host "[INFO] Trying alternative download..." -ForegroundColor Yellow
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $ubuntuUrl -OutFile $ubuntuPath -UseBasicParsing
    }
}

if (-not (Test-Path $ubuntuPath)) {
    Write-Host "[ERROR] Ubuntu download failed" -ForegroundColor Red
    Write-Host "Please download manually: $ubuntuUrl" -ForegroundColor Yellow
    Write-Host "Save to: $ubuntuPath" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create install directory
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}

# Check existing distro
$existing = wsl --list --quiet 2>$null | Where-Object { $_ -match "Ubuntu" }
if ($existing) {
    Write-Host "[WARN] Existing Ubuntu found: $existing" -ForegroundColor Yellow
    $remove = Read-Host "Unregister it first? (y/n)"
    if ($remove -eq "y") {
        wsl --unregister $DistroName
    }
}

# Import Ubuntu
Write-Host "[INFO] Importing Ubuntu to $InstallPath..." -ForegroundColor Green
Write-Host "[INFO] This may take a few minutes..." -ForegroundColor Yellow
wsl --import $DistroName $InstallPath $ubuntuPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Ubuntu installed successfully!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Installation failed" -ForegroundColor Red
    exit 1
}

# Verify
Write-Host ""
Write-Host "[INFO] Installed distributions:" -ForegroundColor Green
wsl --list --verbose

Write-Host ""
Write-Host "[INFO] Testing Ubuntu..." -ForegroundColor Green
wsl -d $DistroName -- uname -a

# Create user
Write-Host ""
$createUser = Read-Host "Create a normal user? (y/n)"
if ($createUser -eq "y") {
    $username = Read-Host "Enter username"
    if ($username) {
        wsl -d $DistroName -- useradd -m -s /bin/bash $username
        wsl -d $DistroName -- usermod -aG sudo $username
        Write-Host "[INFO] Setting password for $username..." -ForegroundColor Green
        wsl -d $DistroName -- passwd $username

        # Set default user
        $wslConf = "[user]`ndefault=$username`n[boot]`nsystemd=true"
        wsl -d $DistroName -- bash -c "echo '$wslConf' > /etc/wsl.conf"

        Write-Host "[OK] User $username created" -ForegroundColor Green
        wsl --shutdown
    }
}

# Done
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Location: $InstallPath" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start WSL: wsl" -ForegroundColor White
Write-Host "  2. Run setup script:" -ForegroundColor White
Write-Host "     cd /mnt/d/data/PycharmProjects/PythonProject1/scripts" -ForegroundColor White
Write-Host "     chmod +x wsl2-setup-cuda-pytorch.sh" -ForegroundColor White
Write-Host "     ./wsl2-setup-cuda-pytorch.sh" -ForegroundColor White
Write-Host ""

# Cleanup
$cleanup = Read-Host "Delete temp files? (y/n)"
if ($cleanup -eq "y") {
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Temp files deleted" -ForegroundColor Green
}

Read-Host "Press Enter to exit"
