import json
import os
import sys
from pathlib import Path

AHRI_MEMORY_DIR = Path(os.environ.get("AHRI_MEMORY_DIR", str(Path(__file__).parent.parent / "ahri")))

if str(AHRI_MEMORY_DIR) not in sys.path:
    sys.path.insert(0, str(AHRI_MEMORY_DIR))

try:
    import ahri as ahri_memory
    _HAS_AHRI = True
except ImportError:
    _HAS_AHRI = False


def read_context(key: str):
    if _HAS_AHRI:
        return ahri_memory.read_entry("context", key)
    path = AHRI_MEMORY_DIR / "context" / f"{key}.json"
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def write_context(key: str, data):
    if _HAS_AHRI:
        ahri_memory.write_entry("context", key, data if isinstance(data, dict) else {"data": data})
        return
    (AHRI_MEMORY_DIR / "context").mkdir(parents=True, exist_ok=True)
    path = AHRI_MEMORY_DIR / "context" / f"{key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_context(key: str, partial: dict):
    current = read_context(key) or {}
    if isinstance(current, dict) and isinstance(partial, dict):
        current.update(partial)
    else:
        current = partial
    write_context(key, current)


def list_context_keys() -> list:
    ctx_dir = AHRI_MEMORY_DIR / "context"
    if not ctx_dir.exists():
        return []
    return [p.stem for p in ctx_dir.glob("*.json")]


def read_client(client_id: str):
    clients = read_context("clients")
    if not clients or not isinstance(clients, dict):
        return None
    return clients.get(client_id)


def write_client(client_id: str, data: dict):
    clients = read_context("clients") or {}
    clients[client_id] = data
    write_context("clients", clients)