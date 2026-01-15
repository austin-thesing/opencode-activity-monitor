#!/bin/bash
# OpenCode Activity Monitor - Platform Router
#
# Detects the current platform and runs the appropriate installer.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════╗"
echo "║  OpenCode Activity Monitor - Installer       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected: macOS"
    echo ""
    
    if [ ! -f "$SCRIPT_DIR/macos/install.sh" ]; then
        echo "Error: macos/install.sh not found."
        echo "Please run from the repository root directory."
        exit 1
    fi
    
    exec bash "$SCRIPT_DIR/macos/install.sh"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected: Linux"
    echo ""
    
    if [ ! -f "$SCRIPT_DIR/omarchy/install.sh" ]; then
        echo "Error: omarchy/install.sh not found."
        echo "Please run from the repository root directory."
        exit 1
    fi
    
    exec bash "$SCRIPT_DIR/omarchy/install.sh"
    
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Detected: Windows"
    echo ""
    echo "Please run the PowerShell installer instead:"
    echo "  powershell -ExecutionPolicy Bypass -File windows/install.ps1"
    echo ""
    echo "Or with startup option:"
    echo "  powershell -ExecutionPolicy Bypass -File windows/install.ps1 -AddToStartup"
    exit 1
    
else
    echo "Error: Unsupported platform: $OSTYPE"
    echo ""
    echo "Supported platforms:"
    echo "  - macOS (darwin)"
    echo "  - Linux (Hyprland/Wayland)"
    echo "  - Windows (use PowerShell installer)"
    exit 1
fi
