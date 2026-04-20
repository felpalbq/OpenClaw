import os
import sys
import json
import urllib.request
from datetime import datetime

ROOT = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from state import read_state, write_state

# ---------------------------------------------------------------------------
# LLM config — via .env (OpenRouter or OpenAI)
# ---------------------------------------------------------------------------

LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
LLM_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """Você é a Ahri — HQ conversacional do OpenClaw.
Você é a assistente pessoal do Felipe. Responde com base no estado real do sistema.

Regras:
- Nunca invente dados. Se não há informação no estado, diga que não tem.
- Responda em português brasileiro, de forma direta e útil.
- Se o usuário pedir algo que requer uma tool, use a tool disponível.
- Se um módulo especialista for mencionado, verifique no estado se está acoplado.
- Sempre que possível, aja: não só informe, execute.
"""

# ---------------------------------------------------------------------------
# Telegram config
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
# Tools — wrap existing tools for Ahri
# ---------------------------------------------------------------------------

def _try_import(module_path: str, func_name: str):
    try:
        mod = __import__(module_path, fromlist=[func_name])
        return getattr(mod, func_name, None)
    except Exception:
        return None


def _run_tool(tool_name: str, **kwargs) -> dict:
    tool_map = {
        "gmail_list": ("tools.google.gmail", "list_emails"),
        "gmail_read": ("tools.google.gmail", "read_email"),
        "calendar_today": ("tools.google.calendar", "today_events"),
        "calendar_list": ("tools.google.calendar", "list_events"),
        "calendar_create": ("tools.google.calendar", "create_event"),
        "drive_list": ("tools.google.drive", "list_files"),
        "drive_search": ("tools.google.drive", "search_file"),
        "trello_test": ("tools.trello", "test_connection"),
        "trello_create_card": ("tools.trello", "create_card"),
        "supabase_health": ("tools.supabase", "is_connected"),
    }

    if tool_name not in tool_map:
        return {"error": f"Tool desconhecida: {tool_name}"}

    module_path, func_name = tool_map[tool_name]
    fn = _try_import(module_path, func_name)
    if fn is None:
        return {"error": f"Tool não disponível: {tool_name}"}

    try:
        result = fn(**kwargs)
        return result if isinstance(result, dict) else {"result": result}
    except Exception as e:
        return {"error": str(e)}


def get_available_tools() -> list:
    tools = []
    tool_defs = [
        ("gmail_list", "Listar emails recentes"),
        ("gmail_read", "Ler email específico"),
        ("calendar_today", "Eventos de hoje"),
        ("calendar_list", "Listar eventos"),
        ("calendar_create", "Criar evento"),
        ("drive_list", "Listar arquivos do Drive"),
        ("drive_search", "Buscar arquivo no Drive"),
        ("trello_test", "Testar conexão Trello"),
        ("trello_create_card", "Criar card no Trello"),
        ("supabase_health", "Verificar Supabase"),
    ]
    for name, desc in tool_defs:
        module_path, func_name = dict([
            ("gmail_list", ("tools.google.gmail", "list_emails")),
            ("gmail_read", ("tools.google.gmail", "read_email")),
            ("calendar_today", ("tools.google.calendar", "today_events")),
            ("calendar_list", ("tools.google.calendar", "list_events")),
            ("calendar_create", ("tools.google.calendar", "create_event")),
            ("drive_list", ("tools.google.drive", "list_files")),
            ("drive_search", ("tools.google.drive", "search_file")),
            ("trello_test", ("tools.trello", "test_connection")),
            ("trello_create_card", ("tools.trello", "create_card")),
            ("supabase_health", ("tools.supabase", "health_check")),
        ])[name]
        fn = _try_import(module_path, func_name)
        tools.append({"name": name, "description": desc, "available": fn is not None})
    return tools


# ---------------------------------------------------------------------------
# Core: ask()
# ---------------------------------------------------------------------------

def ask(question: str, state: dict = None) -> str:
    if state is None:
        state = read_state()

    state_summary = _summarize_state(state)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Estado atual:\n{state_summary}\n\nPergunta do Felipe: {question}"},
    ]

    response = _llm_call(messages)

    # Update Ahri's interaction in state
    state.setdefault("ahri", {})
    state["ahri"]["last_interaction"] = datetime.now().isoformat()
    state["ahri"]["current_context"] = question[:200]
    write_state(state, agent="ahri", reason="interaction")

    # Try to register in memory
    try:
        from ahri_memory import write_memory, should_register
        entry = {
            "type": "interaction",
            "summary": question[:200],
            "relevance": "medium",
        }
        if should_register(entry):
            write_memory(entry)
    except ImportError:
        pass

    return response


def execute_tool(tool_name: str, **kwargs) -> dict:
    return _run_tool(tool_name, **kwargs)


def ask_with_tools(question: str, state: dict = None) -> str:
    if state is None:
        state = read_state()

    state_summary = _summarize_state(state)
    tools = get_available_tools()
    tool_list = "\n".join(
        f"- {t['name']}: {t['description']} ({'OK' if t['available'] else 'indisponível'})"
        for t in tools
    )

    prompt = f"""Estado atual:
{state_summary}

Tools disponíveis:
{tool_list}

Pergunta do Felipe: {question}

Se precisar usar uma tool, responda EXATAMENTE no formato:
TOOL:nome_da_tool|param1=val1,param2=val2

Caso contrário, responda normalmente em português brasileiro."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    response = _llm_call(messages)

    # Check if Ahri wants to use a tool
    if response.startswith("TOOL:"):
        try:
            parts = response.split("|", 1)
            tool_name = parts[0].replace("TOOL:", "").strip()
            kwargs = {}
            if len(parts) > 1:
                for pair in parts[1].split(","):
                    k, v = pair.split("=", 1)
                    kwargs[k.strip()] = v.strip()
            result = _run_tool(tool_name, **kwargs)
            # Feed result back to LLM for natural response
            follow_up = _llm_call([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Pergunta: {question}\n\nResultado da tool {tool_name}: {json.dumps(result, ensure_ascii=False)}\n\nResponda em português de forma natural com base nesse resultado."},
            ])
            state.setdefault("ahri", {})
            state["ahri"]["last_interaction"] = datetime.now().isoformat()
            state["ahri"]["current_context"] = question[:200]
            write_state(state, agent="ahri", reason="tool_execution")
            return follow_up
        except Exception as e:
            return f"Erro ao executar tool: {e}"

    state.setdefault("ahri", {})
    state["ahri"]["last_interaction"] = datetime.now().isoformat()
    state["ahri"]["current_context"] = question[:200]
    write_state(state, agent="ahri", reason="interaction")

    try:
        from ahri_memory import write_memory, should_register
        entry = {"type": "interaction", "summary": question[:200], "relevance": "medium"}
        if should_register(entry):
            write_memory(entry)
    except ImportError:
        pass

    return response


# ---------------------------------------------------------------------------
# Telegram integration
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
# Helpers
# ---------------------------------------------------------------------------

def _summarize_state(state: dict) -> str:
    lines = []
    if "clients" in state and state["clients"]:
        lines.append(f"Clientes: {len(state['clients'])} registrado(s)")
    else:
        lines.append("Clientes: nenhum")

    tasks = state.get("tasks", {})
    if tasks:
        pending = sum(1 for t in tasks.values() if isinstance(t, dict) and t.get("status") == "pending")
        ready = sum(1 for t in tasks.values() if isinstance(t, dict) and t.get("status") == "ready")
        done = sum(1 for t in tasks.values() if isinstance(t, dict) and t.get("status") in ("done", "complete"))
        lines.append(f"Tarefas: {len(tasks)} total ({pending} pendente(s), {ready} pronta(s), {done} concluída(s))")
    else:
        lines.append("Tarefas: nenhuma")

    modules = state.get("modules", {})
    active = [k for k, v in modules.items() if isinstance(v, dict) and v.get("status") == "active"]
    if active:
        lines.append(f"Módulos ativos: {', '.join(active)}")
    else:
        lines.append("Módulos: nenhum módulo especialista contratado")

    integrations = state.get("integrations", {})
    for name, info in integrations.items():
        if isinstance(info, dict):
            lines.append(f"  {name}: {info.get('status', 'unknown')}")

    ahri = state.get("ahri", {})
    if ahri.get("last_interaction"):
        lines.append(f"Última interação: {ahri['last_interaction']}")

    return "\n".join(lines)