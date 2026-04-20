# inject.py — Injeta dados sintéticos no estado
# MERGE, não substitui. Nunca destrói estrutura existente.
# Uso: python tests/inject.py
#
# Regra de ouro: se este script for apagado, o sistema funciona igual.

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Forcar UTF-8 no Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("STATE_FILE", "state_test.json")

FIXTURES_DIR = ROOT / "tests" / "fixtures"


def load_fixture(filename: str) -> dict:
    path = FIXTURES_DIR / filename
    if not path.exists():
        print(f"  [X] Fixture não encontrado: {filename}")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def inject():
    print("\n==================================================")
    print("  OpenClaw — Inject — Injeta dados sintéticos")
    print("==================================================\n")

    client = load_fixture("client_test.json")
    tasks = load_fixture("task_test.json")

    if not client:
        print("  [X] client_test.json não encontrado. Abortando.")
        return

    if not tasks:
        print("  [X] task_test.json não encontrado. Abortando.")
        return

    # Importar state module — se não existe, não podemos injetar
    try:
        from state import read_state, write_state
    except ImportError:
        print("  [X] state/__init__.py não encontrado. Implementar antes de injetar.")
        print("    Criar state/__init__.py com read_state() e write_state().")
        return

    # Ler estado atual — MERGE, nunca substituir
    state = read_state()

    # Mesclar cliente de teste
    if "clients" not in state:
        state["clients"] = {}
    state["clients"]["client_test_001"] = client
    print(f"  [OK] Cliente injetado: {client.get('name', 'client_test_001')}")

    # Mesclar tarefas de teste
    if "tasks" not in state:
        state["tasks"] = {}
    for task in tasks.get("tasks", []):
        task_id = task.get("id")
        if task_id:
            state["tasks"][task_id] = task
    print(f"  [OK] Tarefas injetadas: {len(tasks.get('tasks', []))}")

    # Garantir seções base (modules, ahri, integrations)
    if "modules" not in state:
        state["modules"] = {}
    if "ahri" not in state:
        state["ahri"] = {"last_interaction": "", "current_context": ""}
    if "integrations" not in state:
        state["integrations"] = {
            "google": {"status": "unknown"},
            "trello": {"status": "unknown"},
            "supabase": {"status": "unknown"},
            "telegram": {"status": "unknown"}
        }
    print(f"  [OK] Seções base do estado garantidas (modules, ahri, integrations)")

    # Marcar que dados de teste foram injetados
    if "meta" not in state:
        state["meta"] = {}
    state["meta"]["test_data_injected"] = True
    state["meta"]["injected_at"] = datetime.now().isoformat()

    # Escrever estado mesclado
    write_state(state, agent="inject", reason="synthetic_test_data")
    print(f"\n  [OK] Dados sintéticos mesclados no estado.\n")


if __name__ == "__main__":
    inject()