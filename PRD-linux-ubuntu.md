# PRD: Linux (Ubuntu/Fedora/Debian) Port (AI Handoff)

## Purpose
Provide a just-enough guide for an AI agent on mainstream Linux desktops to port, run, and validate this Hyprland-first overlay app.

## Current Baseline (Repo Reality)
- Designed for Hyprland/Wayland with `gtk4-layer-shell`.
- Tray uses GTK3 + Ayatana AppIndicator.
- Click-through uses Wayland input regions (selective).
- Controls use UNIX signals (`SIGUSR1` toggle click-through, `SIGUSR2` toggle visibility).
- Config uses XDG path via `src/config.py`.

## Porting Target (Ubuntu/Fedora/Debian)
Deliver a minimal, functional overlay that runs on:
- Wayland (GNOME/KDE) when possible.
- X11 fallback when layer-shell is unavailable.

Required features:
- Always-on-top transparent window.
- Full click-through toggle (selective regions optional).
- Tray menu (if AppIndicator is available; otherwise optional).
- Same session polling logic and UI layout.

## Non-Goals
- Perfect compositor-specific behavior.
- Advanced packaging or distro-specific installers.
- Guaranteed tray support on all desktops.

## Suggested Approach
### Backend Detection
- Detect Wayland vs X11 at runtime (`WAYLAND_DISPLAY` / `DISPLAY`).
- If Wayland + layer-shell available, use current overlay logic.
- Otherwise fall back to GTK keep-above window on X11.

### Click-through
- Wayland: use input regions when available.
- X11: best-effort click-through (full window) or disable if not supported.

### Tray
- Use Ayatana AppIndicator when available.
- If unavailable, run without tray and log a warning.

## Implementation Notes (Linux)
- Keep data logic in `src/opencode_data.py` unchanged.
- Mirror config keys from `src/config.py` so the same `config.toml` works.
- UI can be minimal: header "OPENCODE" and rows of `project`, `status`, `time`.
- Poll with the same refresh interval as `CONFIG["monitor"]["refresh_interval_ms"]`.
- If you split modules, keep names obvious: `platforms/linux/main.py`, `platforms/linux/ui.py`.

## Minimal Test Checklist (Linux)
- Overlay shows and stays on top on both Wayland and X11.
- Click-through toggle works or degrades gracefully.
- Tray works if AppIndicator is installed.
- Session list updates periodically.

## Notes for AI Agent
- Prioritize a working overlay on GNOME/KDE over perfect layer-shell parity.
- It is acceptable to make click-through a simple on/off toggle for the whole window.
- Keep config keys and UI labels aligned with `src/ui.py` and `src/config.py`.
