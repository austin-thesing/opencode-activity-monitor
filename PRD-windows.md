# PRD: Windows Port (AI Handoff)

## Purpose
Provide a just-enough guide for an AI agent on Windows to port, run, and validate this Linux-first overlay app.

## Current Baseline (Repo Reality)
- GTK4 overlay window using `gtk4-layer-shell` (Wayland only).
- Tray uses GTK3 + Ayatana AppIndicator.
- Controls use UNIX signals (`SIGUSR1` toggle click-through, `SIGUSR2` toggle visibility).
- Config loads from XDG Linux paths via `src/config.py`.
- Data polling and session parsing live in `src/opencode_data.py`.

## Porting Target (Windows)
Deliver a minimal, functional Windows overlay with:
- Always-on-top transparent window.
- Full click-through toggle (selective regions optional but not required).
- System tray menu for show/hide, toggle click-through, quit.
- Config loading from Windows path.
- Same session polling logic and UI layout, reusing as much code as possible.

## Non-Goals
- Perfect per-widget hit-testing on first pass.
- Packaging/installer, signing, auto-updates.
- Replacing the data layer.

## Suggested Architecture
- Keep `src/opencode_data.py` as-is (or extract to `core/` if needed).
- Add a Windows-specific entry point (e.g., `platforms/windows/main.py`).
- Implement overlay + tray with Win32 (`pywin32` or `ctypes`).
- Replace signals with a small local control API (named pipe or TCP) if needed; otherwise wire tray directly to in-process handlers.

## Windows Implementation Sketch
### Window
- Borderless layered window using `WS_EX_TOPMOST | WS_EX_LAYERED`.
- Click-through toggle via `WS_EX_TRANSPARENT` on/off.
- Use `SetLayeredWindowAttributes` for opacity.

### Tray
- `Shell_NotifyIcon` via `pywin32` or `pystray`.
- Menu items:
  - Toggle visibility
  - Toggle click-through
  - Quit

### Config Path
- Use `%APPDATA%\opencode-activity-monitor\config.toml`.

## Implementation Notes (Windows)
- Keep data logic in `src/opencode_data.py` unchanged.
- Mirror config keys from `src/config.py` so the same `config.toml` works.
- UI can be minimal: header "OPENCODE" and rows of `project`, `status`, `time`.
- Poll with the same refresh interval as `CONFIG["monitor"]["refresh_interval_ms"]`.
- If you split modules, keep names obvious: `platforms/windows/main.py`, `platforms/windows/ui.py`.

## Minimal Test Checklist (Windows)
- Overlay shows and stays on top.
- Click-through toggle works (full window).
- Tray menu actions work.
- Session list updates periodically.
- Config changes reflected after restart.

## Notes for AI Agent
- A basic text UI (drawn with GDI or a minimal toolkit) is acceptable.
- Focus on a working overlay and tray before adding selective input.
- Keep naming consistent with existing config keys and status labels.
