# PRD: macOS Port (AI Handoff)

## Purpose
Provide a just-enough guide for an AI agent on macOS to port, run, and validate this Linux-first overlay app.

## Current Baseline (Repo Reality)
- GTK4 overlay window using `gtk4-layer-shell` (Wayland only).
- Tray uses GTK3 + Ayatana AppIndicator.
- Controls use UNIX signals (`SIGUSR1` toggle click-through, `SIGUSR2` toggle visibility).
- Config loads from XDG Linux paths via `src/config.py`.
- Data polling and session parsing live in `src/opencode_data.py`.

## Porting Target (macOS)
Deliver a minimal, functional macOS overlay with:
- Always-on-top transparent window.
- Full click-through toggle (selective regions optional but not required).
- Status bar menu for show/hide, toggle click-through, quit.
- Config loading from macOS path.
- Same session polling logic and UI layout, reusing as much code as possible.

## Non-Goals
- Perfect per-widget hit-testing on first pass.
- Packaging, signing, auto-updates.
- Replacing the data layer.

## Suggested Architecture
- Keep `src/opencode_data.py` as-is (or extract to `core/` if needed).
- Add a macOS-specific entry point (e.g., `platforms/macos/main.py`).
- Implement UI + tray in AppKit (PyObjC), no GTK required.
- Replace signals with a small local control API (TCP or Unix socket) if needed; otherwise wire tray directly to in-process handlers.

## macOS Implementation Sketch
### Window
- Borderless `NSWindow`.
- `NSStatusWindowLevel` (or higher) to stay on top.
- Transparent background, non-opaque.
- Click-through via `setIgnoresMouseEvents_(True)`.

### Tray
- `NSStatusBar` + `NSMenu` with actions:
  - Toggle visibility
  - Toggle click-through
  - Quit

### Config Path
- Use `~/Library/Application Support/opencode-activity-monitor/config.toml`.

## Implementation Notes (macOS)
- Keep data logic in `src/opencode_data.py` unchanged.
- Mirror config keys from `src/config.py` so the same `config.toml` works.
- UI can be minimal: header "OPENCODE" and rows of `project`, `status`, `time`.
- Poll with the same refresh interval as `CONFIG["monitor"]["refresh_interval_ms"]`.
- If you split modules, keep names obvious: `platforms/macos/main.py`, `platforms/macos/ui.py`.

## Minimal Test Checklist (macOS)
- Overlay shows and stays on top.
- Click-through toggle works (full window).
- Tray menu actions work.
- Session list updates periodically.
- Config changes reflected after restart.

## Notes for AI Agent
- Do not attempt to perfectly mirror Wayland input regions; full click-through toggle is acceptable.
- Keep UI layout minimal and readable (use the same text as `src/ui.py`).
- Prioritize a working overlay over full parity.
