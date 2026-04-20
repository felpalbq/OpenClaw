import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

STATE_DIR = Path(__file__).parent
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
STATE_PATH = STATE_DIR / STATE_FILE
LOCK_PATH = STATE_DIR / f"{STATE_FILE}.lock"
TMP_PATH = STATE_DIR / f"{STATE_FILE}.tmp"

_IS_WINDOWS = sys.platform == "win32"


def _acquire_lock(lock_fd):
    if _IS_WINDOWS:
        import msvcrt
        msvcrt.locking(lock_fd.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl
        fcntl.flock(lock_fd, fcntl.LOCK_EX)


def _release_lock(lock_fd):
    if _IS_WINDOWS:
        import msvcrt
        try:
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        import fcntl
        fcntl.flock(lock_fd, fcntl.LOCK_UNLCK)


def read_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def write_state(data: dict, agent: str = "", reason: str = ""):
    if agent:
        if "meta" not in data:
            data["meta"] = {}
        data["meta"]["last_written_by"] = agent
        data["meta"]["last_written_reason"] = reason
        data["meta"]["last_written_at"] = datetime.now().isoformat()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)

    lock_fd = open(LOCK_PATH, "w")
    try:
        _acquire_lock(lock_fd)
        with open(TMP_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        if STATE_PATH.exists():
            backup = STATE_DIR / f"{STATE_FILE}.bak"
            try:
                os.replace(str(STATE_PATH), str(backup))
            except OSError:
                pass
        os.replace(str(TMP_PATH), str(STATE_PATH))
    finally:
        _release_lock(lock_fd)
        lock_fd.close()


def merge_state(partial: dict, agent: str = "", reason: str = ""):
    state = read_state()
    _deep_merge(state, partial)
    write_state(state, agent=agent, reason=reason)


def _deep_merge(base: dict, override: dict):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value