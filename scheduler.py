import os
import json
import time
import importlib
from datetime import datetime
from pathlib import Path

from state import read_state, write_state, merge_state, update_state

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Cron registry — discovered from state, not hardcoded
# ---------------------------------------------------------------------------

DEFAULT_CRONS = {
    "executor": {
        "interval_seconds": 10,
        "module": "executor",
        "function": "executor_cycle",
        "status": "active",
    },
    "intent_resolver": {
        "interval_seconds": 5,
        "module": "intent_resolver",
        "function": "intent_resolver_cycle",
        "status": "active",
    },
    "telegram_poll": {
        "interval_seconds": 5,
        "module": "agents.ahri",
        "function": "telegram_poll_cycle",
        "status": "active",
    },
    "audit_check": {
        "interval_seconds": 60,
        "module": "scheduler",
        "function": "audit_expiry_check",
        "status": "active",
    },
    "calendar_check": {
        "interval_seconds": 300,
        "module": "scheduler",
        "function": "check_upcoming_events",
        "status": "active",
    },
    "integration_health": {
        "interval_seconds": 600,
        "module": "scheduler",
        "function": "check_integration_health",
        "status": "active",
    },
    "overdue_tasks": {
        "interval_seconds": 900,
        "module": "scheduler",
        "function": "check_overdue_tasks",
        "status": "active",
    },
    "proactivity_digest": {
        "interval_seconds": 1800,
        "module": "scheduler",
        "function": "flush_digest",
        "status": "active",
    },
    "extraction": {
        "interval_seconds": 300,
        "module": "extraction",
        "function": "extraction_cycle",
        "status": "active",
    },
}


def _register_default_crons():
    def _mutate(state):
        crons = state.setdefault("cron_runtime", {})
        for name, config in DEFAULT_CRONS.items():
            if name not in crons:
                crons[name] = {**config, "last_run_at": "", "run_count": 0}

    update_state(_mutate, agent="scheduler", reason="register_default_crons")


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


def _update_cron_runtime(cron_name: str):
    merge_state({
        "cron_runtime": {
            cron_name: {
                "last_run_at": datetime.now().isoformat(),
                "run_count": 1
            }
        }
    }, agent="scheduler", reason=f"cron_{cron_name}")


def _run_cron_function(module_name: str, function_name: str):
    try:
        mod = importlib.import_module(module_name)
        fn = getattr(mod, function_name)
        fn()
    except Exception as e:
        pass


# ---------------------------------------------------------------------------
# Built-in scheduler functions
# ---------------------------------------------------------------------------

def _now():
    return datetime.now().isoformat()

def audit_expiry_check():
    state = read_state()
    if state.get("ahri_runtime", {}).get("audit_mode"):
        expires = state["ahri_runtime"].get("audit_expires_at")
        if expires:
            try:
                if datetime.now() > datetime.fromisoformat(expires):
                    merge_state({"ahri_runtime": {"audit_mode": False, "audit_scope": None, "audit_expires_at": None}},
                                agent="scheduler", reason="audit_expired")
                    merge_state({"notifications": [{"text": "Modo auditoria expirou. Voltando ao normal.", "priority": "normal", "created_at": _now()}]},
                                agent="scheduler", reason="audit_expired_notification")
            except (ValueError, TypeError):
                pass


def flush_digest():
    state = read_state()
    digest = state.get("proactivity", {}).get("pending_digest", [])
    if not digest:
        return

    merge_state({"notifications": [{"text": f"Atualizacoes acumuladas ({len(digest)}): " + ", ".join(str(d) for d in digest[:5]), "priority": "normal", "created_at": _now()}]},
                agent="scheduler", reason="digest_notification")
    merge_state({"proactivity": {"pending_digest": []}}, agent="scheduler", reason="digest_flushed")


def check_upcoming_events():
    def _mutate(state):
        state.setdefault("action_requests", []).append({
            "tool": "calendar_today",
            "params": {},
            "source": "proactive",
            "priority": "alta",
        })
    update_state(_mutate, agent="scheduler", reason="proactive_calendar_check")


def check_integration_health():
    def _mutate(state):
        for tool_name in ("trello_test", "supabase_health"):
            state.setdefault("action_requests", []).append({
                "tool": tool_name,
                "params": {},
                "source": "proactive",
                "priority": "normal",
            })
    update_state(_mutate, agent="scheduler", reason="proactive_integration_check")


def check_overdue_tasks():
    try:
        from memory_context import read_context
        tasks = read_context("tasks")
    except ImportError:
        return

    if not tasks or not isinstance(tasks, dict):
        return

    overdue = []
    now = datetime.now()
    for task_id, task in tasks.items():
        if not isinstance(task, dict):
            continue
        due = task.get("due_time") or task.get("due_date")
        if due and task.get("status") not in ("done", "complete"):
            try:
                if datetime.fromisoformat(due) < now:
                    overdue.append({"id": task_id, "due": due})
            except (ValueError, TypeError):
                pass

    if overdue:
        msg = f"Chefe, {len(overdue)} tarefa(s) vencida(s): " + ", ".join(t["id"] for t in overdue)
        merge_state({"notifications": [{"text": msg, "priority": "alta", "created_at": _now()}]},
                    agent="scheduler", reason="overdue_tasks_notification")


# ---------------------------------------------------------------------------
# Main loop — discovers and runs crons dynamically from state
# ---------------------------------------------------------------------------

def run():
    _register_default_crons()
    print("OpenClaw Scheduler rodando... (Ctrl+C para parar)")

    state = read_state()
    active_crons = {k: v for k, v in state.get("cron_runtime", {}).items() if v.get("status") == "active"}
    names = ", ".join(f"{k}({v.get('interval_seconds', '?')}s)" for k, v in active_crons.items())
    print(f"Crons ativos: {names}")

    while True:
        state = read_state()
        crons = state.get("cron_runtime", {})

        for cron_name, cron_config in crons.items():
            if cron_config.get("status") != "active":
                continue

            interval = cron_config.get("interval_seconds", 60)
            if not _should_run(cron_name, interval):
                continue

            module_name = cron_config.get("module", "")
            function_name = cron_config.get("function", "")

            if module_name and function_name:
                _run_cron_function(module_name, function_name)

            _update_cron_runtime(cron_name)

        time.sleep(1)


if __name__ == "__main__":
    run()