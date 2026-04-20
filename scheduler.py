import os
import sys
import json
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = str(Path(__file__).parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from state import read_state, write_state, merge_state
from executor import create_action, approve_action, executor_cycle
from agents.ahri import (
    send_notification, check_upcoming_events,
    check_integration_health, check_overdue_tasks,
    telegram_send, telegram_get_updates, handle_telegram_update,
    is_audit_active, stop_audit,
)
from intent_resolver import intent_resolver_cycle

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")


# ---------------------------------------------------------------------------
# Cron definitions
# ---------------------------------------------------------------------------

def _register_default_crons():
    state = read_state()
    crons = state.setdefault("crons", {})

    defaults = {
        "executor": {"interval_seconds": 10, "function": "executor_cycle", "status": "active"},
        "intent_resolver": {"interval_seconds": 5, "function": "intent_resolver_cycle", "status": "active"},
        "calendar_check": {"interval_seconds": 300, "function": "check_upcoming_events", "status": "active"},
        "integration_health": {"interval_seconds": 600, "function": "check_integration_health", "status": "active"},
        "overdue_tasks": {"interval_seconds": 900, "function": "check_overdue_tasks", "status": "active"},
        "telegram_poll": {"interval_seconds": 5, "function": "telegram_poll_cycle", "status": "active"},
        "audit_check": {"interval_seconds": 60, "function": "audit_expiry_check", "status": "active"},
        "proactivity_digest": {"interval_seconds": 1800, "function": "flush_digest", "status": "active"},
    }

    changed = False
    for name, config in defaults.items():
        if name not in crons:
            crons[name] = {**config, "last_run_at": "", "run_count": 0}
            changed = True

    if changed:
        write_state(state, agent="scheduler", reason="register_default_crons")


# ---------------------------------------------------------------------------
# Cron runner
# ---------------------------------------------------------------------------

_last_run = {}


def _should_run(cron_name: str, interval_seconds: int) -> bool:
    last = _last_run.get(cron_name, 0)
    now = time.time()
    if now - last >= interval_seconds:
        _last_run[cron_name] = now
        return True
    return False


def _update_cron_state(cron_name: str):
    state = read_state()
    cron = state.get("crons", {}).get(cron_name, {})
    cron["last_run_at"] = datetime.now().isoformat()
    cron["run_count"] = cron.get("run_count", 0) + 1
    write_state(state, agent="scheduler", reason=f"cron_{cron_name}")


# ---------------------------------------------------------------------------
# Cron functions
# ---------------------------------------------------------------------------

def cron_executor_cycle():
    if _should_run("executor", 10):
        try:
            executor_cycle()
        except Exception as e:
            pass
        _update_cron_state("executor")


def cron_intent_resolver():
    if _should_run("intent_resolver", 5):
        try:
            intent_resolver_cycle()
        except Exception:
            pass
        _update_cron_state("intent_resolver")


def cron_calendar_check():
    if _should_run("calendar_check", 300):
        try:
            check_upcoming_events()
        except Exception:
            pass
        _update_cron_state("calendar_check")


def cron_integration_health():
    if _should_run("integration_health", 600):
        try:
            check_integration_health()
        except Exception:
            pass
        _update_cron_state("integration_health")


def cron_overdue_tasks():
    if _should_run("overdue_tasks", 900):
        try:
            check_overdue_tasks()
        except Exception:
            pass
        _update_cron_state("overdue_tasks")


def cron_telegram_poll():
    if _should_run("telegram_poll", 5):
        try:
            telegram_poll_cycle()
        except Exception:
            pass
        _update_cron_state("telegram_poll")


def cron_audit_check():
    if _should_run("audit_check", 60):
        try:
            audit_expiry_check()
        except Exception:
            pass
        _update_cron_state("audit_check")


def cron_proactivity_digest():
    if _should_run("proactivity_digest", 1800):
        try:
            flush_digest()
        except Exception:
            pass
        _update_cron_state("proactivity_digest")


# ---------------------------------------------------------------------------
# Implementation functions
# ---------------------------------------------------------------------------

_last_update_id = 0


def telegram_poll_cycle():
    global _last_update_id
    updates = telegram_get_updates(offset=_last_update_id + 1)
    for update in updates:
        _last_update_id = update.get("update_id", _last_update_id)
        handle_telegram_update(update)


def audit_expiry_check():
    state = read_state()
    if state.get("ahri", {}).get("audit_mode"):
        if is_audit_active(state):
            return
        send_notification("Modo auditoria expirou. Voltando ao normal.", priority="normal")


def flush_digest():
    state = read_state()
    digest = state.get("proactivity", {}).get("pending_digest", [])
    if not digest:
        return

    msg = f"Atualizacoes acumuladas ({len(digest)}):\n" + "\n".join(f"- {d}" for d in digest[:5])
    telegram_send(msg)

    state.setdefault("proactivity", {})["pending_digest"] = []
    write_state(state, agent="scheduler", reason="digest_flushed")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run():
    _register_default_crons()
    print("OpenClaw Scheduler rodando... (Ctrl+C para parar)")
    print("Crons ativos: executor(10s), intent_resolver(5s), telegram(5s), calendar(5min), health(10min), tasks(15min), digest(30min)")

    while True:
        cron_executor_cycle()
        cron_intent_resolver()
        cron_telegram_poll()
        cron_audit_check()
        cron_calendar_check()
        cron_integration_health()
        cron_overdue_tasks()
        cron_proactivity_digest()
        time.sleep(1)


if __name__ == "__main__":
    run()