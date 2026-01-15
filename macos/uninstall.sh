#!/bin/bash
APP_NAME="opencode-activity-monitor"
PLIST_NAME="com.opencode.activity-monitor.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "Uninstalling OpenCode Activity Monitor..."

echo "Stopping if running..."
if [ -f "$PLIST_PATH" ]; then
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
fi

echo "Removing files..."
rm -rf "$HOME/Library/Application Support/$APP_NAME"
rm -f "$PLIST_PATH"
rm -f "$HOME/Library/Logs/opencode-activity-monitor.log"

echo "Uninstalled."
echo ""
echo "Note: Python dependencies (pyobjc, psutil) were not removed."
echo "To remove them: pip3 uninstall -y pyobjc-core pyobjc-framework-Cocoa psutil"
