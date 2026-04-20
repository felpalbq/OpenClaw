TOOL_REGISTRY = {
    # Gmail
    "gmail_list": {
        "module": "tools.google.gmail",
        "function": "list_emails",
        "requires_approval": False,
        "description": "Listar emails recentes",
        "category": "read",
    },
    "gmail_read": {
        "module": "tools.google.gmail",
        "function": "read_email",
        "requires_approval": False,
        "description": "Ler email especifico",
        "category": "read",
    },
    "gmail_compose": {
        "module": "tools.google.gmail",
        "function": "compose_email",
        "requires_approval": True,
        "description": "Criar novo email",
        "category": "write",
    },
    "gmail_reply": {
        "module": "tools.google.gmail",
        "function": "reply_email",
        "requires_approval": True,
        "description": "Responder email",
        "category": "write",
    },
    "gmail_delete": {
        "module": "tools.google.gmail",
        "function": "delete_email",
        "requires_approval": True,
        "description": "Excluir email",
        "category": "destructive",
    },
    # Calendar
    "calendar_today": {
        "module": "tools.google.calendar",
        "function": "today_events",
        "requires_approval": False,
        "description": "Eventos de hoje",
        "category": "read",
    },
    "calendar_list": {
        "module": "tools.google.calendar",
        "function": "list_events",
        "requires_approval": False,
        "description": "Listar eventos",
        "category": "read",
    },
    "calendar_create": {
        "module": "tools.google.calendar",
        "function": "create_event",
        "requires_approval": True,
        "description": "Criar evento",
        "category": "write",
    },
    "calendar_update": {
        "module": "tools.google.calendar",
        "function": "update_event",
        "requires_approval": True,
        "description": "Modificar evento",
        "category": "write",
    },
    "calendar_delete": {
        "module": "tools.google.calendar",
        "function": "delete_event",
        "requires_approval": True,
        "description": "Excluir evento",
        "category": "destructive",
    },
    # Drive
    "drive_list": {
        "module": "tools.google.drive",
        "function": "list_files",
        "requires_approval": False,
        "description": "Listar arquivos do Drive",
        "category": "read",
    },
    "drive_search": {
        "module": "tools.google.drive",
        "function": "search_file",
        "requires_approval": False,
        "description": "Buscar arquivo no Drive",
        "category": "read",
    },
    "drive_create_folder": {
        "module": "tools.google.drive",
        "function": "create_folder",
        "requires_approval": True,
        "description": "Criar pasta no Drive",
        "category": "write",
    },
    "drive_upload": {
        "module": "tools.google.drive",
        "function": "upload_file",
        "requires_approval": True,
        "description": "Upload de arquivo",
        "category": "write",
    },
    "drive_delete": {
        "module": "tools.google.drive",
        "function": "delete_file",
        "requires_approval": True,
        "description": "Excluir arquivo do Drive",
        "category": "destructive",
    },
    # Trello
    "trello_get_boards": {
        "module": "tools.trello",
        "function": "get_boards",
        "requires_approval": False,
        "description": "Listar boards do Trello",
        "category": "read",
    },
    "trello_get_lists": {
        "module": "tools.trello",
        "function": "get_lists_on_board",
        "requires_approval": False,
        "description": "Listar listas de um board",
        "category": "read",
    },
    "trello_get_cards": {
        "module": "tools.trello",
        "function": "get_cards_on_list",
        "requires_approval": False,
        "description": "Listar cards de uma lista",
        "category": "read",
    },
    "trello_create_card": {
        "module": "tools.trello",
        "function": "create_card",
        "requires_approval": True,
        "description": "Criar card no Trello",
        "category": "write",
    },
    "trello_update_card": {
        "module": "tools.trello",
        "function": "update_card",
        "requires_approval": True,
        "description": "Modificar card no Trello",
        "category": "write",
    },
    "trello_delete_card": {
        "module": "tools.trello",
        "function": "delete_card",
        "requires_approval": True,
        "description": "Excluir card do Trello",
        "category": "destructive",
    },
    "trello_create_list": {
        "module": "tools.trello",
        "function": "create_list",
        "requires_approval": True,
        "description": "Criar lista no Trello",
        "category": "write",
    },
    "trello_update_list": {
        "module": "tools.trello",
        "function": "update_list",
        "requires_approval": True,
        "description": "Modificar lista no Trello",
        "category": "write",
    },
    "trello_get_labels": {
        "module": "tools.trello",
        "function": "get_labels_on_board",
        "requires_approval": False,
        "description": "Listar etiquetas de um board",
        "category": "read",
    },
    "trello_add_label": {
        "module": "tools.trello",
        "function": "add_label_to_card",
        "requires_approval": True,
        "description": "Adicionar etiqueta a card",
        "category": "write",
    },
    "trello_test": {
        "module": "tools.trello",
        "function": "test_connection",
        "requires_approval": False,
        "description": "Testar conexao Trello",
        "category": "read",
    },
    # Supabase
    "supabase_select": {
        "module": "tools.supabase",
        "function": "select",
        "requires_approval": False,
        "description": "Consultar dados no Supabase",
        "category": "read",
    },
    "supabase_insert": {
        "module": "tools.supabase",
        "function": "insert",
        "requires_approval": True,
        "description": "Inserir dado no Supabase",
        "category": "write",
    },
    "supabase_update": {
        "module": "tools.supabase",
        "function": "update",
        "requires_approval": True,
        "description": "Atualizar dado no Supabase",
        "category": "write",
    },
    "supabase_delete": {
        "module": "tools.supabase",
        "function": "delete",
        "requires_approval": True,
        "description": "Excluir dado no Supabase",
        "category": "destructive",
    },
    "supabase_rpc": {
        "module": "tools.supabase",
        "function": "rpc",
        "requires_approval": True,
        "description": "Chamar funcao RPC no Supabase",
        "category": "write",
    },
    "supabase_health": {
        "module": "tools.supabase",
        "function": "is_connected",
        "requires_approval": False,
        "description": "Verificar saude do Supabase",
        "category": "read",
    },
}


def get_tool(tool_name: str) -> dict:
    return TOOL_REGISTRY.get(tool_name)


def get_tools_by_category(category: str) -> list:
    return [t for t in TOOL_REGISTRY.values() if t["category"] == category]


def get_tools_requiring_approval() -> list:
    return [name for name, t in TOOL_REGISTRY.items() if t["requires_approval"]]


def get_autonomous_tools() -> list:
    return [name for name, t in TOOL_REGISTRY.items() if not t["requires_approval"]]