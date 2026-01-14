#!/bin/bash
# OpenCode Activity Monitor - Launcher with proper layer-shell preload
export LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so
exec python3 "${HOME}/.local/share/opencode-activity-monitor/main.py" "$@"
