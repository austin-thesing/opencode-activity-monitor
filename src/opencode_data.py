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


def get_all_sessions_for_path(path: str) -> List[dict]:
    """Get all sessions for a given path."""
    now = time.time()
    cache_key = f"all_{path}"
    
    if cache_key in _title_cache:
        sessions, fetched_at = _title_cache[cache_key]
        if now - fetched_at < _TITLE_CACHE_TTL:
            return sessions

    try:
        output = subprocess.check_output(
            ["opencode", "session", "list", "--format", "json", "--max-count", "20"],
            stderr=subprocess.DEVNULL,
            cwd=path,
            timeout=2,
        )
        sessions = json.loads(output)
        
        # Filter to sessions matching this directory
        matching = [s for s in sessions if s.get('directory') == path]
        _title_cache[cache_key] = (matching, now)
        return matching

    except (subprocess.CalledProcessError, FileNotFoundError,
            subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass

    return []


def get_session_title(path: str, session_id: Optional[str] = None) -> tuple[str, str]:
    """Get session title, optionally matching a specific session ID."""
    sessions = get_all_sessions_for_path(path)
    
    # If we have a session ID, try to match it
    if session_id:
        for sess in sessions:
            if sess.get('id') == session_id:
                return (sess.get('title', 'Session'), session_id)
    
    # Otherwise return the most recent session for this path
    if sessions:
        sess = sessions[0]
        return (sess.get('title', 'Session'), sess.get('id', ''))
    
    # Fallback to directory name
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

        # Use session_id from process args if available
        proc_session_id = proc.get('session_id')
        title, session_id = get_session_title(cwd, proc_session_id)

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

    # Sort all sessions (no deduplication - show each unique session)
    sessions_data.sort(key=lambda s: (
        0 if s['status'] == "active" else (1 if s['status'] == "idle" else 2),
        -(s['last_active_raw'] or 0),
        s['path'],
    ))

    # Deduplicate by session ID (not path) - same session ID means same window
    seen_session_ids: Set[str] = set()
    active_sessions: List[Session] = []
    seen_dirs: Set[str] = set()

    for s in sessions_data:
        # Skip if we've already seen this exact session
        if s['id'] in seen_session_ids:
            continue
        seen_session_ids.add(s['id'])
        
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
