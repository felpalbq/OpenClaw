# validate.py — Verificações objetivas do estado
# Cada nível é INDEPENDENTE. Sem inferência, sem interpretação, sem narrativa.
# Uso: python tests/validate.py --level N
#
# Regra de ouro: se este script for apagado, o sistema funciona igual.

import json
import sys
import argparse
from pathlib import Path

# Forcar UTF-8 no Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import os
os.environ.setdefault("STATE_FILE", "state_test.json")

FIXTURES_DIR = ROOT / "tests" / "fixtures"


def ok(msg): print(f"  [OK] {msg}")
def fail(msg): print(f"  [X]  {msg}")
def section(title): print(f"\n{'='*50}\n  {title}\n{'='*50}")


# ============================================================
# NÍVEL 0 — Estado: read_state/write_state funcionam?
# ============================================================

def validate_level_0():
    section("Nível 0 — Estado: módulo state existe e funciona?")

    # Check 1: state/__init__.py existe
    state_init = ROOT / "state" / "__init__.py"
    if state_init.exists():
        ok("state/__init__.py existe")
    else:
        fail("state/__init__.py não existe")
        return False

    # Check 2: read_state e write_state são importáveis
    try:
        from state import read_state, write_state
        ok("read_state() e write_state() importáveis")
    except ImportError as e:
        fail(f"Importação falhou: {e}")
        return False

    # Check 3: write_state executa sem erro
    test_key = f"_validate_test_{__import__('time').time()}"
    try:
        state = read_state()
        state[test_key] = "validate_check"
        write_state(state, agent="validate", reason="level_0_check")
        ok("write_state() executa sem erro")
    except Exception as e:
        fail(f"write_state() falhou: {e}")
        return False

    # Check 4: read_state retorna JSON válido com o dado escrito
    try:
        state = read_state()
        if state.get(test_key) == "validate_check":
            ok("read_state() retorna dado escrito")
        else:
            fail("read_state() não retornou o dado escrito")
            return False
    except Exception as e:
        fail(f"read_state() falhou: {e}")
        return False

    # Cleanup
    try:
        state = read_state()
        state.pop(test_key, None)
        write_state(state, agent="validate", reason="level_0_cleanup")
    except Exception:
        pass

    return True


# ============================================================
# NÍVEL 1 — Integrações: cada uma responde?
# ============================================================

def validate_level_1():
    section("Nível 1 — Integrações: cada uma responde?")

    all_ok = True

    # OpenRouter
    try:
        from llm.client import _make_openrouter_client
        key = os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            fail("OPENROUTER_API_KEY não configurada")
            all_ok = False
        else:
            ok("openrouter: módulo importável, key presente")
    except ImportError:
        fail("llm/client.py não encontrado")
        all_ok = False
    except Exception as e:
        fail(f"openrouter: {str(e)[:60]}")
        all_ok = False

    # Google
    try:
        from tools.google import test_connection
        ok("tools/google: módulo importável")
    except ImportError:
        fail("tools/google não encontrado")
        all_ok = False
    except Exception as e:
        fail(f"tools/google: {str(e)[:60]}")
        all_ok = False

    # Trello
    try:
        from tools.trello import test_connection as trello_test
        ok("tools/trello: módulo importável")
    except ImportError:
        fail("tools/trello não encontrado")
        all_ok = False
    except Exception as e:
        fail(f"tools/trello: {str(e)[:60]}")
        all_ok = False

    # Supabase
    try:
        from tools.supabase import list_clients
        ok("tools/supabase: módulo importável")
    except ImportError:
        fail("tools/supabase não encontrado")
        all_ok = False
    except Exception as e:
        fail(f"tools/supabase: {str(e)[:60]}")
        all_ok = False

    return all_ok


# ============================================================
# NÍVEL 2 — Agente: estado contém resultado de agente?
# ============================================================

def validate_level_2():
    section("Nível 2 — Agente: estado contém resultado de agente?")

    try:
        from state import read_state
    except ImportError:
        fail("state module não encontrado — executar nível 0 primeiro")
        return False

    state = read_state()

    # Check: agents existe e tem conteúdo
    agents_data = state.get("agents", {})
    if agents_data:
        agent_names = list(agents_data.keys())
        ok(f"Resultado de agente encontrado: {agent_names}")
        return True
    else:
        fail("Nenhum resultado de agente encontrado no estado")
        print("  -> Agente rodou via cron desde a última injeção?")
        return False


# ============================================================
# NÍVEL 3 — Ahri: responde com base no estado real?
# ============================================================

def validate_level_3():
    section("Nível 3 — Ahri: módulo existe e pode responder?")

    # Check 1: ahri.py existe
    ahri_path = ROOT / "agents" / "ahri.py"
    if not ahri_path.exists():
        fail("agents/ahri.py não existe")
        return False

    ok("agents/ahri.py existe")

    # Check 2: ask() é importável
    try:
        from agents.ahri import ask
        ok("agents.ahri.ask() importável")
    except ImportError as e:
        fail(f"ask() não importável: {e}")
        return False

    # Check 3: ask() retorna string
    try:
        from state import read_state
        state = read_state()
        response = ask("Tem alguma tarefa pendente?", state)
        if isinstance(response, str) and len(response) > 10:
            ok(f"Ahri retornou resposta ({len(response)} chars)")
            return True
        else:
            fail("Ahri não retornou resposta válida")
            return False
    except Exception as e:
        fail(f"Erro ao chamar ask(): {e}")
        return False


# ============================================================
# NÍVEL 4 — Ciclo completo: estado contém evidência de ciclo?
# ============================================================

def validate_level_4():
    section("Nível 4 — Ciclo completo: evidência no estado?")

    try:
        from state import read_state
    except ImportError:
        fail("state module não encontrado")
        return False

    state = read_state()

    # Check objetivo: existe tarefa que passou por ciclo completo?
    tasks = state.get("tasks", {})
    has_complete = False

    for task_id, task in tasks.items():
        status = task.get("status", "")
        if status in ("content_done", "distributed", "completed"):
            ok(f"Tarefa com ciclo completo: {task_id} — status: {status}")
            has_complete = True

    if not has_complete:
        fail("Nenhuma tarefa com ciclo completo encontrado no estado")
        print("  -> Sistema rodou ciclo completo desde a última injeção?")

    return has_complete


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Validate — Checks objetivos do estado")
    parser.add_argument("--level", type=int, default=None,
                        help="Nível específico (0-4). Default: todos os níveis.")
    parser.add_argument("--verbose", action="store_true",
                        help="Output detalhado")
    args = parser.parse_args()

    print("\n==================================================")
    print("  OpenClaw — Validate — Checks Objetivos")
    print("==================================================")

    levels = {
        0: ("Estado", validate_level_0),
        1: ("Integrações", validate_level_1),
        2: ("Agente", validate_level_2),
        3: ("Ahri", validate_level_3),
        4: ("Ciclo completo", validate_level_4),
    }

    if args.level is not None:
        if args.level not in levels:
            print(f"\n  [X] Nível inválido: {args.level}. Use 0-4.\n")
            return
        name, fn = levels[args.level]
        passed = fn()
        status = "PASSOU" if passed else "FALHOU"
        print(f"\n  [{status}] Nível {args.level} ({name})\n")
    else:
        results = {}
        for level, (name, fn) in levels.items():
            passed = fn()
            results[level] = passed
            mark = "OK" if passed else " X"
            print(f"  [{mark}] Nível {level} ({name})")
        print(f"\n  Total: {sum(results.values())}/{len(results)} passaram\n")


if __name__ == "__main__":
    main()