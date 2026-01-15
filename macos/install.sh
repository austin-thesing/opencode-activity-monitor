#!/bin/bash
# OpenCode Activity Monitor - macOS Installer
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

APP_NAME="opencode-activity-monitor"
INSTALL_DIR="$HOME/Library/Application Support/$APP_NAME"
CONFIG_DIR="$INSTALL_DIR"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.opencode.activity-monitor.plist"
PLIST_PATH="$LAUNCH_AGENT_DIR/$PLIST_NAME"

echo "Installing OpenCode Activity Monitor for macOS..."
echo ""

echo "Installing Python dependencies..."
pip3 install --user -r "$REPO_ROOT/requirements.txt"

echo ""
echo "Creating install directories..."
mkdir -p "$INSTALL_DIR/src"
mkdir -p "$INSTALL_DIR/macos"
mkdir -p "$LAUNCH_AGENT_DIR"

echo "Copying shared source files..."
cp "$REPO_ROOT/src/__init__.py" "$INSTALL_DIR/src/"
cp "$REPO_ROOT/src/config.py" "$INSTALL_DIR/src/"
cp "$REPO_ROOT/src/opencode_data.py" "$INSTALL_DIR/src/"
cp "$REPO_ROOT/src/platform.py" "$INSTALL_DIR/src/"

echo "Copying macOS application files..."
cp "$REPO_ROOT/macos/__init__.py" "$INSTALL_DIR/macos/"
cp "$REPO_ROOT/macos/main.py" "$INSTALL_DIR/macos/"
cp "$REPO_ROOT/macos/overlay.py" "$INSTALL_DIR/macos/"
cp "$REPO_ROOT/macos/menu_bar.py" "$INSTALL_DIR/macos/"

if [ -f "$REPO_ROOT/config.toml" ]; then
    mkdir -p "$CONFIG_DIR"
    cp "$REPO_ROOT/config.toml" "$CONFIG_DIR/config.toml"
fi

echo ""
echo "Creating launcher script..."
cat > "$INSTALL_DIR/launcher.sh" << 'EOF'
#!/bin/bash
# OpenCode Activity Monitor - Launcher Script
# This script is called by the LaunchAgent to start the application.

# Navigate to the application directory
cd "$HOME/Library/Application Support/opencode-activity-monitor"

# Ensure the local bin is in PATH for opencode CLI access
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

# Run the application using the system Python
exec /usr/bin/python3 -m macos.main
EOF
chmod +x "$INSTALL_DIR/launcher.sh"

echo ""
echo "Creating LaunchAgent for auto-start at login..."
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.opencode.activity-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HOME/Library/Application Support/opencode-activity-monitor/launcher.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/opencode-activity-monitor.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/opencode-activity-monitor.log</string>
</dict>
</plist>
EOF

echo ""
echo "Installation complete!"
echo ""
echo "To start now:  launchctl load \"$PLIST_PATH\""
echo "To stop:       launchctl unload \"$PLIST_PATH\""
echo "Logs:          \"$HOME/Library/Logs/opencode-activity-monitor.log\""
echo ""
echo "The app will automatically start at login."
echo ""
read -p "Start the app now? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    launchctl load "$PLIST_PATH"
    echo "App started. Look for the terminal icon in the menu bar."
fi
