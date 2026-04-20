import json
import os
import sys
from datetime import datetime
from pathlib import Path

AHRI_MEMORY_DIR = Path(os.environ.get("AHRI_MEMORY_DIR", str(Path(__file__).parent.parent / "ahri")))

if str(AHRI_MEMORY_DIR) not in sys.path:
    sys.path.insert(0, str(AHRI_MEMORY_DIR))

SESSIONS_DIR = AHRI_MEMORY_DIR / "sessions"
CONTEXT_CHARS = 4000

try:
    import ahri as ahri_memory
    _HAS_AHRI = True
except ImportError:
    _HAS_AHRI = False


def append_session(role: str, content: str, metadata: dict = None):
    if _HAS_AHRI:
        ahri_memory.append_session(role, content, metadata)
        return

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().isoformat(),
        "role": role,
        "content": content,
    }
    if metadata:
        entry["metadata"] = metadata

    path = SESSIONS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_recent_history(limit: int = 20, timeout_minutes: int = 30) -> list:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True)

    entries = []
    now = datetime.now()
    cutoff = now.timestamp() - (timeout_minutes * 60)

    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue

    entries.reverse()

    recent = []
    for entry in entries[-limit:]:
        try:
            ts = datetime.fromisoformat(entry.get("ts", "")).timestamp()
            if ts >= cutoff:
                recent.append({"role": entry["role"], "content": entry["content"]})
        except (ValueError, TypeError):
            recent.append({"role": entry["role"], "content": entry["content"]})

    return recent


def get_recent_context(max_chars: int = CONTEXT_CHARS) -> str:
    if _HAS_AHRI:
        try:
            return ahri_memory.get_context_for_session()
        except Exception:
            pass

    history = get_recent_history()
    if not history:
        return ""

    lines = []
    total = 0
    for entry in reversed(history):
        line = f"{entry['role']}: {entry['content'][:200]}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)

    lines.reverse()
    return "\n".join(lines)


def cleanup_old_sessions(max_days: int = 30):
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    for path in SESSIONS_DIR.glob("*.jsonl"):
        try:
            date_str = path.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if (now - file_date).days > max_days:
                path.unlink()
        except (ValueError, OSError):
            pass