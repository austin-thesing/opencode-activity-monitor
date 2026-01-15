# OpenCode Activity Monitor - Windows Installer
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [switch]$AddToStartup,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Configuration
$AppName = "opencode-activity-monitor"
$DisplayName = "OpenCode Activity Monitor"

# Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$AppDataDir = Join-Path $env:APPDATA $AppName
$LocalAppDataDir = Join-Path $env:LOCALAPPDATA $AppName
$StartupDir = [Environment]::GetFolderPath("Startup")

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  $DisplayName - Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "  Please install Python 3.9+ and add it to PATH" -ForegroundColor Red
    exit 1
}

# Check if already installed
if ((Test-Path $LocalAppDataDir) -and -not $Force) {
    Write-Host ""
    Write-Host "WARNING: $DisplayName appears to be already installed." -ForegroundColor Yellow
    Write-Host "  Install location: $LocalAppDataDir" -ForegroundColor Yellow
    $response = Read-Host "Do you want to reinstall? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Installation cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Create directories
Write-Host ""
Write-Host "Creating directories..." -ForegroundColor Yellow

if (-not (Test-Path $LocalAppDataDir)) {
    New-Item -ItemType Directory -Path $LocalAppDataDir -Force | Out-Null
    Write-Host "  Created: $LocalAppDataDir" -ForegroundColor Green
}

if (-not (Test-Path $AppDataDir)) {
    New-Item -ItemType Directory -Path $AppDataDir -Force | Out-Null
    Write-Host "  Created: $AppDataDir" -ForegroundColor Green
}

# Copy application files
Write-Host ""
Write-Host "Copying application files..." -ForegroundColor Yellow

# Copy src/ directory
$srcSource = Join-Path $RepoRoot "src"
$srcDest = Join-Path $LocalAppDataDir "src"
if (Test-Path $srcDest) { Remove-Item -Recurse -Force $srcDest }
Copy-Item -Recurse $srcSource $srcDest
Write-Host "  Copied: src/" -ForegroundColor Green

# Copy windows/ directory
$winSource = Join-Path $RepoRoot "windows"
$winDest = Join-Path $LocalAppDataDir "windows"
if (Test-Path $winDest) { Remove-Item -Recurse -Force $winDest }
Copy-Item -Recurse $winSource $winDest
Write-Host "  Copied: windows/" -ForegroundColor Green

# Copy config.toml template if not exists
$configSource = Join-Path $RepoRoot "config.toml"
$configDest = Join-Path $AppDataDir "config.toml"
if (-not (Test-Path $configDest)) {
    Copy-Item $configSource $configDest
    Write-Host "  Copied: config.toml (to $AppDataDir)" -ForegroundColor Green
} else {
    Write-Host "  Skipped: config.toml (already exists)" -ForegroundColor Yellow
}

# Install Python dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
$requirementsPath = Join-Path $RepoRoot "requirements.txt"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r $requirementsPath
Write-Host "  Dependencies installed" -ForegroundColor Green

# Create launcher batch file
Write-Host ""
Write-Host "Creating launcher..." -ForegroundColor Yellow
$launcherPath = Join-Path $LocalAppDataDir "opencode-monitor.bat"
$launcherContent = @"
@echo off
cd /d "$LocalAppDataDir"
pythonw -m windows.main
"@
Set-Content -Path $launcherPath -Value $launcherContent
Write-Host "  Created: opencode-monitor.bat" -ForegroundColor Green

# Create VBS launcher (for silent startup without console window)
$vbsLauncherPath = Join-Path $LocalAppDataDir "opencode-monitor.vbs"
$vbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "$LocalAppDataDir"
WshShell.Run "pythonw -m windows.main", 0, False
"@
Set-Content -Path $vbsLauncherPath -Value $vbsContent
Write-Host "  Created: opencode-monitor.vbs" -ForegroundColor Green

# Add to startup if requested
if ($AddToStartup) {
    Write-Host ""
    Write-Host "Adding to startup..." -ForegroundColor Yellow
    $shortcutPath = Join-Path $StartupDir "OpenCode Monitor.lnk"
    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcut = $WScriptShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "wscript.exe"
    $shortcut.Arguments = "`"$vbsLauncherPath`""
    $shortcut.WorkingDirectory = $LocalAppDataDir
    $shortcut.Description = $DisplayName
    $shortcut.Save()
    Write-Host "  Added to: $StartupDir" -ForegroundColor Green
}

# Done
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run manually:" -ForegroundColor White
Write-Host "  $launcherPath" -ForegroundColor Gray
Write-Host ""
Write-Host "Or from the install directory:" -ForegroundColor White
Write-Host "  cd $LocalAppDataDir" -ForegroundColor Gray
Write-Host "  python -m windows.main" -ForegroundColor Gray
Write-Host ""
Write-Host "Configuration file:" -ForegroundColor White
Write-Host "  $configDest" -ForegroundColor Gray
Write-Host ""

if (-not $AddToStartup) {
    Write-Host "To add to Windows startup, run:" -ForegroundColor White
    Write-Host "  .\install.ps1 -AddToStartup" -ForegroundColor Gray
    Write-Host ""
}
