import json
import os
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).parent
INDEX_PATH = MEMORY_DIR / "index.json"
INTERACTIONS_DIR = MEMORY_DIR / "interactions"
CLIENTS_DIR = MEMORY_DIR / "clients"
PATTERNS_DIR = MEMORY_DIR / "patterns"

MAX_ENTRIES = 500
TTL_HIGH = None
TTL_MEDIUM_DAYS = 90
TTL_LOW_DAYS = 30


def _git(*args) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", "-C", str(MEMORY_DIR)] + list(args),
        capture_output=True, text=True, timeout=30
    )
    return result


def has_git_repo() -> bool:
    return (MEMORY_DIR / ".git").exists()


def init_repo():
    if not has_git_repo():
        _git("init")
        _git("checkout", "-b", "ahri-memory")
        _git("config", "user.email", "ahri@openclaw.local")
        _git("config", "user.name", "Ahri")
        _git("add", ".")
        _git("commit", "-m", "init: ahri memory repo")
        print("  [OK] Repositorio Git da memoria inicializado")


def commit(message: str) -> bool:
    if not has_git_repo():
        return False

    _git("add", ".")
    result = _git("commit", "-m", message)
    return result.returncode == 0


def push() -> bool:
    if not has_git_repo():
        return False

    result = _git("push", "origin", "ahri-memory")
    if result.returncode == 0:
        return True

    # Push failed — try rebase
    pull_result = _git("pull", "--rebase", "origin", "ahri-memory")
    if pull_result.returncode == 0:
        result2 = _git("push", "origin", "ahri-memory")
        return result2.returncode == 0

    # Rebase conflict — resolve index.json
    _resolve_index_conflict()
    _git("add", ".")
    _git("rebase", "--continue")
    result3 = _git("push", "origin", "ahri-memory")
    if result3.returncode == 0:
        return True

    # Unrecoverable — log error
    try:
        from state import merge_state
        merge_state({"integrations": {"ahri_memory": {"status": "git_sync_failed"}}},
                     agent="ahri_memory", reason="git_push_failed")
    except Exception:
        pass
    return False


def pull() -> bool:
    if not has_git_repo():
        return False

    result = _git("pull", "origin", "ahri-memory")
    return result.returncode == 0


def _resolve_index_conflict():
    """Resolve merge conflicts in index.json by merging both entry lists and deduplicating."""
    index_path = INDEX_PATH
    if not index_path.exists():
        return

    try:
        with open(index_path, encoding="utf-8") as f:
            content = f.read()

        if "<<<<<<<" not in content:
            return

        # Parse both sides of the conflict
        ours = []
        theirs = []
        current = None
        for line in content.split("\n"):
            if line.startswith("<<<<<<<"):
                current = "ours"
                continue
            if line.startswith("======="):
                current = "theirs"
                continue
            if line.startswith(">>>>>>>"):
                current = None
                continue

        # Simpler approach: re-read from git stages
        _git("checkout", "--theirs", "index.json")
        theirs_data = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"entries": []}

        _git("checkout", "--ours", "index.json")
        ours_data = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"entries": []}

        # Merge entries by ID
        all_entries = {}
        for e in ours_data.get("entries", []):
            all_entries[e.get("id", "")] = e
        for e in theirs_data.get("entries", []):
            eid = e.get("id", "")
            if eid not in all_entries:
                all_entries[eid] = e

        merged = {
            "entries": list(all_entries.values()),
            "stats": {
                "total": len(all_entries),
                "by_type": _count_by_type(all_entries.values()),
            },
            "last_updated": datetime.now().isoformat(),
        }

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

    except Exception:
        pass


def _count_by_type(entries) -> dict:
    counts = {}
    for e in entries:
        t = e.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Memory filters — enhanced
# ---------------------------------------------------------------------------

def _content_hash(entry: dict) -> str:
    content = f"{entry.get('type','')}|{entry.get('summary','')}|{entry.get('context','')}"
    return hashlib.md5(content.encode()).hexdigest()


def _is_near_duplicate(entry: dict, existing_entries: list) -> bool:
    new_hash = _content_hash(entry)
    new_summary = entry.get("summary", "").lower()[:100]

    for existing in existing_entries:
        if _content_hash(existing) == new_hash:
            return True

        existing_summary = existing.get("summary", "").lower()[:100]
        if new_summary and existing_summary:
            overlap = sum(1 for w in new_summary.split() if w in existing_summary)
            total = len(new_summary.split())
            if total > 0 and overlap / total > 0.8:
                return True

    return False


def _is_expired(entry: dict) -> bool:
    relevance = entry.get("relevance", "medium")
    date_str = entry.get("date", "")

    if not date_str:
        return False

    try:
        entry_date = datetime.fromisoformat(date_str)
        age_days = (datetime.now() - entry_date).days
    except (ValueError, TypeError):
        return False

    ttl_map = {
        "high": None,
        "alta": None,
        "medium": TTL_MEDIUM_DAYS,
        "low": TTL_LOW_DAYS,
        "baixa": TTL_LOW_DAYS,
        "none": 1,
    }

    ttl = ttl_map.get(relevance, TTL_MEDIUM_DAYS)
    if ttl is None:
        return False
    return age_days > ttl


def should_register(entry: dict) -> bool:
    relevance = entry.get("relevance", "").lower()
    mem_type = entry.get("type", "").lower()

    if relevance in ("high", "alta"):
        return True
    if mem_type == "feedback":
        return True
    if mem_type == "error_resolved":
        return True
    if mem_type == "client_learning":
        return True
    if mem_type == "pattern":
        return True
    if entry.get("duplicate"):
        return False
    if relevance in ("none", "low", "baixa") and mem_type in ("casual",):
        return False

    # Check against existing entries for near-duplicates
    try:
        index = _load_index()
        existing = index.get("entries", [])
        if _is_near_duplicate(entry, existing):
            return False
    except Exception:
        pass

    # Check total count
    try:
        index = _load_index()
        if len(index.get("entries", [])) >= MAX_ENTRIES:
            # Only register if high relevance
            return relevance in ("high", "alta")
    except Exception:
        pass

    if mem_type == "interaction" and relevance == "medium":
        summary = entry.get("summary", "")
        return len(summary) > 20

    return False


def _prune_expired():
    index = _load_index()
    entries = index.get("entries", [])

    active = []
    pruned = 0
    for entry in entries:
        if _is_expired(entry):
            # Remove file
            mem_id = entry.get("id", "")
            tdir = _type_dir(entry.get("type", "interaction"))
            fpath = tdir / f"{mem_id}.json"
            if fpath.exists():
                fpath.unlink()
            pruned += 1
        else:
            active.append(entry)

    if pruned > 0:
        index["entries"] = active
        index["stats"]["total"] = len(active)
        index["stats"]["by_type"] = _count_by_type(active)
        _save_index(index)

    return pruned


def _consolidate_entries():
    """Merge 3+ entries about the same topic into 1."""
    index = _load_index()
    entries = index.get("entries", [])

    topic_groups = {}
    for entry in entries:
        summary = entry.get("summary", "").lower()
        words = summary.split()[:3]
        key = " ".join(words)
        topic_groups.setdefault(key, []).append(entry)

    consolidated = 0
    final = []
    for key, group in topic_groups.items():
        if len(group) >= 3:
            # Keep the most recent, discard others
            group.sort(key=lambda e: e.get("date", ""), reverse=True)
            final.append(group[0])
            for old in group[1:]:
                mem_id = old.get("id", "")
                tdir = _type_dir(old.get("type", "interaction"))
                fpath = tdir / f"{mem_id}.json"
                if fpath.exists():
                    fpath.unlink()
            consolidated += len(group) - 1
        else:
            final.extend(group)

    if consolidated > 0:
        index["entries"] = final
        index["stats"]["total"] = len(final)
        index["stats"]["by_type"] = _count_by_type(final)
        _save_index(index)

    return consolidated


# ---------------------------------------------------------------------------
# Core memory operations
# ---------------------------------------------------------------------------

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
    return f"mem_{_content_hash(entry)[:8]}"


def _type_dir(mem_type: str) -> Path:
    mapping = {
        "interaction": INTERACTIONS_DIR,
        "client_learning": CLIENTS_DIR,
        "pattern": PATTERNS_DIR,
        "error": INTERACTIONS_DIR,
        "error_resolved": INTERACTIONS_DIR,
        "feedback": INTERACTIONS_DIR,
    }
    return mapping.get(mem_type, INTERACTIONS_DIR)


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

    tdir = _type_dir(mem_type)
    tdir.mkdir(parents=True, exist_ok=True)
    fpath = tdir / f"{mem_id}.json"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)

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

    # Auto-commit
    try:
        commit(f"{mem_type}: {entry.get('summary', 'memory update')[:60]}")
    except Exception:
        pass

    return mem_id


def search_memory(query: str, limit: int = 10) -> list:
    index = _load_index()
    query_lower = query.lower()
    results = []
    for entry in index.get("entries", []):
        if query_lower in entry.get("summary", "").lower():
            results.append(entry)
        if len(results) >= limit:
            break

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
    _prune_expired()
    _consolidate_entries()
    memory = read_memory(limit=20)
    if not memory:
        return "Nenhuma memoria anterior."
    lines = []
    for entry in memory:
        date = entry.get("date", "")[:10]
        summary = entry.get("summary", "")
        lines.append(f"[{date}] {summary}")
    return "\n".join(lines)


def maintenance():
    pruned = _prune_expired()
    consolidated = _consolidate_entries()
    pushed = push()
    return {"pruned": pruned, "consolidated": consolidated, "pushed": pushed}