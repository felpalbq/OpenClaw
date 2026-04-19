# trello.py — Integração com Trello
# Usa REST API do Trello diretamente via urllib — sem dependências extras.
# Erros são escritos no estado, não emitidos como eventos.

import os
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional


def _get_config():
    """Retorna configuração do Trello do ambiente."""
    return {
        "api_key": os.environ.get("TRELLO_API_KEY", ""),
        "token": os.environ.get("TRELLO_TOKEN", ""),
        "board_id": os.environ.get("TRELLO_BOARD_ID", ""),
        "default_list_id": os.environ.get("TRELLO_DEFAULT_LIST_ID", ""),
    }


def _validate_config():
    """Valida se credenciais do Trello estão presentes."""
    config = _get_config()
    missing = [k for k, v in config.items() if not v and k != "default_list_id"]
    if missing:
        return False, config, missing
    return True, config, []


def _trello_request(method: str, endpoint: str,
                    params: Optional[dict] = None,
                    body: Optional[dict] = None) -> dict:
    """Faz request à API REST do Trello.

    Em caso de falha, escreve erro no estado e levanta exceção.
    """
    valid, config, missing = _validate_config()
    if not valid:
        raise ValueError(f"Trello: credenciais ausentes: {', '.join(missing)}")

    base_params = {
        "key": config["api_key"],
        "token": config["token"],
    }
    if params:
        base_params.update(params)

    query_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in base_params.items())
    url = f"https://api.trello.com/1/{endpoint}?{query_string}"

    try:
        data = json.dumps(body).encode("utf-8") if body else None
        headers = {"Content-Type": "application/json"} if body else {}

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="ignore")[:200]
        cause = "credenciais inválidas" if e.code == 401 else \
                "recurso não encontrado" if e.code == 404 else \
                "rate limit" if e.code == 429 else \
                f"erro HTTP {e.code}"

        error_context = {
            "integration": "trello",
            "stage": endpoint,
            "error": f"HTTP {e.code}: {body_text}",
            "cause": cause,
            "code": str(e.code)
        }

        try:
            from state import write_state
            write_state({"integrations": {"trello": {"status": "error", "last_error": error_context}}},
                        agent="trello_tool", reason=f"request_failed_{endpoint}")
        except Exception:
            pass

        raise Exception(f"Trello {e.code}: {cause}")

    except urllib.error.URLError as e:
        error_context = {
            "integration": "trello",
            "stage": endpoint,
            "error": str(e.reason),
            "cause": "erro de rede — Trello inacessível",
        }

        try:
            from state import write_state
            write_state({"integrations": {"trello": {"status": "error", "last_error": error_context}}},
                        agent="trello_tool", reason=f"network_error_{endpoint}")
        except Exception:
            pass

        raise


def get_lists_on_board(board_id: Optional[str] = None) -> list:
    """Retorna listas do board configurado."""
    config = _get_config()
    bid = board_id or config["board_id"]
    if not bid:
        return []
    result = _trello_request("GET", f"boards/{bid}/lists")
    return [{"id": l["id"], "name": l["name"]} for l in result]


def create_card(title: str,
                description: str = "",
                list_id: Optional[str] = None,
                package_id: Optional[str] = None) -> dict:
    """Cria um card no Trello.

    Args:
        title: Título do card
        description: Descrição (aceita markdown)
        list_id: ID da lista destino. Se None, usa TRELLO_DEFAULT_LIST_ID
        package_id: ID do ContentPackage para rastreamento

    Returns:
        Dict com id, url e name do card criado
    """
    config = _get_config()
    target_list = list_id or config["default_list_id"]

    if not target_list:
        raise ValueError("list_id obrigatório — configurar TRELLO_DEFAULT_LIST_ID no .env")

    desc = description
    if package_id:
        desc += f"\n\n---\n_package_id: {package_id}_"

    result = _trello_request("POST", "cards", body={
        "name": title,
        "desc": desc,
        "idList": target_list,
        "pos": "top"
    })

    try:
        from state import write_state
        write_state({"integrations": {"trello": {"status": "connected", "last_action": "create_card"}}},
                    agent="trello_tool", reason="card_created")
    except Exception:
        pass

    return {
        "id": result.get("id"),
        "url": result.get("shortUrl"),
        "name": result.get("name")
    }


def test_connection() -> bool:
    """Testa autenticação e acesso ao board."""
    try:
        config = _get_config()
        if not config["board_id"]:
            return False
        lists = get_lists_on_board()
        if lists:
            print(f"  Trello conectado — {len(lists)} listas no board")
            for l in lists:
                print(f"    {l['name']} (id: {l['id']})")
            return True
        return False
    except Exception:
        return False