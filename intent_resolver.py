import json
import os
import sys
import uuid
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = str(Path(__file__).parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from state import read_state, write_state
from tools.registry import TOOL_REGISTRY, get_tool

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# LLM config
# ---------------------------------------------------------------------------

RESOLVER_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
RESOLVER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
RESOLVER_MODEL = os.environ.get("RESOLVER_MODEL", os.environ.get("LLM_MODEL", "gpt-4o-mini"))

RESOLVER_SYSTEM_PROMPT = """Voce e o intent_resolver do OpenClaw.
Sua funcao e traduzir intencoes em linguagem natural para acoes estruturadas.

Voce recebe:
- O texto da intenção (linguagem natural)
- A lista de tools disponiveis com nome, descricao e categoria

Voce responde APENAS com JSON, sem texto antes ou depois:
- Se consegue mapear para exatamente UMA tool: {"tool": "nome_da_tool", "params": {"key": "value"}, "confidence": "high"|"medium"|"low"}
- Se a intenção e ambígua (cabe em mais de uma tool ou falta informacao): {"tool": null, "ambiguity": "descricao da ambiguidade", "candidates": ["tool1", "tool2"], "confidence": "low"}
- Se nao ha tool que atenda: {"tool": null, "unresolvable": true, "reason": "motivo"}

Regras:
- So use tools que estao na lista fornecida
- Nao invente nomes de tools
- Se falta parametro essencial, marque como ambíguo
- confidence "high" = certeza razoavel, "medium" = provavel mas incerto, "low" = chute
- Params devem ser strings, nao invente valores que o usuario nao forneceu
"""


def _resolver_llm_call(messages: list) -> str:
    if not RESOLVER_API_KEY:
        return '{"tool": null, "unresolvable": true, "reason": "sem API key"}'

    body = json.dumps({
        "model": RESOLVER_MODEL,
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.2,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RESOLVER_API_KEY}",
    }
    if "openrouter" in RESOLVER_BASE_URL:
        headers["HTTP-Referer"] = "https://openclaw.local"
        headers["X-Title"] = "OpenClaw IntentResolver"

    req = urllib.request.Request(
        f"{RESOLVER_BASE_URL}/chat/completions",
        data=body,
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f'{{"tool": null, "unresolvable": true, "reason": "llm_error: {e}"}}'


def _build_tools_catalog() -> str:
    lines = []
    for name, info in TOOL_REGISTRY.items():
        lines.append(f"- {name}: {info['description']} (categoria: {info['category']}, requer aprovacao: {info['requires_approval']})")
    return "\n".join(lines)


def _parse_resolver_response(raw: str) -> dict:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"tool": None, "unresolvable": True, "reason": f"json_parse_error: {raw[:200]}"}


# ---------------------------------------------------------------------------
# Core: resolve a single intention
# ---------------------------------------------------------------------------

def resolve_intention(intention: dict) -> dict:
    text = intention.get("text", "")
    if not text:
        return {"status": "unresolvable", "reason": "empty_text"}

    tools_catalog = _build_tools_catalog()

    messages = [
        {"role": "system", "content": RESOLVER_SYSTEM_PROMPT},
        {"role": "user", "content": f"Intencao: {text}\n\nTools disponiveis:\n{tools_catalog}"},
    ]

    raw = _resolver_llm_call(messages)
    result = _parse_resolver_response(raw)

    return result


# ---------------------------------------------------------------------------
# Cycle: process all pending intentions from state
# ---------------------------------------------------------------------------

def intent_resolver_cycle():
    state = read_state()
    intentions = state.get("intentions", [])
    changed = False

    for intention in intentions:
        if intention.get("status") != "pending":
            continue

        result = resolve_intention(intention)

        if result.get("unresolvable"):
            intention["status"] = "unresolvable"
            intention["resolved_at"] = datetime.now().isoformat()
            intention["resolution_reason"] = result.get("reason", "unknown")
            changed = True
            continue

        tool_name = result.get("tool")
        if not tool_name:
            # Ambiguous
            intention["status"] = "ambiguous"
            intention["resolved_at"] = datetime.now().isoformat()
            intention["ambiguity"] = result.get("ambiguity", "")
            intention["candidates"] = result.get("candidates", [])
            intention["confidence"] = result.get("confidence", "low")
            changed = True
            continue

        # Validate tool exists
        tool_def = get_tool(tool_name)
        if not tool_def:
            intention["status"] = "unresolvable"
            intention["resolved_at"] = datetime.now().isoformat()
            intention["resolution_reason"] = f"tool_not_found: {tool_name}"
            changed = True
            continue

        confidence = result.get("confidence", "low")
        if confidence == "low":
            intention["status"] = "ambiguous"
            intention["resolved_at"] = datetime.now().isoformat()
            intention["ambiguity"] = f"Baixa confianca na resolucao (tool: {tool_name})"
            intention["candidates"] = [tool_name]
            intention["confidence"] = confidence
            changed = True
            continue

        # High/medium confidence — create action in state
        params = result.get("params", {})
        try:
            from executor import create_action
            action_id = create_action(tool_name, params=params, source="intent_resolver")
            intention["status"] = "resolved"
            intention["resolved_at"] = datetime.now().isoformat()
            intention["resolved_action_id"] = action_id
            changed = True
        except ValueError as e:
            intention["status"] = "unresolvable"
            intention["resolved_at"] = datetime.now().isoformat()
            intention["resolution_reason"] = str(e)
            changed = True

    # Cleanup: remove resolved/unresolvable intentions older than 1 hour
    now = datetime.now()
    still_active = []
    for intention in intentions:
        terminal = intention.get("status") in ("resolved", "unresolvable")
        if terminal:
            resolved_at = intention.get("resolved_at", "")
            if resolved_at:
                try:
                    elapsed = (now - datetime.fromisoformat(resolved_at)).total_seconds()
                    if elapsed > 3600:
                        continue
                except (ValueError, TypeError):
                    pass
        still_active.append(intention)

    state["intentions"] = still_active

    if changed:
        write_state(state, agent="intent_resolver", reason="cycle_completed")


# ---------------------------------------------------------------------------
# Helpers (used by other modules via state, not direct import)
# ---------------------------------------------------------------------------

def get_ambiguous_intentions() -> list:
    state = read_state()
    return [i for i in state.get("intentions", []) if i.get("status") == "ambiguous"]


def resolve_ambiguity(intention_id: str, chosen_tool: str, params: dict = None) -> str:
    state = read_state()
    for intention in state.get("intentions", []):
        if intention.get("id") == intention_id and intention.get("status") == "ambiguous":
            tool_def = get_tool(chosen_tool)
            if not tool_def:
                return f"Tool nao encontrada: {chosen_tool}"

            from executor import create_action
            action_id = create_action(chosen_tool, params=params or {}, source="intent_resolver")
            intention["status"] = "resolved"
            intention["resolved_at"] = datetime.now().isoformat()
            intention["resolved_action_id"] = action_id
            write_state(state, agent="intent_resolver", reason=f"ambiguity_resolved_{intention_id}")
            return action_id

    return "Intencao nao encontrada ou nao esta ambígua"


if __name__ == "__main__":
    print("Intent Resolver rodando... (Ctrl+C para parar)")
    while True:
        try:
            intent_resolver_cycle()
        except Exception as e:
            print(f"Erro no ciclo: {e}")
        import time
        time.sleep(5)