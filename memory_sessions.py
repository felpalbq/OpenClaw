"""
Session logging — delegates to ahri memory repo.
"""

import ahri as _ahri


def append_session(role: str, content: str, metadata: dict = None):
    _ahri.append_session(role, content, metadata)


def get_recent_history(limit: int = 20, timeout_minutes: int = 30) -> list:
    sessions = _ahri.read_sessions(limit=limit)
    return [{"role": s.get("role", ""), "content": s.get("content", "")} for s in sessions]


def get_recent_context(max_chars: int = 4000) -> str:
    return _ahri.get_context_for_session()


def cleanup_old_sessions(max_days: int = 30):
    _ahri.maintenance()