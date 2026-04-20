import json
import os
import sys
from pathlib import Path

# Ahri memory repo (persistent, versioned)
AHRI_MEMORY_DIR = Path(os.environ.get("AHRI_MEMORY_DIR", str(Path(__file__).parent.parent / "ahri")))

if str(AHRI_MEMORY_DIR) not in sys.path:
    sys.path.insert(0, str(AHRI_MEMORY_DIR))

CONFIG_PATH = AHRI_MEMORY_DIR / "core" / "system_config.json"


def _ensure_config():
    AHRI_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    (AHRI_MEMORY_DIR / "core").mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        _defaults = {
            "crons": {
                "executor": {"interval_seconds": 10, "status": "active"},
                "intent_resolver": {"interval_seconds": 5, "status": "active"},
                "calendar_check": {"interval_seconds": 300, "status": "active"},
                "integration_health": {"interval_seconds": 600, "status": "active"},
                "overdue_tasks": {"interval_seconds": 900, "status": "active"},
                "telegram_poll": {"interval_seconds": 5, "status": "active"},
                "audit_check": {"interval_seconds": 60, "status": "active"},
                "proactivity_digest": {"interval_seconds": 1800, "status": "active"},
            },
            "llm": {
                "current_model": "gpt-4o-mini",
                "current_provider": "openrouter",
                "agent_model": "gpt-4o-mini",
                "available_models": [],
            },
            "auto_approved_patterns": [
                {"tool": "gmail_list", "params": {}},
                {"tool": "calendar_today", "params": {}},
                {"tool": "calendar_list", "params": {}},
                {"tool": "drive_list", "params": {}},
                {"tool": "trello_get_boards", "params": {}},
                {"tool": "trello_get_lists", "params": {}},
                {"tool": "trello_get_cards", "params": {}},
                {"tool": "trello_get_labels", "params": {}},
                {"tool": "trello_test", "params": {}},
                {"tool": "supabase_select", "params": {}},
                {"tool": "supabase_health", "params": {}},
            ],
            "modules": {},
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(_defaults, f, indent=2, ensure_ascii=False)
        return _defaults

    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def read_config() -> dict:
    return _ensure_config()


def write_config(data: dict):
    AHRI_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    (AHRI_MEMORY_DIR / "core").mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_crons_config() -> dict:
    return read_config().get("crons", {})


def get_llm_config() -> dict:
    return read_config().get("llm", {})


def get_auto_approved_patterns() -> list:
    return read_config().get("auto_approved_patterns", [])


def get_modules_config() -> dict:
    return read_config().get("modules", {})