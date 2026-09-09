# Build and Sign Windows Installer for BusinessApp
# Powered by wokdens.com

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "       Building BusinessApp Standalone & Installer     " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# 1. Check & locate Inno Setup Compiler
$InnoCandidates = @(
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$IsccPath = $null
foreach ($path in $InnoCandidates) {
    if (Test-Path $path) {
        $IsccPath = $path
        break
    }
}

if (-not $IsccPath) {
    $found = Get-Command iscc -ErrorAction SilentlyContinue
    if ($found) { $IsccPath = $found.Source }
}

if (-not $IsccPath) {
    Write-Error "Inno Setup Compiler (ISCC.exe) not found! Please install Inno Setup 6."
    exit 1
}
Write-Host "[1/4] Found Inno Setup Compiler: $IsccPath" -ForegroundColor Green

# 2. Sign main BusinessApp.exe
$MainExe = Join-Path $ProjectDir "dist\BusinessApp\BusinessApp.exe"
if (-not (Test-Path $MainExe)) {
    Write-Error "dist\BusinessApp\BusinessApp.exe not found! Please build PyInstaller package first."
    exit 1
}

Write-Host "[2/4] Signing BusinessApp.exe with Authenticode certificate..." -ForegroundColor Cyan
& (Join-Path $ScriptDir "sign_app.ps1") -FilePath $MainExe

# 3. Compile Inno Setup Installer
$IssFile = Join-Path $ProjectDir "installer\setup_script.iss"
Write-Host "[3/4] Compiling Installer using Inno Setup..." -ForegroundColor Cyan
& $IsccPath $IssFile

$InstallerExe = Join-Path $ProjectDir "dist_installer\BizDabba_Setup_v1.0.exe"
if (-not (Test-Path $InstallerExe)) {
    Write-Error "Failed to generate installer executable at: $InstallerExe"
    exit 1
}
Write-Host "Installer compiled: $InstallerExe" -ForegroundColor Green

# 4. Sign the Installer Executable
Write-Host "[4/4] Digitally Signing Installer Executable..." -ForegroundColor Cyan
& (Join-Path $ScriptDir "sign_app.ps1") -FilePath $InstallerExe

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Green
Write-Host "   BUILD & SIGNING COMPLETE!                           " -ForegroundColor Green
Write-Host "   Installer: dist_installer\BizDabba_Setup_v1.0.exe   " -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green
