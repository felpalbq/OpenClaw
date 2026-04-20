import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).parent
INDEX_PATH = MEMORY_DIR / "index.json"
INTERACTIONS_DIR = MEMORY_DIR / "interactions"
CLIENTS_DIR = MEMORY_DIR / "clients"
PATTERNS_DIR = MEMORY_DIR / "patterns"


def _load_index() -> dict:
    if not INDEX_PATH.exists():
        return {"entries": [], "stats": {"total": 0, "by_type": {}}, "last_updated": ""}
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_index(index: dict):
    index["last_updated"] = datetime.now().isoformat()
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def _generate_id(entry: dict) -> str:
    content = f"{entry.get('type','')}|{entry.get('summary','')}|{entry.get('context','')}"
    return f"mem_{hashlib.md5(content.encode()).hexdigest()[:8]}"


def _type_dir(mem_type: str) -> Path:
    mapping = {
        "interaction": INTERACTIONS_DIR,
        "client_learning": CLIENTS_DIR,
        "pattern": PATTERNS_DIR,
        "error": INTERACTIONS_DIR,
    }
    return mapping.get(mem_type, INTERACTIONS_DIR)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_memory(mem_type: str = None, limit: int = 50) -> list:
    index = _load_index()
    entries = index.get("entries", [])

    if mem_type:
        entries = [e for e in entries if e.get("type") == mem_type]

    result = []
    for entry in entries[:limit]:
        mem_id = entry.get("id", "")
        tdir = _type_dir(entry.get("type", "interaction"))
        fpath = tdir / f"{mem_id}.json"
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                result.append(json.load(f))
        else:
            result.append(entry)

    return result


def write_memory(entry: dict) -> str:
    if "id" not in entry:
        entry["id"] = _generate_id(entry)
    if "date" not in entry:
        entry["date"] = datetime.now().isoformat()

    mem_id = entry["id"]
    mem_type = entry.get("type", "interaction")

    # Save full entry to type-specific directory
    tdir = _type_dir(mem_type)
    tdir.mkdir(parents=True, exist_ok=True)
    fpath = tdir / f"{mem_id}.json"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)

    # Update index with summary
    index = _load_index()
    existing_ids = {e["id"] for e in index.get("entries", [])}
    if mem_id not in existing_ids:
        index.setdefault("entries", []).append({
            "id": mem_id,
            "type": mem_type,
            "summary": entry.get("summary", "")[:200],
            "date": entry["date"],
            "relevance": entry.get("relevance", "medium"),
        })
        index["stats"]["total"] = len(index["entries"])
        by_type = index["stats"].setdefault("by_type", {})
        by_type[mem_type] = by_type.get(mem_type, 0) + 1

    _save_index(index)
    return mem_id


def should_register(entry: dict) -> bool:
    relevance = entry.get("relevance", "").lower()
    mem_type = entry.get("type", "").lower()

    # High relevance always registers
    if relevance in ("high", "alta"):
        return True

    # Explicit feedback always registers
    if mem_type == "feedback":
        return True

    # Error resolved always registers
    if mem_type == "error_resolved":
        return True

    # Client learning always registers
    if mem_type == "client_learning":
        return True

    # Pattern after confirmation (3+ occurrences) registers
    if mem_type == "pattern":
        return True

    # Duplicates never register
    if entry.get("duplicate"):
        return False

    # Casual/none relevance never registers
    if relevance in ("none", "low", "baixa") and mem_type in ("casual", "interaction"):
        return False

    # Medium relevance interactions: register only if summary has substance
    if mem_type == "interaction" and relevance == "medium":
        summary = entry.get("summary", "")
        return len(summary) > 20

    return False


def search_memory(query: str, limit: int = 10) -> list:
    index = _load_index()
    query_lower = query.lower()
    results = []
    for entry in index.get("entries", []):
        if query_lower in entry.get("summary", "").lower():
            results.append(entry)
        if len(results) >= limit:
            break

    # Load full entries
    full = []
    for entry in results:
        tdir = _type_dir(entry.get("type", "interaction"))
        fpath = tdir / f"{entry['id']}.json"
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                full.append(json.load(f))
        else:
            full.append(entry)
    return full


def get_context_for_session() -> str:
    memory = read_memory(limit=20)
    if not memory:
        return "Nenhuma memória anterior."

    lines = []
    for entry in memory:
        date = entry.get("date", "")[:10]
        summary = entry.get("summary", "")
        lines.append(f"[{date}] {summary}")

    return "\n".join(lines)