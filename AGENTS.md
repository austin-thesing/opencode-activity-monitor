# AGENTS.md - OpenCode Session Activity Monitor Navigation Guide

## Overview

Cross-platform overlay for monitoring OpenCode session activity. Supports **macOS** (menu bar app) and **Linux/Hyprland** (Wayland overlay).

**Key characteristics:**
- Single-language Python project
- Platform-specific implementations: `macos/` and `omarchy/`
- Shared core logic in `src/`
- Configuration via TOML
- Cross-platform process detection via `psutil`

## Project Structure

```
opencode-activity-monitor/
├── src/                     # Shared cross-platform code
│   ├── config.py            # TOML config loading with defaults
│   ├── opencode_data.py     # OpenCode session data fetching
│   ├── platform.py          # Cross-platform abstractions (psutil)
│   └── __init__.py
├── omarchy/                 # Linux/Hyprland implementation
│   ├── main.py              # Application entry point, signal handlers
│   ├── overlay.py           # GTK4 overlay window, UI refresh logic
│   ├── ui.py                # CSS generation and widget styling
│   ├── tray.py              # System tray icon (GTK3, AyatanaAppIndicator)
│   ├── tray_manager.py      # Tray process launcher
│   ├── install.sh           # Linux installer
│   ├── uninstall.sh         # Linux uninstaller
│   └── __init__.py
├── macos/                   # macOS implementation
│   ├── main.py              # Application entry point (PyObjC)
│   ├── overlay.py           # NSWindow overlay with vibrancy
│   ├── menu_bar.py          # NSStatusBar menu bar icon
│   ├── install.sh           # macOS installer
│   ├── uninstall.sh         # macOS uninstaller
│   └── __init__.py
├── install.sh               # Platform router (detects OS, runs correct installer)
├── uninstall.sh             # Platform router (uninstall)
├── config.toml              # User configuration template
├── requirements.txt         # Python dependencies
└── README.md                # User documentation
```

## Development Workflow

### Running from Source

**Linux (Hyprland):**
```bash
LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so python3 -m omarchy.main

# Toggle click-through mode (sends SIGUSR1)
kill -USR1 $(pgrep -f "omarchy.main")

# Toggle visibility (sends SIGUSR2)
kill -USR2 $(pgrep -f "omarchy.main")
```

**macOS:**
```bash
python3 -m macos.main
```

### Installation

```bash
./install.sh  # Auto-detects platform and runs appropriate installer
```

**Linux install locations:**
- App: `~/.local/share/opencode-activity-monitor/`
- Config: `~/.config/opencode-activity-monitor/config.toml`
- Binaries: `~/.local/bin/opencode-activity-monitor*`
- Systemd: `~/.config/systemd/user/opencode-activity-monitor.service`

**macOS install locations:**
- App: `~/Library/Application Support/opencode-activity-monitor/`
- Config: `~/Library/Application Support/opencode-activity-monitor/config.toml`
- LaunchAgent: `~/Library/LaunchAgents/com.opencode.activity-monitor.plist`
- Logs: `~/Library/Logs/opencode-activity-monitor.log`

## Architecture

### Shared Code (`src/`)

#### Configuration Loading (`src/config.py`)
- Uses `tomllib` (Python 3.11+) or `tomli` (Python 3.9+)
- Search order: platform config dir → repo root `config.toml`
- Deep merge: user config overrides `DEFAULT_CONFIG` dict
- Exported as `CONFIG` singleton

#### Session Data Fetching (`src/opencode_data.py`)
- Uses `psutil` for cross-platform process discovery
- Matches processes to session metadata from `opencode session list --format json`
- Key dataclass: `Session` (id, title, project, path, status, last_active_fmt)
- Process filtering: excludes helper processes (run, x, acp, serve, etc.)
- CPU-based activity detection for status (active/idle/stale)

#### Platform Abstraction (`src/platform.py`)
- `is_macos()` / `is_linux()`: Platform detection
- `get_config_dir()`: Platform-appropriate config path
- `find_opencode_processes()`: Cross-platform process discovery
- `get_process_cwd()` / `get_process_cpu_time()`: Process introspection

### Linux Implementation (`omarchy/`)

**Main Application (`omarchy/main.py`):**
- GTK4 application with signal handlers
- Spawns tray process (monitor parent PID)
- SIGUSR1/SIGUSR2 for toggle controls

**Overlay Window (`omarchy/overlay.py`):**
- GTK4 + gtk4-layer-shell for Wayland integration
- Dynamic input region for click-through mode
- Threaded data refresh

**System Tray (`omarchy/tray.py`):**
- GTK3 + AyatanaAppIndicator3 (separate process)
- Menu: Show/Hide, Toggle Click-through, Exit

### macOS Implementation (`macos/`)

**Main Application (`macos/main.py`):**
- PyObjC NSApplication with AppDelegate
- NSTimer-based refresh loop
- Menu bar actions via @objc.IBAction

**Overlay Window (`macos/overlay.py`):**
- NSWindow with NSVisualEffectView (HUDWindow material)
- Draggable window with position memory
- Click-through via setIgnoresMouseEvents_

**Menu Bar (`macos/menu_bar.py`):**
- NSStatusBar with SF Symbols icon
- Menu: Show/Hide, Toggle Click-through, Reset Position, Quit

## Code Style Guidelines

### Python Conventions
- **Type hints:** Required for function signatures and dataclass fields
- **Dataclasses:** Use for structured data (Session)
- **Imports:** Group standard library, third-party, local modules
- **String formatting:** f-strings preferred
- **Error handling:** Print to stderr, continue gracefully

### Configuration Access

```python
from src.config import CONFIG

interval = CONFIG["monitor"]["refresh_interval_ms"]
opacity = CONFIG["appearance"]["background_opacity"]
anchor = CONFIG["position"]["anchor"]
```

## Common Tasks

### Add New Configuration Option
1. Add key to `DEFAULT_CONFIG` in `src/config.py`
2. Add documentation comment to `config.toml`
3. Use via `CONFIG["section"]["key"]`

### Modify Session Data Display
Edit `Session` dataclass in `src/opencode_data.py` or UI rendering in:
- Linux: `omarchy/ui.py` → `make_session_row()`
- macOS: `macos/overlay.py` → `update_sessions()`

### Add Platform-Specific Feature
1. Implement in `omarchy/` or `macos/` directory
2. Use `src/platform.py` for any shared cross-platform logic
3. Update platform-specific installer if needed

## Dependencies

**Linux (Arch/pacman):**
- `python-gobject` (PyGObject bindings)
- `gtk4` (GUI toolkit)
- `gtk4-layer-shell` (Wayland layer shell)
- `python-psutil` (process management)
- `libayatana-appindicator` (tray icon)

**macOS:**
- `pyobjc-core` (Python-ObjC bridge)
- `pyobjc-framework-Cocoa` (AppKit/Foundation)
- `psutil` (process management)

## Platform Constraints

**Linux:**
- Hyprland/Wayland only (wlroots-based compositor)
- Uses gtk4-layer-shell for overlay

**macOS:**
- macOS 11+ (Big Sur or later)
- Uses NSVisualEffectView for vibrancy
