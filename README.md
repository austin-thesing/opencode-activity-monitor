# OpenCode Session Activity Monitor

A transparent, always-on-top, click-through overlay for monitoring OpenCode sessions on Hyprland/Wayland.

## Features

- **Transparent overlay** - Configurable opacity, sits on top of everything
- **Session Monitoring** - Shows active OpenCode sessions, their projects, and status
- **Compact UI** - High-density information display with JetBrains Mono font
- **Selective Click-through** - Window is passthrough except for interactive UI elements
- **Layer-shell** - Proper Wayland overlay using gtk4-layer-shell
- **Real-time updates** - Configurable refresh interval
- **Status indicators** - Green/orange/red based on session activity (active, idle, stale)
- **Easy config** - Well-commented TOML config file

<img width="608" height="324" alt="screenshot-2026-01-14_13-56-29" src="https://github.com/user-attachments/assets/dda429ec-3a35-43ec-b8d8-b19cb728aaa4" />

## Requirements

- Arch Linux with Hyprland (or any wlroots-based compositor)
- Python 3.11+
- GTK4 + gtk4-layer-shell

```bash
sudo pacman -S python-gobject gtk4 gtk4-layer-shell
```

## Installation

```bash
git clone <repo>
cd opencode-activity-monitor
chmod +x install.sh
./install.sh
```

## Usage

```bash
opencode-activity-monitor              # Start overlay
opencode-activity-monitor-toggle       # Toggle click-through mode
```

### Hyprand Keybind

Add to `~/.config/hypr/hyprland.conf`:

```
bind = SUPER SHIFT, Q, exec, opencode-activity-monitor-toggle
```

## Configuration

Edit `~/.config/opencode-activity-monitor/config.toml`:

```toml
# Monitor settings
[monitor]
refresh_interval_ms = 5000

# Appearance
[appearance]
background_opacity = 0.55
text_opacity = 0.85
width = 210
corner_radius = 10

# Position
[position]
anchor = "top-left"
margin_top = 10
margin_left = 10

# Behavior
[behavior]
click_through = true

# Colors
[colors]
ok = "#4caf50"        # Green - active
warning = "#ff9800"   # Orange - idle
critical = "#f44336"  # Red - stale
provider = "#64b5f6"  # Header color
background = "10, 12, 16"
```

After editing, restart: `pkill -f opencode-activity-monitor && opencode-activity-monitor &`

## Files

```
~/.config/opencode-activity-monitor/config.toml   # Configuration
~/.local/share/opencode-activity-monitor/main.py  # Application
~/.local/bin/opencode-activity-monitor            # Launcher script
~/.local/bin/opencode-activity-monitor-toggle     # Toggle script
```

## Manual Run

```bash
LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so python3 src/main.py
```

## **Disclaimer:** This is a community project for OpenCode and is not maintained by the OpenCode creators.

## License

MIT
