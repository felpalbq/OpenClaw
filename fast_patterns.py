"""
Fast-path intent classification — keyword patterns for read-only tools.
Skips LLM when all keywords match and tool category is "read".
"""
from tools.registry import TOOL_REGISTRY


FAST_PATTERNS = [
    # Gmail read
    {"keywords": ["email", "listar"], "tool": "gmail_list"},
    {"keywords": ["email", "recent"], "tool": "gmail_list"},
    {"keywords": ["emails"], "tool": "gmail_list"},
    {"keywords": ["email", "ler"], "tool": "gmail_read"},
    {"keywords": ["email", "ler", "mensagem"], "tool": "gmail_read"},
    # Calendar read
    {"keywords": ["agenda", "hoje"], "tool": "calendar_today"},
    {"keywords": ["eventos", "hoje"], "tool": "calendar_today"},
    {"keywords": ["calendario", "hoje"], "tool": "calendar_today"},
    {"keywords": ["agenda", "listar"], "tool": "calendar_list"},
    {"keywords": ["eventos", "listar"], "tool": "calendar_list"},
    {"keywords": ["calendario", "listar"], "tool": "calendar_list"},
    # Drive read
    {"keywords": ["drive", "listar"], "tool": "drive_list"},
    {"keywords": ["arquivos", "drive"], "tool": "drive_list"},
    {"keywords": ["drive", "buscar"], "tool": "drive_search"},
    {"keywords": ["arquivo", "buscar"], "tool": "drive_search"},
    # Trello read
    {"keywords": ["trello", "boards"], "tool": "trello_get_boards"},
    {"keywords": ["trello", "listar"], "tool": "trello_get_boards"},
    {"keywords": ["trello", "listas"], "tool": "trello_get_lists"},
    {"keywords": ["trello", "cards"], "tool": "trello_get_cards"},
    {"keywords": ["trello", "etiquetas"], "tool": "trello_get_labels"},
    {"keywords": ["trello", "conexao"], "tool": "trello_test"},
    # Supabase read
    {"keywords": ["supabase", "consultar"], "tool": "supabase_select"},
    {"keywords": ["supabase", "saude"], "tool": "supabase_health"},
    {"keywords": ["supabase", "status"], "tool": "supabase_health"},
]


def try_fast_resolve(text: str) -> dict | None:
    """
    Try to resolve an intent via keyword matching.
    Returns {"tool": ..., "params": {}, "confidence": "high", "source": "fast_pattern"} or None.
    All keywords in a pattern must appear in the text (case-insensitive).
    Only matches tools with category "read" (no side effects).
    """
    text_lower = text.lower()

    for pattern in FAST_PATTERNS:
        if all(kw in text_lower for kw in pattern["keywords"]):
            tool_name = pattern["tool"]
            tool_def = TOOL_REGISTRY.get(tool_name)
            if tool_def and tool_def.get("category") == "read":
                return {
                    "tool": tool_name,
                    "params": {},
                    "confidence": "high",
                    "source": "fast_pattern",
                }

    return None