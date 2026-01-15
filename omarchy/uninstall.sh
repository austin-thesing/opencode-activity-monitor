#!/bin/bash
# OpenCode Activity Monitor - Linux/Hyprland Uninstaller

echo "Uninstalling OpenCode Activity Monitor (Linux)..."

# Stop service if running
if systemctl --user is-active opencode-activity-monitor.service &>/dev/null; then
    echo "Stopping service..."
    systemctl --user stop opencode-activity-monitor.service
    systemctl --user disable opencode-activity-monitor.service
fi

# Kill any running processes
pkill -f "omarchy.main" 2>/dev/null || true
pkill -f "opencode-activity-monitor" 2>/dev/null || true

echo "Removing files..."
rm -rf "$HOME/.local/share/opencode-activity-monitor"
rm -f "$HOME/.local/bin/opencode-activity-monitor"
rm -f "$HOME/.local/bin/opencode-activity-monitor-toggle"
rm -f "$HOME/.local/bin/opencode-activity-monitor-visibility"
rm -f "$HOME/.local/share/applications/opencode-activity-monitor.desktop"
rm -f "$HOME/.config/autostart/opencode-activity-monitor.desktop"
rm -f "$HOME/.config/systemd/user/opencode-activity-monitor.service"

echo ""
echo "Uninstalled."
echo ""
echo "Note: Config file preserved at ~/.config/opencode-activity-monitor/config.toml"
echo "To remove config: rm -rf ~/.config/opencode-activity-monitor"
