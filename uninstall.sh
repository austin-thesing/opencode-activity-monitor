#!/bin/bash
# OpenCode Activity Monitor - Platform Router (Uninstall)
#
# Detects the current platform and runs the appropriate uninstaller.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════╗"
echo "║  OpenCode Activity Monitor - Uninstaller     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected: macOS"
    echo ""
    
    if [ ! -f "$SCRIPT_DIR/macos/uninstall.sh" ]; then
        echo "Error: macos/uninstall.sh not found."
        exit 1
    fi
    
    exec bash "$SCRIPT_DIR/macos/uninstall.sh"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected: Linux"
    echo ""
    
    if [ ! -f "$SCRIPT_DIR/omarchy/uninstall.sh" ]; then
        echo "Error: omarchy/uninstall.sh not found."
        exit 1
    fi
    
    exec bash "$SCRIPT_DIR/omarchy/uninstall.sh"
    
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Detected: Windows"
    echo ""
    echo "Please run the PowerShell uninstaller instead:"
    echo "  powershell -ExecutionPolicy Bypass -File windows/uninstall.ps1"
    exit 1
    
else
    echo "Error: Unsupported platform: $OSTYPE"
    exit 1
fi
