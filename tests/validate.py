# validate.py — Verificacoes objetivas do estado
# Cada nivel e INDEPENDENTE. Foco em Ahri e memoria (Fase 1).
# Uso: python tests/validate.py --level N
#
# Regra de ouro: se este script for apagado, o sistema funciona igual.

import json
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import os
os.environ.setdefault("STATE_FILE", "state_test.json")

# Forcar UTF-8 no Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

FIXTURES_DIR = ROOT / "tests" / "fixtures"


def ok(msg): print(f"  [OK] {msg}")
def fail(msg): print(f"  [X]  {msg}")
def section(title): print(f"\n{'='*50}\n  {title}\n{'='*50}")


# ============================================================
# NIVEL 0 — Estado: read_state/write_state funcionam?
# ============================================================

def validate_level_0():
    section("Nivel 0 — Estado: modulo state funciona?")

    state_init = ROOT / "state" / "__init__.py"
    if state_init.exists():
        ok("state/__init__.py existe")
    else:
        fail("state/__init__.py nao existe")
        return False

    try:
        from state import read_state, write_state
        ok("read_state() e write_state() importaveis")
    except ImportError as e:
        fail(f"Importacao falhou: {e}")
        return False

    test_key = f"_validate_test_{__import__('time').time()}"
    try:
        state = read_state()
        state[test_key] = "validate_check"
        write_state(state, agent="validate", reason="level_0_check")
        ok("write_state() executa sem erro")
    except Exception as e:
        fail(f"write_state() falhou: {e}")
        return False

    try:
        state = read_state()
        if state.get(test_key) == "validate_check":
            ok("read_state() retorna dado escrito")
        else:
            fail("read_state() nao retornou o dado escrito")
            return False
    except Exception as e:
        fail(f"read_state() falhou: {e}")
        return False

    try:
        state = read_state()
        state.pop(test_key, None)
        write_state(state, agent="validate", reason="level_0_cleanup")
    except Exception:
        pass

    return True


# ============================================================
# NIVEL 1 — Ahri conversacional: le estado e responde?
# ============================================================

def validate_level_1():
    section("Nivel 1 — Ahri: le estado e responde sem inventar?")

    ahri_path = ROOT / "agents" / "ahri.py"
    if not ahri_path.exists():
        fail("agents/ahri.py nao existe")
        return False

    ok("agents/ahri.py existe")

    try:
        from agents.ahri import ask
        ok("agents.ahri.ask() importavel")
    except ImportError as e:
        fail(f"ask() nao importavel: {e}")
        return False

    try:
        from state import read_state
        state = read_state()
        response = ask("Tem alguma tarefa pendente?", state)
        if isinstance(response, str) and len(response) > 10:
            ok(f"Ahri retornou resposta ({len(response)} chars)")
            return True
        else:
            fail("Ahri nao retornou resposta valida")
            return False
    except Exception as e:
        fail(f"Erro ao chamar ask(): {e}")
        return False


# ============================================================
# NIVEL 2 — Ahri + tools: usa integracoes?
# ============================================================

def validate_level_2():
    section("Nivel 2 — Ahri + tools: usa integracoes e responde com dados reais?")

    try:
        from agents.ahri import ask
        from state import read_state
    except ImportError:
        fail("agents/ahri.py ou state module nao encontrado")
        return False

    # Verificar se Ahri pode usar tools
    try:
        from agents.ahri import get_available_tools
        tools = get_available_tools()
        ok(f"Ahri tem acesso a {len(tools)} tool(s)")
    except (ImportError, AttributeError):
        warn = "  [!] Ahri nao expoe get_available_tools() — verificar implementacao"
        print(warn)

    # Verificar se integracoes sao acessiveis
    tools_ok = 0
    tools_total = 0

    for tool_name, module_path in [
        ("trello", "tools.trello"),
        ("google", "tools.google"),
    ]:
        tools_total += 1
        try:
            __import__(module_path)
            ok(f"Tool {tool_name} importavel")
            tools_ok += 1
        except ImportError:
            fail(f"Tool {tool_name} nao encontrada")

    return tools_ok == tools_total


# ============================================================
# NIVEL 3 — Memoria da Ahri: persiste e recupera?
# ============================================================

def validate_level_3():
    section("Nivel 3 — Memoria da Ahri: persiste e recupera?")

    ahri_memory_dir = ROOT / "ahri_memory"
    if not ahri_memory_dir.exists():
        fail("ahri_memory/ nao existe")
        return False

    ok("ahri_memory/ existe")

    index_path = ahri_memory_dir / "index.json"
    if index_path.exists():
        ok("ahri_memory/index.json existe")
    else:
        fail("ahri_memory/index.json nao existe")
        return False

    # Verificar se Ahri pode ler/escrever memoria
    try:
        from ahri_memory import read_memory, write_memory
        ok("ahri_memory.read_memory() e write_memory() importaveis")
    except ImportError:
        fail("ahri_memory/__init__.py nao encontrado ou sem funcoes exportadas")
        return False

    # Teste de escrita e leitura
    try:
        test_entry = {
            "id": f"validate_test_{__import__('time').time()}",
            "type": "interaction",
            "summary": "entrada de teste do validate",
            "relevance": "low"
        }
        write_memory(test_entry)
        ok("write_memory() executa sem erro")

        memory = read_memory()
        if any(e.get("id") == test_entry["id"] for e in memory if isinstance(e, dict)):
            ok("read_memory() retorna entrada escrita")
            return True
        else:
            fail("read_memory() nao retornou a entrada escrita")
            return False
    except Exception as e:
        fail(f"Erro ao testar memoria: {e}")
        return False


# ============================================================
# NIVEL 4 — Filtro de memoria: registra o que importa?
# ============================================================

def validate_level_4():
    section("Nivel 4 — Filtro de memoria: registra o que importa e descarta ruido?")

    try:
        from ahri_memory import should_register
        ok("ahri_memory.should_register() importavel")
    except ImportError:
        fail("ahri_memory.should_register() nao encontrada")
        return False

    # Testar: feedback explicito deve ser registrado
    if should_register({
        "type": "feedback",
        "summary": "Felipe rejeitou tom do caption",
        "relevance": "high"
    }):
        ok("Feedback explicito: deve registrar -> PASSOU")
    else:
        fail("Feedback explicito: deveria registrar mas should_register retornou False")
        return False

    # Testar: conversa casual nao deve ser registrada
    if not should_register({
        "type": "casual",
        "summary": "Bom dia Chefe",
        "relevance": "none"
    }):
        ok("Conversa casual: nao deve registrar -> PASSOU")
    else:
        fail("Conversa casual: nao deveria registrar mas should_register retornou True")
        return False

    # Testar: erro resolvido deve ser registrado
    if should_register({
        "type": "error_resolved",
        "summary": "Trello falhou 3 vezes, resolvido reiniciando token",
        "relevance": "high"
    }):
        ok("Erro resolvido: deve registrar -> PASSOU")
    else:
        fail("Erro resolvido: deveria registrar mas should_register retornou False")
        return False

    # Testar: dado duplicado nao deve ser registrado
    if not should_register({
        "type": "interaction",
        "summary": "mesmo dado ja registrado",
        "relevance": "none",
        "duplicate": True
    }):
        ok("Dado duplicado: nao deve registrar -> PASSOU")
    else:
        fail("Dado duplicado: nao deveria registrar mas should_register retornou True")
        return False

    return True


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Validate — Checks objetivos (Fase 1: Ahri + memória)")
    parser.add_argument("--level", type=int, default=None,
                        help="Nível específico (0-4). Default: todos os níveis.")
    args = parser.parse_args()

    print("\n==================================================")
    print("  OpenClaw — Validate — Checks Objetivos")
    print("  Fase 1: Ahri + Memória")
    print("==================================================")

    levels = {
        0: ("Estado", validate_level_0),
        1: ("Ahri conversacional", validate_level_1),
        2: ("Ahri + tools", validate_level_2),
        3: ("Memória da Ahri", validate_level_3),
        4: ("Filtro de memória", validate_level_4),
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