import os
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional


def _get_config():
    return {
        "api_key": os.environ.get("TRELLO_API_KEY", ""),
        "token": os.environ.get("TRELLO_TOKEN", ""),
        "board_id": os.environ.get("TRELLO_BOARD_ID", ""),
        "default_list_id": os.environ.get("TRELLO_DEFAULT_LIST_ID", ""),
    }


def _validate_config():
    config = _get_config()
    missing = [k for k, v in config.items() if not v and k != "default_list_id"]
    if missing:
        return False, config, missing
    return True, config, []


def _trello_request(method: str, endpoint: str,
                    params: Optional[dict] = None,
                    body: Optional[dict] = None) -> dict:
    valid, config, missing = _validate_config()
    if not valid:
        raise ValueError(f"Trello: credenciais ausentes: {', '.join(missing)}")

    base_params = {"key": config["api_key"], "token": config["token"]}
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
        cause = ("credenciais invalidas" if e.code == 401 else
                 "recurso nao encontrado" if e.code == 404 else
                 "rate limit" if e.code == 429 else
                 f"erro HTTP {e.code}")
        raise Exception(f"Trello {e.code}: {cause}")

    except urllib.error.URLError as e:
        raise


def get_boards() -> list:
    config = _get_config()
    result = _trello_request("GET", "members/me/boards", params={"fields": "name,id"})
    return [{"id": b["id"], "name": b["name"]} for b in result]


def get_lists_on_board(board_id: Optional[str] = None) -> list:
    config = _get_config()
    bid = board_id or config["board_id"]
    if not bid:
        return []
    result = _trello_request("GET", f"boards/{bid}/lists", params={"fields": "name,id"})
    return [{"id": l["id"], "name": l["name"]} for l in result]


def get_cards_on_list(list_id: str) -> list:
    result = _trello_request("GET", f"lists/{list_id}/cards", params={"fields": "name,id,labels,desc"})
    return result


def create_card(title: str, description: str = "",
                list_id: Optional[str] = None,
                labels: Optional[list] = None) -> dict:
    config = _get_config()
    target_list = list_id or config["default_list_id"]
    if not target_list:
        raise ValueError("list_id obrigatorio — configurar TRELLO_DEFAULT_LIST_ID no .env")

    body = {"name": title, "desc": description, "idList": target_list, "pos": "top"}
    if labels:
        body["idLabels"] = labels

    result = _trello_request("POST", "cards", body=body)
    return {"id": result.get("id"), "url": result.get("shortUrl"), "name": result.get("name"), "_integration_status": {"status": "connected", "last_action": "create_card"}}


def update_card(card_id: str, updates: dict) -> dict:
    result = _trello_request("PUT", f"cards/{card_id}", body=updates)
    result["_integration_status"] = {"status": "connected", "last_action": "update_card"}
    return result


def delete_card(card_id: str) -> dict:
    result = _trello_request("DELETE", f"cards/{card_id}")
    result["_integration_status"] = {"status": "connected", "last_action": "delete_card"}
    return result


def create_list(name: str, board_id: Optional[str] = None) -> dict:
    config = _get_config()
    bid = board_id or config["board_id"]
    if not bid:
        raise ValueError("board_id obrigatorio")
    result = _trello_request("POST", "lists", body={"name": name, "idBoard": bid, "pos": "bottom"})
    return {"id": result.get("id"), "name": result.get("name")}


def update_list(list_id: str, updates: dict) -> dict:
    return _trello_request("PUT", f"lists/{list_id}", body=updates)


def get_labels_on_board(board_id: Optional[str] = None) -> list:
    config = _get_config()
    bid = board_id or config["board_id"]
    if not bid:
        return []
    result = _trello_request("GET", f"boards/{bid}/labels", params={"fields": "name,id,color"})
    return result


def add_label_to_card(card_id: str, label_id: str) -> dict:
    return _trello_request("POST", f"cards/{card_id}/idLabels", body={"value": label_id})


def test_connection() -> bool:
    try:
        config = _get_config()
        if not config["board_id"]:
            return False
        lists = get_lists_on_board()
        if lists:
            return True
        return False
    except Exception:
        return False