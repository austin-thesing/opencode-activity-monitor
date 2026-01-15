import subprocess
import json
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Set

from src.platform import (
    get_process_cpu_time,
    get_process_cwd,
    process_exists,
    find_opencode_processes
)


@dataclass
class Session:
    """Represents a running OpenCode session."""
    id: str
    pid: int
    title: str
    project: str
    path: str
    status: str
    last_active_raw: float
    last_active_fmt: str
    agent: Optional[str] = None
    is_group_start: bool = False


# Status thresholds (in seconds)
ACTIVE_THRESHOLD = 30      # Active if CPU activity within last 30s
IDLE_THRESHOLD = 5 * 60    # Idle if inactive 30s - 5min
# Stale if inactive > 5min


def get_status_from_inactivity(seconds_inactive: float) -> str:
    if seconds_inactive < ACTIVE_THRESHOLD:
        return "active"
    elif seconds_inactive < IDLE_THRESHOLD:
        return "idle"
    return "stale"


_cpu_state: Dict[int, tuple] = {}
_title_cache: Dict[str, tuple] = {}
_TITLE_CACHE_TTL = 60


def get_cpu_time(pid: int) -> Optional[int]:
    return get_process_cpu_time(pid)


def is_process_active(pid: int, threshold_ticks: int = 10) -> tuple[bool, float]:
    now = time.time()
    cpu_time = get_cpu_time(pid)

    if cpu_time is None:
        if pid in _cpu_state:
            _, _, last_active = _cpu_state[pid]
            return (False, last_active)
        return (False, 0)

    if pid not in _cpu_state:
        _cpu_state[pid] = (cpu_time, now, 0)
        return (False, 0)

    last_cpu, last_check, last_active = _cpu_state[pid]
    time_delta = now - last_check

    if time_delta < 0.5:
        is_active = last_active > 0 and (now - last_active) < 30
        return (is_active, last_active)

    cpu_delta = cpu_time - last_cpu

    if time_delta > 1:
        cpu_rate = cpu_delta / time_delta
    else:
        cpu_rate = cpu_delta

    if cpu_rate > threshold_ticks:
        _cpu_state[pid] = (cpu_time, now, now)
        return (True, now)
    else:
        _cpu_state[pid] = (cpu_time, now, last_active)
        is_active = last_active > 0 and (now - last_active) < 30
        return (is_active, last_active)


def get_running_processes() -> List[dict]:
    processes = []

    proc_list = find_opencode_processes()

    if not proc_list:
        return []

    for proc in proc_list:
        pid = proc['pid']
        cmdline = proc['cmdline']

        args = cmdline.split()

        if len(args) > 1:
            subcommand = args[1]
            if subcommand in ('run', 'x', 'acp', 'serve', 'session',
                              'completion', 'add', 'install', 'upgrade',
                              'debug', 'export', 'import', 'models',
                              'stats', 'auth', 'mcp', 'github', 'pr',
                              'attach', 'web', 'agent'):
                continue

        if '/opencode run' in cmdline or 'extension-host' in cmdline:
            continue

        cwd = get_process_cwd(pid)
        if not cwd:
            continue

        session_id = None
        agent_name = None
        for i, arg in enumerate(args):
            if arg in ("-s", "--session") and i + 1 < len(args):
                session_id = args[i + 1]
            elif arg == "--agent" and i + 1 < len(args):
                agent_name = args[i + 1]

        processes.append({
            'pid': pid,
            'cwd': cwd,
            'session_id': session_id,
            'agent': agent_name,
        })

    return processes


def get_session_title(path: str) -> tuple[str, str]:
    now = time.time()

    if path in _title_cache:
        title, session_id, fetched_at = _title_cache[path]
        if now - fetched_at < _TITLE_CACHE_TTL:
            return (title, session_id)

    try:
        output = subprocess.check_output(
            ["opencode", "session", "list", "--format", "json", "--max-count", "5"],
            stderr=subprocess.DEVNULL,
            cwd=path,
            timeout=2,
        )
        sessions = json.loads(output)

        for sess in sessions:
            if sess.get('directory') == path:
                title = sess.get('title', 'Session')
                session_id = sess.get('id', '')
                _title_cache[path] = (title, session_id, now)
                return (title, session_id)

        if sessions:
            title = sessions[0].get('title', 'Session')
            session_id = sessions[0].get('id', '')
            _title_cache[path] = (title, session_id, now)
            return (title, session_id)

    except (subprocess.CalledProcessError, FileNotFoundError,
            subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass

    fallback = os.path.basename(path)
    return (fallback, f"path-{path}")


def format_time_ago(seconds: float) -> str:
    if seconds < 0:
        return "now"
    elif seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        if mins > 0:
            return f"{hours}h{mins}m"
        return f"{hours}h"
    return f"{int(seconds // 86400)}d"


def fetch_data() -> List[Session]:
    processes = get_running_processes()

    if not processes:
        return []

    now = time.time()
    sessions_data: List[dict] = []

    for proc in processes:
        pid = proc['pid']
        cwd = proc['cwd']
        project_name = os.path.basename(cwd)

        # Check if process is actually still running
        if not process_exists(pid):
            continue

        is_active, last_active_time = is_process_active(pid)

        if is_active:
            seconds_inactive = 0
            status = "active"
        elif last_active_time > 0:
            seconds_inactive = now - last_active_time
            status = get_status_from_inactivity(seconds_inactive)
        else:
            seconds_inactive = float('inf')
            status = "stale"

        if last_active_time > 0:
            time_fmt = format_time_ago(seconds_inactive)
        else:
            time_fmt = ""

        title, session_id = get_session_title(cwd)

        sessions_data.append({
            'id': session_id,
            'pid': pid,
            'title': title,
            'project': project_name,
            'path': cwd,
            'status': status,
            'last_active_raw': last_active_time * 1000 if last_active_time else 0,
            'last_active_fmt': time_fmt,
            'agent': proc.get('agent'),
        })

    # Remove duplicate sessions by path, keeping most active
    seen_paths: Dict[str, dict] = {}
    for s in sessions_data:
        path = s['path']
        status_priority = {"active": 0, "idle": 1, "stale": 2}
        current_priority = status_priority.get(s['status'], 3)
        
        if path not in seen_paths:
            seen_paths[path] = s
        else:
            existing = seen_paths[path]
            existing_priority = status_priority.get(existing['status'], 3)
            if current_priority < existing_priority:
                seen_paths[path] = s
            elif current_priority == existing_priority and s['last_active_raw'] > existing['last_active_raw']:
                seen_paths[path] = s

    # Sort unique sessions
    unique_sessions = list(seen_paths.values())
    unique_sessions.sort(key=lambda s: (
        0 if s['status'] == "active" else (1 if s['status'] == "idle" else 2),
        -(s['last_active_raw'] or 0),
        s['path'],
    ))

    active_sessions: List[Session] = []
    seen_dirs: Set[str] = set()

    for s in unique_sessions:
        path = s['path']
        parent = os.path.dirname(path)

        is_new_group = path not in seen_dirs
        if parent in seen_dirs:
            is_new_group = False

        seen_dirs.add(path)

        active_sessions.append(Session(
            id=s['id'],
            pid=s['pid'],
            title=s['title'],
            project=s['project'],
            path=path,
            status=s['status'],
            last_active_raw=s['last_active_raw'],
            last_active_fmt=s['last_active_fmt'],
            agent=s['agent'],
            is_group_start=is_new_group and len(active_sessions) > 0,
        ))

    return active_sessions


def cleanup_stale_pids():
    stale = [pid for pid in _cpu_state if not process_exists(pid)]
    for pid in stale:
        del _cpu_state[pid]
