import os
import sys
import json
import uuid
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from state import read_state, write_state, merge_state, update_state
from fast_patterns import try_fast_resolve

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# LLM config
# ---------------------------------------------------------------------------

LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
LLM_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """Voce e a Ahri — HQ conversacional do OpenClaw.
Voce e a assistente pessoal do Felipe. Responde com base no estado real do sistema.

Regras:
- Nunca invente dados. Se nao ha informacao no estado, diga que nao tem.
- Responda em portugues brasileiro, de forma direta e util.
- Quando o Chefe pedir algo operacional (que envolva tools do sistema), voce IDENTIFICA a intenção e responde naturalmente. Nao use comandos estruturados.
- Para acoes de leitura (listar emails, ver agenda), responda que vai verificar.
- Para acoes de escrita (criar card, enviar email), informe que vai registrar e precisa de autorizacao.
- Sempre que possivel, aja: nao so informe, identifique intenção operacional.
- Voce pode ser proativa: alertar sobre eventos proximos, falhas, tarefas vencidas.
- Maximo 2 observacoes proativas por interacao.

Quando identificar uma intenção operacional do Chefe, inclua no formato:
INTENTION:descricao natural da intenção em linguagem simples

Exemplos:
- Chefe: "Verifica meu email" → responda naturalmente + INTENTION:verificar emails recentes
- Chefe: "Cria um card no Trello sobre X" → responda que vai registrar + INTENTION:criar card no Trello sobre X
- Chefe: "Manda email pro cliente" → INTENTION:enviar email para o cliente

Nao estruture a acao. Nao escolha tools. Nao monte parametros. So descreva a intenção.
O sistema resolve a intenção separadamente.
"""

# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def _llm_call(messages: list) -> str:
    if not LLM_API_KEY:
        return "[Sem LLM_API_KEY configurada — modo offline]"

    body = json.dumps({
        "model": LLM_MODEL,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.7,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }
    if "openrouter" in LLM_BASE_URL:
        headers["HTTP-Referer"] = "https://openclaw.local"
        headers["X-Title"] = "OpenClaw"

    req = urllib.request.Request(
        f"{LLM_BASE_URL}/chat/completions",
        data=body,
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Erro LLM: {e}]"


# ---------------------------------------------------------------------------
# Proactivity (reads/writes state only)
# ---------------------------------------------------------------------------

def _can_notify(priority: str, state: dict) -> bool:
    pro = state.get("proactivity", {})
    now = datetime.now()

    if priority == "critica":
        return True

    last_key = f"last_{priority}_at" if priority in ("alta",) else "last_notification_at"
    last_str = pro.get(last_key, "")
    if not last_str:
        return True

    try:
        last = datetime.fromisoformat(last_str)
        if priority == "alta" and (now - last).total_seconds() > 300:
            return True
        if priority in ("normal",) and (now - last).total_seconds() > 1800:
            return True
    except (ValueError, TypeError):
        return True

    return False


def _record_notification(priority: str, state: dict):
    pro = state.setdefault("proactivity", {})
    now = datetime.now().isoformat()
    pro["last_notification_at"] = now
    if priority in ("alta", "critica"):
        pro[f"last_{priority}_at"] = now


def send_notification(text: str, priority: str = "normal", chat_id: str = None) -> bool:
    sent = False

    def _mutate(state):
        nonlocal sent
        if not _can_notify(priority, state):
            if priority in ("normal", "baixa"):
                state.setdefault("proactivity", {}).setdefault("pending_digest", []).append(text)
                return
        _record_notification(priority, state)
        sent = True

    update_state(_mutate, agent="ahri", reason="notification_check")

    if sent:
        return telegram_send(text, chat_id)
    return False


# ---------------------------------------------------------------------------
# Telegram (I/O only — no state mutation beyond what send_notification does)
# ---------------------------------------------------------------------------

def telegram_send(text: str, chat_id: str = None) -> bool:
    if not TELEGRAM_TOKEN:
        return False
    chat = chat_id or TELEGRAM_CHAT_ID
    if not chat:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    body = json.dumps({"chat_id": chat, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def telegram_get_updates(offset: int = 0) -> list:
    if not TELEGRAM_TOKEN:
        return []

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result", [])
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Approval handling — reads/writes state only
# ---------------------------------------------------------------------------

def _parse_approval(text: str):
    text = text.strip()
    if text.startswith("/approve "):
        return ("approve", text.split()[1])
    if text.startswith("/reject "):
        return ("reject", text.split()[1])
    return None, None


def _approve_via_state(action_id: str, approved_by: str) -> bool:
    found = False

    def _mutate(state):
        nonlocal found
        for action in state.get("pending_actions", []):
            if action.get("id") == action_id and action.get("status") == "pending_approval":
                action["status"] = "approved"
                action["approved_at"] = datetime.now().isoformat()
                action["approved_by"] = approved_by
                found = True
                return

    update_state(_mutate, agent="user", reason=f"approved_{action_id}")
    return found


def _reject_via_state(action_id: str, rejected_by: str) -> bool:
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


# ---------------------------------------------------------------------------
# Intention registration — writes to state only
# ---------------------------------------------------------------------------

def _register_intention_via_state(text: str, source: str = "ahri", context: dict = None) -> str:
    intention_id = f"int_{uuid.uuid4().hex[:8]}"
    intention = {
        "id": intention_id,
        "text": text,
        "source": source,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "resolved_at": None,
        "resolved_action_id": None,
        "ambiguity": None,
        "candidates": [],
        "confidence": None,
        "resolution_reason": None,
    }
    if context:
        intention["context"] = context

    def _mutate(state):
        state.setdefault("intentions", []).append(intention)

    update_state(_mutate, agent=source, reason=f"intention_registered_{intention_id}")

    return intention_id


def _get_ambiguous_intentions() -> list:
    state = read_state()
    return [i for i in state.get("intentions", []) if i.get("status") == "ambiguous"]


# ---------------------------------------------------------------------------
# Telegram update handler — all communication via state
# ---------------------------------------------------------------------------

def handle_telegram_update(update: dict):
    text = update.get("message", {}).get("text", "")
    chat_id = str(update.get("message", {}).get("chat", {}).get("id", ""))

    if TELEGRAM_CHAT_ID and chat_id != TELEGRAM_CHAT_ID:
        return

    action_type, action_id = _parse_approval(text)
    if action_type == "approve":
        if _approve_via_state(action_id, approved_by=f"telegram_{chat_id}"):
            telegram_send("Acao aprovada. Executando...", chat_id)
        else:
            telegram_send("Acao nao encontrada ou ja processada.", chat_id)
        return

    if action_type == "reject":
        if _reject_via_state(action_id, rejected_by=f"telegram_{chat_id}"):
            telegram_send("Acao rejeitada.", chat_id)
        else:
            telegram_send("Acao nao encontrada ou ja processada.", chat_id)
        return

    response = ask(text)
    telegram_send(response, chat_id)

    pending = get_pending_approvals()
    if pending:
        lines = ["Acoes pendentes de aprovacao:"]
        for a in pending:
            lines.append(f"  {a['id']}: {a['tool']} — /approve {a['id']} ou /reject {a['id']}")
        telegram_send("\n".join(lines), chat_id)


# ---------------------------------------------------------------------------
# Core: ask() — communicates ONLY via state
# ---------------------------------------------------------------------------

def ask(question: str, state: dict = None) -> str:
    if state is None:
        state = read_state()

    # Fast-path: obvious read-only intents skip the full LLM cycle
    fast = try_fast_resolve(question)
    if fast:
        merge_state({
            "action_requests": [{
                "tool": fast["tool"],
                "params": fast.get("params", {}),
                "source": "ahri_fast",
                "priority": "normal",
                "requires_approval": False,
            }]
        }, agent="ahri", reason="fast_pattern")
        return f"Ok, vou {question.lower().strip('.')}. Um momento..."

    state_summary = _summarize_state(state)
    memory_context = _get_memory_context()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if memory_context:
        messages.append({"role": "system", "content": f"Memoria recente:\n{memory_context}"})

    messages.append({
        "role": "user",
        "content": f"Estado atual:\n{state_summary}\n\nMensagem do Chefe: {question}",
    })

    response = _llm_call(messages)

    # Extract intentions and register via state
    intentions = _extract_intentions(response)

    for intention_text in intentions:
        try:
            _register_intention_via_state(intention_text, source="ahri", context={"question": question[:200]})
        except Exception:
            pass

    # Clean response before showing to user
    response = _strip_intentions(response)

    # Check for ambiguous intentions that need user clarification
    ambiguous = _get_ambiguous_intentions()
    for amb in ambiguous:
        candidates = amb.get("candidates", [])
        amb_text = amb.get("ambiguity", "")
        if candidates:
            response += f"\n\nPreciso esclarecer: {amb_text}. Opcoes: {', '.join(candidates)}. Qual voce quer?"
        else:
            response += f"\n\nNao consegui entender exatamente: {amb_text}. Pode ser mais especifico?"

    # Log to sessions (append-only)
    try:
        from memory_sessions import append_session
        append_session("user", question, metadata={"source": "telegram"})
        append_session("assistant", response, metadata={"source": "ahri"})
    except ImportError:
        pass

    # Update runtime state
    merge_state({"ahri_runtime": {"last_interaction": datetime.now().isoformat()}}, agent="ahri", reason="interaction")

    return response


def ask_for_result(action_id: str) -> str:
    state = read_state()
    for action in state.get("pending_actions", []):
        if action.get("id") == action_id:
            result_ref = action.get("result_ref", "")
            result = state.get("results", {}).get(result_ref, {})
            if not result:
                return "Resultado ainda nao disponivel."
            status = result.get("status", "unknown")
            data = result.get("data")
            error = result.get("error")
            if status == "success" and data:
                return json.dumps(data, ensure_ascii=False, indent=2)
            elif error:
                return f"Erro: {error}"
            else:
                return "Acao ainda em andamento."
    return "Resultado nao encontrado."


# ---------------------------------------------------------------------------
# Audit mode — reads/writes state only
# ---------------------------------------------------------------------------

def start_audit(scope: str, duration_minutes: int = 30):
    merge_state({"ahri_runtime": {
        "audit_mode": True,
        "audit_scope": scope,
        "audit_expires_at": (datetime.now() + timedelta(minutes=duration_minutes)).isoformat()
    }}, agent="user", reason="audit_authorized")


def stop_audit():
    merge_state({"ahri_runtime": {
        "audit_mode": False,
        "audit_scope": None,
        "audit_expires_at": None
    }}, agent="ahri", reason="audit_expired")


def is_audit_active(state: dict = None) -> bool:
    if state is None:
        state = read_state()
    if not state.get("ahri_runtime", {}).get("audit_mode"):
        return False
    expires = state["ahri_runtime"].get("audit_expires_at")
    if expires:
        try:
            if datetime.now() > datetime.fromisoformat(expires):
                stop_audit()
                return False
        except (ValueError, TypeError):
            pass
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _summarize_state(state: dict) -> str:
    lines = []

    integrations = state.get("integrations", {})
    for name, info in integrations.items():
        if isinstance(info, dict):
            lines.append(f"  {name}: {info.get('status', 'unknown')}")

    pending_actions = [a for a in state.get("pending_actions", []) if a.get("status") in ("pending", "pending_approval", "approved")]
    if pending_actions:
        lines.append(f"Acoes pendentes: {len(pending_actions)}")

    pending_intentions = [i for i in state.get("intentions", []) if i.get("status") in ("pending", "ambiguous")]
    if pending_intentions:
        lines.append(f"Intencoes pendentes: {len(pending_intentions)}")
    ambiguous_intentions = [i for i in state.get("intentions", []) if i.get("status") == "ambiguous"]
    if ambiguous_intentions:
        lines.append(f"Intencoes ambíguas: {len(ambiguous_intentions)}")

    results = state.get("results", {})
    recent_results = {k: v for k, v in results.items() if v.get("status")}
    if recent_results:
        lines.append(f"Resultados recentes: {len(recent_results)}")

    if state.get("ahri_runtime", {}).get("audit_mode"):
        lines.append(f"MODO AUDITORIA ATIVO — escopo: {state['ahri_runtime'].get('audit_scope', 'geral')}")

    return "\n".join(lines)


def _get_memory_context() -> str:
    try:
        from memory_sessions import get_recent_context
        return get_recent_context()
    except ImportError:
        pass
    try:
        from ahri_memory import get_context_for_session
        return get_context_for_session()
    except ImportError:
        return ""


def _extract_intentions(response: str) -> list:
    intentions = []
    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("INTENTION:"):
            intention_text = line[10:].strip()
            if intention_text:
                intentions.append(intention_text)
    return intentions


def _strip_intentions(response: str) -> str:
    lines = []
    for line in response.split("\n"):
        if not line.strip().startswith("INTENTION:"):
            lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Telegram poll cycle (called by scheduler)
# ---------------------------------------------------------------------------

_last_update_id = 0


def telegram_poll_cycle():
    global _last_update_id

    # Send queued notifications from state
    state = read_state()
    notifications = state.get("notifications", [])
    if notifications:
        for notif in notifications:
            text = notif.get("text", "")
            priority = notif.get("priority", "normal")
            telegram_send(text)
        # Clear notifications after sending
        merge_state({"notifications": []}, agent="ahri", reason="notifications_sent")

    # Poll for Telegram updates
    updates = telegram_get_updates(offset=_last_update_id + 1)
    for update in updates:
        _last_update_id = update.get("update_id", _last_update_id)
        handle_telegram_update(update)