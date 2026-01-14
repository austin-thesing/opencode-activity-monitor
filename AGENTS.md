# AGENTS.md - OpenCode Session Activity Monitor Navigation Guide

## Overview

Transparent GTK4 overlay for monitoring OpenCode session activity on Hyprland/Wayland. Python 3.11+, uses gtk4-layer-shell for Wayland integration.

**Key characteristics:**
- Single-language Python project
- Configuration via TOML
- Signal-based inter-process communication (USR1/USR2)
- No package manager or test suite

## Project Structure

```
opencode-activity-monitor/
├── src/
│   ├── main.py            # Application entry point, signal handlers
│   ├── overlay.py         # GTK4 overlay window, UI refresh logic
│   ├── ui.py              # CSS generation and widget styling
│   ├── config.py          # TOML config loading with defaults
│   ├── opencode_data.py   # OpenCode session data fetching
│   ├── tray_manager.py    # Tray process launcher
│   ├── tray.py            # System tray icon (GTK3, AyatanaAppIndicator)
│   └── __init__.py
├── config.toml            # User configuration template
├── install.sh             # Installation script
└── README.md              # User documentation
```

## Development Workflow

### Running from Source

```bash
# Manual execution (requires gtk4-layer-shell)
LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so python3 src/main.py

# Toggle click-through mode (sends SIGUSR1)
kill -USR1 $(pgrep -f "src.main")

# Toggle visibility (sends SIGUSR2)
kill -USR2 $(pgrep -f "src.main")
```

### Installation

```bash
./install.sh  # Copies to ~/.local/share/opencode-activity-monitor and sets up PATH
```

**Install locations:**
- App: `~/.local/share/opencode-activity-monitor/`
- Config: `~/.config/opencode-activity-monitor/config.toml`
- Binaries: `~/.local/bin/opencode-activity-monitor`, `opencode-activity-monitor-toggle`, `opencode-activity-monitor-visibility`
- Systemd service: `~/.config/systemd/user/opencode-activity-monitor.service

### Runtime Control

The application responds to UNIX signals:
- `SIGUSR1` → Toggle click-through mode
- `SIGUSR2` → Show/hide overlay
- `SIGTERM` → Graceful shutdown

## Architecture

### Configuration Loading (@src/config.py)

- Uses `tomllib` (Python 3.11+ standard library)
- Search order: repo root `config.toml` → `src/config.toml`
- Deep merge: user config overrides `DEFAULT_CONFIG` dict
- Exported as `CONFIG` singleton

### Session Data Fetching (@src/opencode_data.py)

- Scans `/proc` for running `opencode` processes via `pgrep`
- Matches processes to session metadata from `opencode session list --format json`
- Key dataclass: `Session` (id, title, project, path, status, last_active_fmt)
- Process filtering: excludes helper processes (run, x, acp, serve, extension-host, completion)
- Matching priority: CLI session ID → CWD (most recent for directory)

### Main Application (@src/main.py)

**Data flow:**
1. Spawn tray process (monitor parent PID)
2. Initialize overlay window with layer shell
3. Refresh session data every `CONFIG["monitor"]["refresh_interval_ms"]`
4. Update GTK widgets via `GLib.idle_add()`

**Signal handlers:**
- `SIGUSR1` → Toggle click-through mode
- `SIGUSR2` → Show/hide overlay
- `SIGTERM`/`SIGINT` → Graceful shutdown

**Wayland integration:**
- `Gtk4LayerShell.LayerShell` for layer surface
- Dynamic input region: calculate bounds of interactive widgets only
- Click-through mode: empty input region = full passthrough

### UI Components (@src/ui.py)

- `get_css()`: Generates CSS from config (colors, opacity, spacing)
- CSS classes: `.overlay-main`, `.provider-name`, `.session-project`, `.session-status`
- Dynamic widget styling based on session status (working/idle)

### System Tray (@src/tray.py)

- Runs as separate process (spawned by main.py)
- GTK3 + AyatanaAppIndicator3 (NOT GTK4)
- Parent process monitoring: exits if main.py dies
- Menu items: Show/Hide, Toggle Click-through, Exit

## Code Style Guidelines

### Python Conventions

- **Type hints:** Required for function signatures and dataclass fields
- **Dataclasses:** Use for structured data (Session)
- **Imports:** Group standard library, third-party (gi), local modules
- **String formatting:** f-strings preferred
- **Error handling:** Print to stderr, continue gracefully where possible

### GTK4 Patterns

```python
# Layer shell initialization
LayerShell.init_for_window(window)
LayerShell.set_layer(window, LayerShell.Layer.OVERLAY)
LayerShell.set_anchor(window, edge, True)

# Dynamic input region (selective click-through)
rect = Gdk.Rectangle()
rect.x, rect.y, rect.width, rect.height = widget_bounds
window.set_input_region([rect])

# Thread-safe UI updates
GLib.idle_add(callback, *args)
```

### Configuration Access

```python
from src.config import CONFIG

interval = CONFIG["monitor"]["refresh_interval_ms"]
opacity = CONFIG["appearance"]["background_opacity"]
anchor = CONFIG["position"]["anchor"]
```

## Systemd Service

```bash
# Enable and start the service
systemctl --user enable --now opencode-activity-monitor.service

# Check status
systemctl --user status opencode-activity-monitor.service

# View logs
journalctl --user -u opencode-activity-monitor.service -f
```

## Common Tasks

### Add New Configuration Option

1. Add key to `DEFAULT_CONFIG` in `src/config.py`
2. Add documentation comment to `config.toml`
3. Use via `CONFIG["section"]["key"]`

### Modify Session Data Display

Edit `Session` dataclass in `src/opencode_data.py` or `make_session_row()` in `src/ui.py` to change display format.

### Change Widget Styling

Modify `get_css()` in `src/ui.py` to add new CSS rules or adjust existing ones.

### Debugging

Run with verbose output: main.py prints to stdout/stderr. Check logs via:
```bash
opencode-activity-monitor 2>&1 | tee debug.log
```

## Dependencies

**System packages (Arch/pacman):**
- `python-gobject` (PyGObject bindings)
- `gtk4` (GUI toolkit)
- `gtk4-layer-shell` (Wayland layer shell)
- `libayatana-appindicator` (for tray icon)

**Python standard library only** - no pip packages required.

## Platform Constraints

- **Hyprland/Wayland only** (not X11-compatible)
- Requires wlroots-based compositor
- Uses Python 3.11+ `tomllib` module
