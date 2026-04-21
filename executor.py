import json
import os
import sys
import time
import uuid
import importlib
from datetime import datetime, timedelta
from pathlib import Path

ROOT = str(Path(__file__).parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from state import read_state, write_state, merge_state, update_state
from tools.registry import TOOL_REGISTRY, get_tool

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

STALE_SECONDS = 60
CLEANUP_HOURS = 24
RESULT_TTL_DAYS = 7


def _now() -> str:
    return datetime.now().isoformat()


def _is_stale(action: dict) -> bool:
    executed = action.get("executed_at")
    if not executed:
        return False
    try:
        elapsed = (datetime.now() - datetime.fromisoformat(executed)).total_seconds()
        return elapsed > STALE_SECONDS
    except (ValueError, TypeError):
        return True


def _is_approval_expired(action: dict) -> bool:
    expires = action.get("approval_expires_at")
    if not expires:
        return False
    try:
        return datetime.now() > datetime.fromisoformat(expires)
    except (ValueError, TypeError):
        return True


def _is_old_completed(action: dict) -> bool:
    executed = action.get("executed_at")
    if not executed:
        return False
    try:
        elapsed = (datetime.now() - datetime.fromisoformat(executed)).total_seconds()
        return elapsed > CLEANUP_HOURS * 3600
    except (ValueError, TypeError):
        return True


def _backoff_delay(retry_count: int) -> float:
    delays = {1: 10, 2: 30, 3: 60}
    return delays.get(retry_count, 60)


def _execute_tool(tool_name: str, params: dict) -> dict:
    tool_def = get_tool(tool_name)
    if not tool_def:
        return {"status": "error", "data": None, "error": f"Tool nao encontrada: {tool_name}"}

    try:
        module = importlib.import_module(tool_def["module"])
        fn = getattr(module, tool_def["function"])
        result = fn(**params)
        return {"status": "success", "data": result, "error": None}
    except Exception as e:
        return {"status": "error", "data": None, "error": str(e)}


def executor_cycle():
    def _mutate(state):
        actions = state.get("pending_actions", [])
        results = state.get("results", {})
        changed = False

        # Process action_requests from intent_resolver
        action_requests = state.pop("action_requests", [])
        for req in action_requests:
            tool_name = req.get("tool")
            params = req.get("params") or {}
            source = req.get("source", "intent_resolver")
            priority = req.get("priority", "normal")
            requires_approval = req.get("requires_approval", None)
            tool_def = get_tool(tool_name)
            if not tool_def:
                continue
            if requires_approval is None:
                requires_approval = tool_def["requires_approval"]
            action_id = f"act_{uuid.uuid4().hex[:8]}"
            result_id = f"res_{action_id}"
            action = {
                "id": action_id,
                "source": source,
                "tool": tool_name,
                "params": params,
                "status": "pending_approval" if requires_approval else "pending",
                "requires_approval": requires_approval,
                "created_at": _now(),
                "approved_at": None,
                "approved_by": None,
                "executed_at": None,
                "result_ref": result_id,
                "retry_count": 0,
                "max_retries": 3,
                "timeout_seconds": 30,
                "approval_expires_at": (datetime.now() + timedelta(minutes=30)).isoformat() if requires_approval else None,
                "priority": priority,
            }
            actions.append(action)
            changed = True

        for action in actions:
            status = action.get("status")

            if status == "running" and _is_stale(action):
                action["status"] = "failed"
                action["retry_count"] = action.get("retry_count", 0) + 1
                result_id = action.get("result_ref", f"res_{action['id']}")
                results[result_id] = {
                    "action_id": action["id"], "status": "error", "data": None,
                    "error": "executor_crash_detected", "executed_at": _now(), "execution_time_ms": 0,
                }
                changed = True
                continue

            if status == "pending_approval" and _is_approval_expired(action):
                action["status"] = "expired"
                changed = True
                continue

            if status in ("pending", "approved"):
                tool_def = get_tool(action.get("tool", ""))
                if not tool_def:
                    action["status"] = "failed_permanent"
                    result_id = action.get("result_ref", f"res_{action['id']}")
                    results[result_id] = {
                        "action_id": action["id"], "status": "error", "data": None,
                        "error": f"tool_not_found: {action.get('tool')}", "executed_at": _now(), "execution_time_ms": 0,
                    }
                    changed = True
                    continue

                action["status"] = "running"
                action["executed_at"] = _now()
                changed = True

                start = time.time()
                result = _execute_tool(action["tool"], action.get("params", {}))
                elapsed_ms = int((time.time() - start) * 1000)

                result_id = action.get("result_ref", f"res_{action['id']}")
                results[result_id] = {
                    "action_id": action["id"], "status": result["status"], "data": result["data"],
                    "error": result["error"], "executed_at": _now(), "execution_time_ms": elapsed_ms,
                }

                # Check for integration status in result
                if "_integration_status" in result.get("data", {}) or "_integration_status" in result:
                    int_status = result.get("data", {}).get("_integration_status") or result.get("_integration_status")
                    if int_status and isinstance(int_status, dict):
                        tool_domain = action.get("tool", "").split("_")[0]
                        state.setdefault("integrations", {})
                        state["integrations"][tool_domain] = int_status

                if result["status"] == "success":
                    action["status"] = "done"
                else:
                    action["retry_count"] = action.get("retry_count", 0) + 1
                    action["status"] = "failed"
                changed = True

            if action.get("status") == "failed" and action.get("retry_count", 0) < action.get("max_retries", 3):
                action["status"] = "retrying"

            if action.get("status") == "failed" and action.get("retry_count", 0) >= action.get("max_retries", 3):
                action["status"] = "failed_permanent"
                state.setdefault("intentions", []).append({
                    "id": f"int_{uuid.uuid4().hex[:8]}",
                    "text": f"Notificar: acao {action['id']} ({action.get('tool')}) falhou permanentemente",
                    "source": "executor", "status": "pending", "created_at": _now(),
                })
                changed = True

        # Cleanup old completed actions
        still_active = []
        for action in actions:
            if action.get("status") in ("done", "rejected", "expired", "failed_permanent"):
                if _is_old_completed(action):
                    rid = action.get("result_ref", "")
                    results.pop(rid, None)
                    continue
            still_active.append(action)

        state["pending_actions"] = still_active
        state["results"] = results

    update_state(_mutate, agent="executor", reason="cycle_completed")


def create_action(tool_name: str, params: dict = None,
                  source: str = "ahri", priority: str = "normal",
                  requires_approval: bool = None) -> str:
    tool_def = get_tool(tool_name)
    if not tool_def:
        raise ValueError(f"Tool nao registrada: {tool_name}")

    if requires_approval is None:
        requires_approval = tool_def["requires_approval"]

    action_id = f"act_{uuid.uuid4().hex[:8]}"
    result_id = f"res_{action_id}"

    action = {
        "id": action_id,
        "source": source,
        "tool": tool_name,
        "params": params or {},
        "status": "pending_approval" if requires_approval else "pending",
        "requires_approval": requires_approval,
        "created_at": _now(),
        "approved_at": None,
        "approved_by": None,
        "executed_at": None,
        "result_ref": result_id,
        "retry_count": 0,
        "max_retries": 3,
        "timeout_seconds": 30,
        "approval_expires_at": None,
        "priority": priority,
    }

    if requires_approval:
        action["approval_expires_at"] = (datetime.now() + timedelta(minutes=30)).isoformat()

    def _mutate(state):
        state.setdefault("pending_actions", []).append(action)

    update_state(_mutate, agent=source, reason=f"action_created_{tool_name}")
    return action_id


def approve_action(action_id: str, approved_by: str = "user") -> bool:
    found = False

    def _mutate(state):
        nonlocal found
        for action in state.get("pending_actions", []):
            if action.get("id") == action_id and action.get("status") == "pending_approval":
                action["status"] = "approved"
                action["approved_at"] = _now()
                action["approved_by"] = approved_by
                found = True
                return

    update_state(_mutate, agent="user", reason=f"approved_{action_id}")
    return found


def reject_action(action_id: str, rejected_by: str = "user") -> bool:
    found = False

    def _mutate(state):
        nonlocal found
        for action in state.get("pending_actions", []):
            if action.get("id") == action_id and action.get("status") == "pending_approval":
                action["status"] = "rejected"
                found = True
                return

    update_state(_mutate, agent="user", reason=f"rejected_{action_id}")
    return found


def get_pending_approvals() -> list:
    state = read_state()
    return [a for a in state.get("pending_actions", [])
            if a.get("status") == "pending_approval"]


def get_action_result(action_id: str) -> dict:
    state = read_state()
    for action in state.get("pending_actions", []):
        if action.get("id") == action_id:
            result_ref = action.get("result_ref", "")
            return state.get("results", {}).get(result_ref, {})
    return {}


if __name__ == "__main__":
    print("Executor rodando... (Ctrl+C para parar)")
    while True:
        try:
            executor_cycle()
        except Exception as e:
            print(f"Erro no ciclo: {e}")
        time.sleep(10)