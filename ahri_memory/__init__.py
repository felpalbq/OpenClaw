"""
Thin wrapper for ahri memory repo.
All operations delegate to the ahri package (repo at AHRI_MEMORY_DIR).
"""
import os
import sys

AHRI_MEMORY_DIR = os.environ.get("AHRI_MEMORY_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ahri"))

if AHRI_MEMORY_DIR not in sys.path:
    sys.path.insert(0, AHRI_MEMORY_DIR)

import ahri as _ahri


def read_memory(mem_type=None, limit=50):
    return _ahri.read_entry(mem_type, limit=limit)


def write_memory(entry):
    return _ahri.write_entry(entry["type"], entry.get("id", ""), entry)


def search_memory(query, limit=10):
    return _ahri.search_entries(query, limit=limit)


def get_context_for_session():
    return _ahri.get_context_for_session()


def should_register(entry):
    return _ahri.should_register(entry)


def maintenance():
    return _ahri.maintenance()


def init_repo():
    return _ahri.init_repo()


def commit(message=""):
    return _ahri.commit(message)


def push():
    return _ahri.push()


def pull():
    return _ahri.pull()


def has_git_repo():
    return _ahri.has_git_repo()


__all__ = [
    "read_memory", "write_memory", "search_memory",
    "get_context_for_session", "should_register", "maintenance",
    "init_repo", "commit", "push", "pull", "has_git_repo",
]