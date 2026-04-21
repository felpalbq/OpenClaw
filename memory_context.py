"""
Context read/write — delegates to ahri memory repo.
"""

import ahri as _ahri


def read_context(key: str):
    return _ahri.read_entry("context", key)


def write_context(key: str, data):
    entry = data if isinstance(data, dict) else {"data": data}
    _ahri.write_entry("context", key, entry)


def update_context(key: str, partial: dict):
    current = read_context(key) or {}
    if isinstance(current, dict) and isinstance(partial, dict):
        current.update(partial)
    else:
        current = partial
    write_context(key, current)


def list_context_keys() -> list:
    entries = _ahri.list_entries("context")
    return [e.get("id", "") for e in entries]


def read_client(client_id: str):
    clients = read_context("clients")
    if not clients or not isinstance(clients, dict):
        return None
    return clients.get(client_id)


def write_client(client_id: str, data: dict):
    clients = read_context("clients") or {}
    clients[client_id] = data
    write_context("clients", clients)