import os
import sys
import json
import time
import importlib
from datetime import datetime
from pathlib import Path

ROOT = str(Path(__file__).parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from state import read_state, write_state

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
        "module": "agents.ahri",
        "function": "audit_expiry_check",
        "status": "active",
    },
    "calendar_check": {
        "interval_seconds": 300,
        "module": "agents.ahri",
        "function": "check_upcoming_events",
        "status": "active",
    },
    "integration_health": {
        "interval_seconds": 600,
        "module": "agents.ahri",
        "function": "check_integration_health",
        "status": "active",
    },
    "overdue_tasks": {
        "interval_seconds": 900,
        "module": "agents.ahri",
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
    state = read_state()
    crons = state.setdefault("cron_runtime", {})

    changed = False
    for name, config in DEFAULT_CRONS.items():
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


def _update_cron_runtime(cron_name: str):
    state = read_state()
    cron = state.get("cron_runtime", {}).get(cron_name, {})
    cron["last_run_at"] = datetime.now().isoformat()
    cron["run_count"] = cron.get("run_count", 0) + 1
    write_state(state, agent="scheduler", reason=f"cron_{cron_name}")


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

def audit_expiry_check():
    from agents.ahri import is_audit_active, send_notification
    state = read_state()
    if state.get("ahri_runtime", {}).get("audit_mode"):
        if is_audit_active(state):
            return
        send_notification("Modo auditoria expirou. Voltando ao normal.", priority="normal")


def flush_digest():
    from agents.ahri import telegram_send
    state = read_state()
    digest = state.get("proactivity", {}).get("pending_digest", [])
    if not digest:
        return

    msg = f"Atualizacoes acumuladas ({len(digest)}):\n" + "\n".join(f"- {d}" for d in digest[:5])
    telegram_send(msg)

    state = read_state()
    state.setdefault("proactivity", {})["pending_digest"] = []
    write_state(state, agent="scheduler", reason="digest_flushed")


def check_upcoming_events():
    from executor import create_action
    create_action("calendar_today", source="ahri_proactive", priority="alta")


def check_integration_health():
    from executor import create_action
    from tools.registry import get_tool
    for tool_name in ("trello_test", "supabase_health"):
        if get_tool(tool_name):
            try:
                create_action(tool_name, source="ahri_proactive", priority="normal")
            except Exception:
                pass


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
        from agents.ahri import send_notification
        msg = f"Chefe, {len(overdue)} tarefa(s) vencida(s): " + ", ".join(t["id"] for t in overdue)
        send_notification(msg, priority="alta")


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