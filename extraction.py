import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = str(Path(__file__).parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

AHRI_MEMORY_DIR = Path(os.environ.get("AHRI_MEMORY_DIR", str(Path(__file__).parent.parent / "ahri")))

if str(AHRI_MEMORY_DIR) not in sys.path:
    sys.path.insert(0, str(AHRI_MEMORY_DIR))

import ahri as ahri_memory

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Repetition tracking
# ---------------------------------------------------------------------------

_TRACKING_PATH = AHRI_MEMORY_DIR / ".extraction_tracking.json"


def _read_tracking() -> dict:
    if not _TRACKING_PATH.exists():
        return {"events": {}}
    try:
        with open(_TRACKING_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"events": {}}


def _write_tracking(data: dict):
    with open(_TRACKING_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _increment_event(event_type: str, event_key: str) -> int:
    tracking = _read_tracking()
    events = tracking.setdefault("events", {})
    key = f"{event_type}:{event_key}"
    events[key] = events.get(key, 0) + 1
    _write_tracking(tracking)
    return events[key]


# ---------------------------------------------------------------------------
# Extraction from sessions
# ---------------------------------------------------------------------------

def extract_from_sessions(max_sessions: int = 200):
    sessions = ahri_memory.read_sessions(limit=max_sessions)

    for entry in sessions:
        role = entry.get("role", "")
        content = entry.get("content", "")
        ts = entry.get("ts", "")

        if role == "user":
            _check_explicit_decision(content, ts)
            _check_explicit_preference(content, ts)
            _check_context_update(content, ts)

        if role == "assistant":
            _check_intention_pattern(content, ts)

    # Check results for errors/successes
    _check_action_results()


def _check_explicit_decision(content: str, ts: str):
    decision_markers = [
        "decidimos", "a partir de agora", "vamos usar",
        "mudamos para", "decisão:", "decidido",
    ]
    content_lower = content.lower()

    for marker in decision_markers:
        if marker in content_lower:
            count = _increment_event("explicit_decision", content[:100])
            if count == 1:
                ahri_memory.write_entry(
                    "decisions",
                    f"d_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    {
                        "title": content[:100],
                        "context": "Identificado por extração de sessions",
                        "source": "extraction",
                        "status": "candidate",
                        "created_at": ts,
                    },
                    meta={"relevance": "high", "source": "extraction"},
                )
            elif count == 2:
                existing = ahri_memory.search_entries("decisions", content[:50])
                for entry in existing:
                    if entry.get("status") == "candidate" and entry.get("title", "")[:50] == content[:50]:
                        ahri_memory.write_entry(
                            "decisions", entry.get("id", ""),
                            {**entry, "status": "confirmed", "confirmed_at": ts},
                        )
                        break
            break


def _check_explicit_preference(content: str, ts: str):
    preference_markers = ["prefiro", "não faça", "nunca", "sempre", "gosto de", "não gosto"]
    content_lower = content.lower()

    for marker in preference_markers:
        if marker in content_lower:
            count = _increment_event("explicit_preference", content[:100])
            pref_text = content[:200]

            if count == 1:
                ahri_memory.write_entry(
                    "decisions",
                    f"d_pref_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    {
                        "title": f"Preferência: {pref_text[:80]}",
                        "context": "Identificado por extração de sessions",
                        "source": "extraction",
                        "status": "candidate",
                        "created_at": ts,
                    },
                    meta={"relevance": "medium", "source": "extraction"},
                )
            elif count == 2:
                existing = ahri_memory.search_entries("decisions", pref_text[:50])
                for entry in existing:
                    if entry.get("status") == "candidate" and pref_text[:50] in entry.get("title", ""):
                        ahri_memory.write_entry(
                            "decisions", entry.get("id", ""),
                            {**entry, "status": "confirmed", "confirmed_at": ts},
                        )
                        # Apply confirmed preference to user context
                        user_ctx = ahri_memory.read_entry("context", "user") or {}
                        prefs = user_ctx.setdefault("preferences", [])
                        if pref_text not in prefs:
                            prefs.append(pref_text)
                            ahri_memory.write_entry("context", "user", user_ctx)
                        break
            break


def _check_context_update(content: str, ts: str):
    context_markers = ["cliente", "projeto", "pausou", "mudou de foco", "entrou", "saiu"]
    content_lower = content.lower()

    for marker in context_markers:
        if marker in content_lower:
            count = _increment_event("context_update", content[:100])

            if count == 1:
                ahri_memory.write_entry(
                    "learnings",
                    f"l_ctx_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    {
                        "type": "context_update",
                        "summary": content[:200],
                        "status": "candidate",
                        "created_at": ts,
                    },
                    meta={"relevance": "medium", "source": "extraction"},
                )
            elif count == 2:
                existing = ahri_memory.search_entries("learnings", content[:50])
                for entry in existing:
                    if entry.get("status") == "candidate" and entry.get("type") == "context_update":
                        ahri_memory.write_entry(
                            "learnings", entry.get("id", ""),
                            {**entry, "status": "confirmed", "confirmed_at": ts},
                        )
                        break
            break


def _check_intention_pattern(content: str, ts: str):
    if "INTENTION:" in content:
        intentions = [line.strip() for line in content.split("\n") if line.strip().startswith("INTENTION:")]
        for intention in intentions:
            text = intention[10:].strip()
            count = _increment_event("intention", text[:100])
            if count >= 3:
                existing = ahri_memory.search_entries("patterns", text[:50])
                if not existing:
                    ahri_memory.write_entry(
                        "patterns",
                        f"p_int_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        {
                            "type": "behavior",
                            "pattern": f"Intenção recorrente: {text[:100]}",
                            "occurrences": count,
                            "source": "intention_tracking",
                            "created_at": ts,
                        },
                        meta={"relevance": "high", "source": "extraction"},
                    )


def _check_action_results():
    try:
        from state import read_state
        state = read_state()
    except ImportError:
        return

    results = state.get("results", {})
    for result_id, result in results.items():
        status = result.get("status", "")
        action_id = result.get("action_id", "")
        error = result.get("error", "")
        ts = result.get("executed_at", "")

        if status == "error" and error:
            count = _increment_event("error", error[:100])
            if count == 1:
                ahri_memory.write_entry(
                    "learnings",
                    f"l_err_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    {
                        "type": "error",
                        "action_id": action_id,
                        "error": error[:200],
                        "occurrences": count,
                        "source": "executor_result",
                        "created_at": ts,
                    },
                    meta={"relevance": "high", "source": "extraction"},
                )
            elif count >= 3:
                existing = ahri_memory.search_entries("patterns", error[:50])
                if not existing:
                    ahri_memory.write_entry(
                        "patterns",
                        f"ap_err_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        {
                            "type": "anti_pattern",
                            "pattern": f"Erro recorrente: {error[:100]}",
                            "occurrences": count,
                            "source": "error_tracking",
                            "created_at": ts,
                        },
                        meta={"relevance": "high", "source": "extraction"},
                    )


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------

def consolidate():
    # Deduplicate learnings
    learnings = ahri_memory.list_entries("learnings")
    seen = {}
    for learning in learnings:
        lid = learning.get("id", "")
        summary = learning.get("summary", learning.get("error", ""))[:100]
        if summary in seen:
            ahri_memory.delete_entry("learnings", lid)
        else:
            seen[summary] = lid

    # Prune stale candidates (>30 days without confirmation)
    _prune_stale_candidates()

    # Run maintenance (TTL pruning)
    ahri_memory.maintenance()


def _prune_stale_candidates(max_days: int = 30):
    cutoff = datetime.now() - timedelta(days=max_days)

    for entry_type in ("decisions", "learnings"):
        entries = ahri_memory.list_entries(entry_type)
        for entry in entries:
            if entry.get("status") != "candidate":
                continue
            created = entry.get("created_at", "")
            if not created:
                continue
            try:
                created_dt = datetime.fromisoformat(created)
                if created_dt < cutoff:
                    ahri_memory.delete_entry(entry_type, entry.get("id", ""))
            except (ValueError, TypeError):
                pass


# ---------------------------------------------------------------------------
# Cycle (called by scheduler cron)
# ---------------------------------------------------------------------------

def extraction_cycle():
    extract_from_sessions()
    consolidate()


if __name__ == "__main__":
    print("Extraction pipeline rodando... (Ctrl+C para parar)")
    import time
    while True:
        try:
            extraction_cycle()
        except Exception as e:
            print(f"Erro no ciclo: {e}")
        time.sleep(60)