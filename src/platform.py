"""Cross-platform platform abstraction layer."""

import sys
from pathlib import Path
from typing import Optional, List, Dict
import psutil


def is_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform.startswith("linux")


def get_config_dir() -> Path:
    """Get platform-appropriate config directory."""
    if is_macos():
        return Path.home() / "Library" / "Application Support" / "opencode-activity-monitor"
    else:
        return Path.home() / ".config" / "opencode-activity-monitor"


def get_process_cwd(pid: int) -> Optional[str]:
    """Get working directory of a process."""
    try:
        return psutil.Process(pid).cwd()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def get_process_cpu_time(pid: int) -> Optional[int]:
    """Get total CPU time (user + system) in centiseconds."""
    try:
        times = psutil.Process(pid).cpu_times()
        return int((times.user + times.system) * 100)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def process_exists(pid: int) -> bool:
    """Check if a process exists."""
    return psutil.pid_exists(pid)


def find_opencode_processes() -> List[Dict]:
    """Find all running opencode processes with their PIDs and command lines."""
    results = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        try:
            info = proc.info
            cmdline = info.get('cmdline') or []
            cmdline_str = ' '.join(cmdline)

            if 'opencode' in cmdline_str:
                results.append({
                    'pid': info['pid'],
                    'cmdline': cmdline_str,
                    'cwd': info.get('cwd')
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return results
