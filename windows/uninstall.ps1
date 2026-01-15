# OpenCode Activity Monitor - Windows Uninstaller
# Run with: powershell -ExecutionPolicy Bypass -File uninstall.ps1

param(
    [switch]$KeepConfig,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Configuration
$AppName = "opencode-activity-monitor"
$DisplayName = "OpenCode Activity Monitor"

# Paths
$AppDataDir = Join-Path $env:APPDATA $AppName
$LocalAppDataDir = Join-Path $env:LOCALAPPDATA $AppName
$StartupDir = [Environment]::GetFolderPath("Startup")
$StartupShortcut = Join-Path $StartupDir "OpenCode Monitor.lnk"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  $DisplayName - Uninstaller" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if installed
if (-not (Test-Path $LocalAppDataDir)) {
    Write-Host "WARNING: $DisplayName does not appear to be installed." -ForegroundColor Yellow
    Write-Host "  Expected location: $LocalAppDataDir" -ForegroundColor Yellow
    exit 0
}

# Confirm uninstallation
if (-not $Force) {
    Write-Host "This will remove $DisplayName from your system." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The following will be removed:" -ForegroundColor White
    Write-Host "  - Application files: $LocalAppDataDir" -ForegroundColor Gray
    if (-not $KeepConfig) {
        Write-Host "  - Configuration: $AppDataDir" -ForegroundColor Gray
    }
    if (Test-Path $StartupShortcut) {
        Write-Host "  - Startup shortcut: $StartupShortcut" -ForegroundColor Gray
    }
    Write-Host ""
    $response = Read-Host "Are you sure you want to uninstall? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Uninstallation cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Stop running instances
Write-Host ""
Write-Host "Stopping running instances..." -ForegroundColor Yellow
$processes = Get-Process -Name "python*", "pythonw*" -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like "*windows.main*" -or $_.CommandLine -like "*opencode*" }
if ($processes) {
    $processes | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  Stopped running processes" -ForegroundColor Green
} else {
    Write-Host "  No running instances found" -ForegroundColor Gray
}

# Remove startup shortcut
if (Test-Path $StartupShortcut) {
    Write-Host ""
    Write-Host "Removing startup shortcut..." -ForegroundColor Yellow
    Remove-Item -Force $StartupShortcut
    Write-Host "  Removed: $StartupShortcut" -ForegroundColor Green
}

# Remove application files
Write-Host ""
Write-Host "Removing application files..." -ForegroundColor Yellow
if (Test-Path $LocalAppDataDir) {
    Remove-Item -Recurse -Force $LocalAppDataDir
    Write-Host "  Removed: $LocalAppDataDir" -ForegroundColor Green
}

# Remove configuration
if (-not $KeepConfig) {
    Write-Host ""
    Write-Host "Removing configuration..." -ForegroundColor Yellow
    if (Test-Path $AppDataDir) {
        Remove-Item -Recurse -Force $AppDataDir
        Write-Host "  Removed: $AppDataDir" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "Keeping configuration at: $AppDataDir" -ForegroundColor Yellow
}

# Done
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Uninstallation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($KeepConfig) {
    Write-Host "Configuration was preserved at:" -ForegroundColor White
    Write-Host "  $AppDataDir" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To remove it later, run:" -ForegroundColor White
    Write-Host "  Remove-Item -Recurse `"$AppDataDir`"" -ForegroundColor Gray
    Write-Host ""
}
