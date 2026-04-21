# supabase.py — Supabase Client para OpenClaw
# Usa REST API (PostgREST) diretamente via urllib — sem dependências extras.
# Anon key para operações com RLS. Service key para admin/bypass RLS.
# Fallback silencioso se Supabase indisponível.

import os
import json
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any


# ============================================================
# CONFIG
# ============================================================

def _get_config():
    """Retorna configuração do Supabase do ambiente."""
    return {
        "url": os.environ.get("SUPABASE_URL", ""),
        "anon_key": os.environ.get("SUPABASE_ANON_KEY", ""),
        "service_key": os.environ.get("SUPABASE_SERVICE_KEY", ""),
    }


# ============================================================
# LOW-LEVEL REST CLIENT
# ============================================================

def _request(method: str, path: str, body: Optional[dict] = None,
             use_service_key: bool = False, prefer: Optional[str] = None) -> Any:
    """
    Faz request ao Supabase REST API (PostgREST).

    Args:
        method: GET, POST, PATCH, DELETE
        path: caminho após /rest/v1/ (ex: "clients")
        body: payload para POST/PATCH
        use_service_key: usar service_role key (bypass RLS)
        prefer: header Prefer (ex: "return=representation")

    Returns:
        Parsed JSON response ou None para 204/DELETE sem corpo.

    Raises:
        Exception se request falhar.
    """
    config = _get_config()

    if not config["url"]:
        raise ConnectionError("SUPABASE_URL não configurada no .env")

    api_key = config["service_key"] if use_service_key else config["anon_key"]
    url = f"{config['url']}/rest/v1/{path}"

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if prefer:
        headers["Prefer"] = prefer

    data = json.dumps(body).encode("utf-8") if body else None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 204:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise Exception(f"Supabase {e.code}: {error_body[:300]}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Supabase indisponível: {e.reason}")


# ============================================================
# CRUD HELPERS
# ============================================================

def select(table: str, columns: str = "*", filters: Optional[Dict] = None,
           limit: Optional[int] = None, order: Optional[str] = None,
           use_service_key: bool = False) -> List[Dict]:
    """
    SELECT from table.

    Args:
        table: nome da tabela
        columns: colunas (ex: "id,name,niche")
        filters: {"coluna": "valor"} → ?coluna=eq.valor
        limit: limitar resultados
        order: "coluna.asc" ou "coluna.desc"
        use_service_key: bypass RLS

    Returns:
        Lista de dicts com resultados.
    """
    params = [f"select={columns}"]

    if filters:
        for col, val in filters.items():
            params.append(f"{col}=eq.{val}")

    if limit:
        params.append(f"limit={limit}")

    if order:
        params.append(f"order={order}")

    path = f"{table}?{'&'.join(params)}"
    return _request("GET", path, use_service_key=use_service_key)


def insert(table: str, records: Any, use_service_key: bool = False) -> List[Dict]:
    """
    INSERT into table.

    Args:
        table: nome da tabela
        records: dict ou lista de dicts
        use_service_key: bypass RLS

    Returns:
        Registros inseridos (se return=representation).
    """
    if isinstance(records, dict):
        records = [records]

    return _request("POST", table, body=records, use_service_key=use_service_key,
                     prefer="return=representation")


def update(table: str, filters: Dict, updates: Dict,
           use_service_key: bool = False) -> List[Dict]:
    """
    UPDATE table WHERE filters.

    Args:
        table: nome da tabela
        filters: {"coluna": "valor"} → coluna=eq.valor
        updates: campos para atualizar
        use_service_key: bypass RLS

    Returns:
        Registros atualizados (se return=representation).
    """
    params = []
    for col, val in filters.items():
        params.append(f"{col}=eq.{val}")

    path = f"{table}?{'&'.join(params)}"
    return _request("PATCH", path, body=updates, use_service_key=use_service_key,
                     prefer="return=representation")


def delete(table: str, filters: Dict, use_service_key: bool = False) -> None:
    """
    DELETE from table WHERE filters.

    Args:
        table: nome da tabela
        filters: {"coluna": "valor"} → coluna=eq.valor
        use_service_key: bypass RLS
    """
    params = []
    for col, val in filters.items():
        params.append(f"{col}=eq.{val}")

    path = f"{table}?{'&'.join(params)}"
    _request("DELETE", path, use_service_key=use_service_key)


# ============================================================
# HEALTH CHECK
# ============================================================

def is_connected() -> bool:
    """Verifica se Supabase está acessível."""
    try:
        config = _get_config()
        if not config["url"]:
            return False
        # Query simples com service key (anon não funciona no root endpoint)
        _request("GET", "", use_service_key=True)
        return True
    except Exception:
        return False


def get_status() -> Dict:
    """Retorna status da conexão Supabase."""
    config = _get_config()
    connected = False
    tables = []

    try:
        if config["url"]:
            # Puxar lista de tabelas via OpenAPI
            spec = _request("GET", "", use_service_key=True)
            paths = spec.get("paths", {})
            tables = [p.strip("/") for p in paths.keys() if p != "/"]
            connected = True
    except Exception:
        pass

    return {
        "connected": connected,
        "url": config["url"] or "não configurada",
        "has_anon_key": bool(config["anon_key"]),
        "has_service_key": bool(config["service_key"]),
        "tables": tables
    }


# ============================================================
# RPC (Remote Procedure Calls)
# ============================================================

def rpc(function_name: str, params: Optional[Dict] = None,
        use_service_key: bool = False) -> Any:
    """
    Chama uma função RPC do Supabase.

    Args:
        function_name: nome da função
        params: parâmetros da função
        use_service_key: bypass RLS
    """
    return _request("POST", f"rpc/{function_name}", body=params or {},
                     use_service_key=use_service_key)


# ============================================================
# TABLE CREATION SQL
# ============================================================

# SQL para criar tabelas do OpenClaw no Supabase
# Executar via Supabase Dashboard → SQL Editor

TABLES_SQL = """
-- =====================================================
-- OpenClaw — Tabelas do Supabase
-- Execute via Dashboard → SQL Editor
-- =====================================================

-- Perfis de clientes
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    niche TEXT DEFAULT '',
    level TEXT DEFAULT 'intermediate' CHECK (level IN ('beginner', 'intermediate', 'advanced')),
    capacity TEXT DEFAULT 'medium' CHECK (capacity IN ('low', 'medium', 'high')),
    objective TEXT DEFAULT '',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Histórico de conteúdo gerado
CREATE TABLE IF NOT EXISTS content_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id TEXT REFERENCES clients(id) ON DELETE SET NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('ideas', 'carousel', 'script', 'caption')),
    topic TEXT,
    content JSONB NOT NULL,
    quality_level TEXT,
    refinement_level TEXT DEFAULT 'production',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feedback do usuário
CREATE TABLE IF NOT EXISTS feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pattern TEXT,
    intent TEXT,
    action_taken TEXT,
    approved BOOLEAN NOT NULL,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Decisões do agente (auditoria)
CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    action TEXT NOT NULL,
    confidence REAL,
    demand_type TEXT,
    intent TEXT,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- RLS (Row Level Security) — liberar para anon key
-- =====================================================

ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_decisions ENABLE ROW LEVEL SECURITY;

-- Políticas de leitura/escrita para anon key
CREATE POLICY "Allow anon read clients" ON clients FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon insert clients" ON clients FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow anon update clients" ON clients FOR UPDATE TO anon USING (true);
CREATE POLICY "Allow anon delete clients" ON clients FOR DELETE TO anon USING (true);

CREATE POLICY "Allow anon read content_history" ON content_history FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon insert content_history" ON content_history FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon read feedback" ON feedback FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon insert feedback" ON feedback FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon read agent_decisions" ON agent_decisions FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon insert agent_decisions" ON agent_decisions FOR INSERT TO anon WITH CHECK (true);

-- Índices
CREATE INDEX IF NOT EXISTS idx_content_history_client ON content_history(client_id);
CREATE INDEX IF NOT EXISTS idx_content_history_type ON content_history(content_type);
CREATE INDEX IF NOT EXISTS idx_feedback_pattern ON feedback(pattern);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_created ON agent_decisions(created_at);
"""