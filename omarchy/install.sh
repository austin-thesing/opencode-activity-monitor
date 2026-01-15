#!/bin/bash
# OpenCode Activity Monitor - Linux/Hyprland Installer
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

INSTALL_DIR="$HOME/.local/share/opencode-activity-monitor"
CONFIG_DIR="$HOME/.config/opencode-activity-monitor"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "Installing OpenCode Activity Monitor for Linux/Hyprland..."
echo ""

# Check dependencies
missing=""
/usr/bin/python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null || missing="$missing python-gobject gtk4"
/usr/bin/python3 -c "import gi; gi.require_version('Gtk4LayerShell', '1.0')" 2>/dev/null || missing="$missing gtk4-layer-shell"
/usr/bin/python3 -c "import psutil" 2>/dev/null || missing="$missing python-psutil"

if [ -n "$missing" ]; then
    echo "Missing dependencies:$missing"
    echo "Install: sudo pacman -S$missing"
    exit 1
fi

echo "Creating directories..."
mkdir -p "$INSTALL_DIR/src"
mkdir -p "$INSTALL_DIR/omarchy"
mkdir -p "$CONFIG_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$AUTOSTART_DIR"

echo "Copying shared source files..."
cp "$REPO_ROOT/src/__init__.py" "$INSTALL_DIR/src/"
cp "$REPO_ROOT/src/config.py" "$INSTALL_DIR/src/"
cp "$REPO_ROOT/src/opencode_data.py" "$INSTALL_DIR/src/"
cp "$REPO_ROOT/src/platform.py" "$INSTALL_DIR/src/"

echo "Copying omarchy (Linux) files..."
cp "$REPO_ROOT/omarchy/__init__.py" "$INSTALL_DIR/omarchy/"
cp "$REPO_ROOT/omarchy/main.py" "$INSTALL_DIR/omarchy/"
cp "$REPO_ROOT/omarchy/overlay.py" "$INSTALL_DIR/omarchy/"
cp "$REPO_ROOT/omarchy/ui.py" "$INSTALL_DIR/omarchy/"
cp "$REPO_ROOT/omarchy/tray.py" "$INSTALL_DIR/omarchy/"
cp "$REPO_ROOT/omarchy/tray_manager.py" "$INSTALL_DIR/omarchy/"

if [ ! -f "$CONFIG_DIR/config.toml" ]; then
    cp "$REPO_ROOT/config.toml" "$CONFIG_DIR/config.toml"
    echo "Created config: $CONFIG_DIR/config.toml"
else
    echo "Config exists: $CONFIG_DIR/config.toml (not overwritten)"
fi

echo "Creating launcher scripts..."
cat > "$BIN_DIR/opencode-activity-monitor" << 'LAUNCHER'
#!/bin/bash
export LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so
cd "${HOME}/.local/share/opencode-activity-monitor"
exec /usr/bin/python3 -m omarchy.main "$@"
LAUNCHER
chmod +x "$BIN_DIR/opencode-activity-monitor"

cat > "$BIN_DIR/opencode-activity-monitor-toggle" << 'TOGGLE'
#!/bin/bash
PID=$(pgrep -f "omarchy.main" | head -1)
if [ -n "$PID" ]; then
    kill -USR1 "$PID"
    echo "Toggled click-through mode"
else
    echo "opencode-activity-monitor not running"
fi
TOGGLE
chmod +x "$BIN_DIR/opencode-activity-monitor-toggle"

cat > "$BIN_DIR/opencode-activity-monitor-visibility" << 'VIS'
#!/bin/bash
PID=$(pgrep -f "omarchy.main" | head -1)
if [ -n "$PID" ]; then
    kill -USR2 "$PID"
    echo "Toggled visibility"
else
    echo "opencode-activity-monitor not running"
fi
VIS
chmod +x "$BIN_DIR/opencode-activity-monitor-visibility"

cat > "$DESKTOP_DIR/opencode-activity-monitor.desktop" << 'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=OpenCode Activity Monitor
Comment=Transparent OpenCode session activity overlay for Hyprland
Exec=opencode-activity-monitor
Icon=utilities-system-monitor
Terminal=false
Categories=Utility;System;
DESKTOP

cp "$DESKTOP_DIR/opencode-activity-monitor.desktop" "$AUTOSTART_DIR/"

if [ -f "$REPO_ROOT/opencode-activity-monitor.service" ]; then
    mkdir -p "$HOME/.config/systemd/user"
    cp "$REPO_ROOT/opencode-activity-monitor.service" "$HOME/.config/systemd/user/"
    systemctl --user daemon-reload
    
    echo ""
    echo "Starting systemd service..."
    systemctl --user enable --now opencode-activity-monitor.service
fi

echo ""
echo "Installation complete!"
echo ""
echo "Commands:"
echo "  opencode-activity-monitor           - Start the overlay"
echo "  opencode-activity-monitor-toggle    - Toggle click-through mode"
echo "  opencode-activity-monitor-visibility - Toggle visibility"
echo ""
echo "Config file: $CONFIG_DIR/config.toml"
echo ""
echo "Add keybind to ~/.config/hypr/hyprland.conf:"
echo '  bind = SUPER SHIFT, Q, exec, opencode-activity-monitor-toggle'
echo ""
