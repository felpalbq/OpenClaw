# validate.py — Checks objetivos do sistema (v2)
# Cada nivel e INDEPENDENTE. Foco em Ahri via estado + executor + memoria.
# Uso: python tests/validate.py --level N
#
# Regra de ouro: se este script for apagado, o sistema funciona igual.

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import os
os.environ.setdefault("STATE_FILE", "state_test.json")

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


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
        from state import read_state, write_state, merge_state
        ok("read_state(), write_state(), merge_state() importaveis")
    except ImportError as e:
        fail(f"Importacao falhou: {e}")
        return False

    # Test merge_state (critical for tools)
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

    # Test merge_state
    try:
        merge_state({"integrations": {"test_integration": {"status": "ok"}}},
                     agent="validate", reason="level_0_merge")
        state = read_state()
        if "test_integration" in state.get("integrations", {}):
            ok("merge_state() mescla sem destruir estado existente")
            # Cleanup
            del state["integrations"]["test_integration"]
            state.pop(test_key, None)
            write_state(state, agent="validate", reason="level_0_cleanup")
        else:
            fail("merge_state() nao mesclou corretamente")
            return False
    except Exception as e:
        fail(f"merge_state() falhou: {e}")
        return False

    # Test atomic write (temp + rename)
    try:
        tmp_path = ROOT / "state" / f"{os.environ.get('STATE_FILE', 'state_test.json')}.tmp"
        if not tmp_path.exists():
            ok("Escrita atomica: .tmp nao permanece (correto)")
        else:
            fail("Escrita atomica: .tmp ainda existe (problema)")
            return False
    except Exception:
        pass

    return True


# ============================================================
# NIVEL 1 — Ahri conversacional: le estado e responde via pending_actions?
# ============================================================

def validate_level_1():
    section("Nivel 1 — Ahri: le estado e responde sem inventar?")

    ahri_path = ROOT / "agents" / "ahri.py"
    if not ahri_path.exists():
        fail("agents/ahri.py nao existe")
        return False

    ok("agents/ahri.py existe")

    try:
        from agents.ahri import ask, propose_action
        ok("agents.ahri.ask() e propose_action() importaveis")
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
# NIVEL 2 — Tool registry unificado e tools importaveis?
# ============================================================

def validate_level_2():
    section("Nivel 2 — Tool registry unificado e tools importaveis?")

    registry_path = ROOT / "tools" / "registry.py"
    if not registry_path.exists():
        fail("tools/registry.py nao existe")
        return False

    ok("tools/registry.py existe")

    try:
        from tools.registry import TOOL_REGISTRY, get_tool, get_autonomous_tools, get_tools_requiring_approval
        ok(f"Tool registry carregado: {len(TOOL_REGISTRY)} tools")
    except ImportError as e:
        fail(f"registry.py nao importavel: {e}")
        return False

    # Check no duplicate modules
    autonomous = get_autonomous_tools()
    requires_approval = get_tools_requiring_approval()
    ok(f"Tools autonomas (leitura): {len(autonomous)}")
    ok(f"Tools com aprovacao (escrita/destrutiva): {len(requires_approval)}")

    # Verify categories
    read_tools = [t for t in TOOL_REGISTRY.values() if t["category"] == "read"]
    write_tools = [t for t in TOOL_REGISTRY.values() if t["category"] == "write"]
    destructive_tools = [t for t in TOOL_REGISTRY.values() if t["category"] == "destructive"]

    ok(f"Categorias: {len(read_tools)} leitura, {len(write_tools)} escrita, {len(destructive_tools)} destrutiva")

    # All read tools should be auto-approved
    all_read_auto = all(not t["requires_approval"] for t in read_tools)
    all_write_approval = all(t["requires_approval"] for t in write_tools)
    all_destructive_approval = all(t["requires_approval"] for t in destructive_tools)

    if all_read_auto:
        ok("Todas as tools de leitura sao autonomas")
    else:
        fail("Alguma tool de leitura exige aprovacao (incorreto)")

    if all_write_approval:
        ok("Todas as tools de escrita exigem aprovacao")
    else:
        fail("Alguma tool de escrita nao exige aprovacao (incorreto)")

    if all_destructive_approval:
        ok("Todas as tools destrutivas exigem aprovacao")
    else:
        fail("Alguma tool destrutiva nao exige aprovacao (incorreto)")

    return all_read_auto and all_write_approval and all_destructive_approval


# ============================================================
# NIVEL 3 — Memoria da Ahri: persiste, filtra, versiona?
# ============================================================

def validate_level_3():
    section("Nivel 3 — Memoria da Ahri: persiste, filtra rigorosamente?")

    ahri_memory_dir = ROOT / "ahri_memory"
    if not ahri_memory_dir.exists():
        fail("ahri_memory/ nao existe")
        return False

    ok("ahri_memory/ existe")

    git_sync_path = ahri_memory_dir / "git_sync.py"
    if git_sync_path.exists():
        ok("ahri_memory/git_sync.py existe")
    else:
        fail("ahri_memory/git_sync.py nao existe")

    try:
        from ahri_memory import read_memory, write_memory, should_register
        ok("ahri_memory.read_memory(), write_memory(), should_register() importaveis")
    except ImportError:
        fail("ahri_memory nao importavel")
        return False

    # Test write/read
    try:
        test_entry = {
            "id": f"validate_test_{__import__('time').time()}",
            "type": "interaction",
            "summary": "entrada de teste do validate — filtro rigoroso",
            "relevance": "medium"
        }
        write_memory(test_entry)
        ok("write_memory() executa sem erro")

        memory = read_memory()
        if any(e.get("id") == test_entry["id"] for e in memory if isinstance(e, dict)):
            ok("read_memory() retorna entrada escrita")
        else:
            fail("read_memory() nao retornou a entrada escrita")
            return False
    except Exception as e:
        fail(f"Erro ao testar memoria: {e}")
        return False

    # Test enhanced filters
    if should_register({"type": "feedback", "summary": "teste", "relevance": "high"}):
        ok("Feedback explicito: deve registrar")
    else:
        fail("Feedback explicito: deveria registrar")
        return False

    if not should_register({"type": "casual", "summary": "Bom dia", "relevance": "none"}):
        ok("Conversa casual: nao deve registrar")
    else:
        fail("Conversa casual: nao deveria registrar")
        return False

    if not should_register({"type": "interaction", "summary": "hi", "relevance": "medium"}):
        ok("Resumo curto: nao deve registrar")
    else:
        fail("Resumo curto: deveria ser rejeitado")
        return False

    if not should_register({"type": "error_resolved", "summary": "Trello falhou 3x, resolvido", "relevance": "high"}):
        fail("Erro resolvido deveria registrar")
        return False
    ok("Erro resolvido: deve registrar")

    # Cleanup
    try:
        from ahri_memory.git_sync import _load_index, _save_index
        index = _load_index()
        index["entries"] = [e for e in index.get("entries", []) if not e.get("id", "").startswith("validate_test_")]
        index["stats"]["total"] = len(index["entries"])
        _save_index(index)
    except Exception:
        pass

    return True


# ============================================================
# NIVEL 4 — Executor: ciclo de vida de acoes via estado?
# ============================================================

def validate_level_4():
    section("Nivel 4 — Executor: ciclo de vida completo de acoes?")

    executor_path = ROOT / "executor.py"
    if not executor_path.exists():
        fail("executor.py nao existe")
        return False

    ok("executor.py existe")

    try:
        from executor import create_action, executor_cycle, approve_action, reject_action, get_action_result
        ok("executor funcoes importaveis")
    except ImportError as e:
        fail(f"Executor nao importavel: {e}")
        return False

    # Test action lifecycle: read (auto-approved)
    try:
        act_id = create_action("trello_test", source="validate", priority="normal")
        ok(f"Acao de leitura criada: {act_id}")
    except Exception as e:
        fail(f"create_action() falhou: {e}")
        return False

    # Check status
    from state import read_state
    state = read_state()
    action = [a for a in state.get("pending_actions", []) if a.get("id") == act_id]
    if not action:
        fail("Acao nao encontrada no estado")
        return False

    if action[0].get("status") == "pending":
        ok("Acao de leitura: status = pending (auto-aprovada)")
    else:
        fail(f"Acao de leitura: status = {action[0].get('status')} (esperava pending)")
        return False

    if not action[0].get("requires_approval"):
        ok("Acao de leitura: requires_approval = False")
    else:
        fail("Acao de leitura exige aprovacao (incorreto)")
        return False

    # Test action lifecycle: write (needs approval)
    try:
        act_id2 = create_action("trello_create_card", params={"title": "Validate Test"},
                                 source="validate", priority="normal")
        ok(f"Acao de escrita criada: {act_id2}")
    except Exception as e:
        fail(f"create_action() para escrita falhou: {e}")
        return False

    state = read_state()
    action2 = [a for a in state.get("pending_actions", []) if a.get("id") == act_id2]
    if action2 and action2[0].get("status") == "pending_approval":
        ok("Acao de escrita: status = pending_approval")
    else:
        fail("Acao de escrita deveria estar pending_approval")
        return False

    if action2 and action2[0].get("requires_approval"):
        ok("Acao de escrita: requires_approval = True")
    else:
        fail("Acao de escrita deveria exigir aprovacao")
        return False

    # Approve
    if approve_action(act_id2, approved_by="validate"):
        ok("approve_action() funciona")
    else:
        fail("approve_action() falhou")
        return False

    # Run executor
    executor_cycle()

    # Check result
    state = read_state()
    action_after = [a for a in state.get("pending_actions", []) if a.get("id") == act_id]
    if action_after:
        status = action_after[0].get("status")
        if status in ("done", "failed", "failed_permanent"):
            ok(f"Executor executou acao de leitura: status = {status}")
        else:
            fail(f"Executor nao executou: status = {status}")
            return False

    result_ref = action_after[0].get("result_ref", "") if action_after else ""
    result = state.get("results", {}).get(result_ref, {})
    if result:
        ok(f"Resultado registrado em results[]: {result.get('status')}")
    else:
        fail("Resultado nao encontrado em results[]")
        return False

    # Cleanup
    state = read_state()
    state["pending_actions"] = []
    state["results"] = {}
    from state import write_state
    write_state(state, agent="validate", reason="level_4_cleanup")

    return True


# ============================================================
# NIVEL 5 — Autonomia correta: leitura=autonoma, escrita=aprovacao?
# ============================================================

def validate_level_5():
    section("Nivel 5 — Autonomia: leitura=autonoma, escrita=aprovacao?")

    try:
        from executor import create_action, get_pending_approvals
        from state import read_state, write_state
    except ImportError as e:
        fail(f"Importacao falhou: {e}")
        return False

    # Create read action — should be auto-approved
    act_read = create_action("supabase_health", source="validate")
    state = read_state()
    action = [a for a in state["pending_actions"] if a["id"] == act_read][0]

    if action["status"] == "pending" and not action["requires_approval"]:
        ok("Leitura: auto-aprovada (status=pending, requires_approval=False)")
    else:
        fail("Leitura deveria ser auto-aprovada")
        return False

    # Create write action — should need approval
    act_write = create_action("gmail_compose", params={"to": "test@test.com", "subject": "test", "body": "test"},
                               source="validate")
    state = read_state()
    action2 = [a for a in state["pending_actions"] if a["id"] == act_write][0]

    if action2["status"] == "pending_approval" and action2["requires_approval"]:
        ok("Escrita: requer aprovacao (status=pending_approval, requires_approval=True)")
    else:
        fail("Escrita deveria requerer aprovacao")
        return False

    # Create destructive action — should need approval
    act_delete = create_action("gmail_delete", params={"message_id": "test"},
                                source="validate")
    state = read_state()
    action3 = [a for a in state["pending_actions"] if a["id"] == act_delete][0]

    if action3["status"] == "pending_approval" and action3["requires_approval"]:
        ok("Destrutiva: requer aprovacao")
    else:
        fail("Acao destrutiva deveria requerer aprovacao")
        return False

    # Verify approval timeout
    if action2.get("approval_expires_at"):
        ok("Acao com aprovacao tem expiry configurado")
    else:
        fail("Acao com aprovacao nao tem expiry")

    # Cleanup
    state["pending_actions"] = []
    state["results"] = {}
    write_state(state, agent="validate", reason="level_5_cleanup")

    return True


# ============================================================
# NIVEL 6 — Proatividade: sistema de prioridade?
# ============================================================

def validate_level_6():
    section("Nivel 6 — Proatividade: sistema de prioridade e anti-ruido?")

    try:
        from agents.ahri import send_notification, _can_notify
        from state import read_state, write_state
    except ImportError as e:
        fail(f"Importacao falhou: {e}")
        return False

    state = read_state()

    # Test priority logic
    if _can_notify("critica", state):
        ok("Prioridade critica: sempre pode notificar")
    else:
        fail("Prioridade critica deveria sempre passar")
        return False

    # Test anti-noise: pending_digest exists
    if "pending_digest" in state.get("proactivity", {}):
        ok("Sistema de digest existe no estado")
    else:
        fail("pending_digest nao encontrado no estado")

    # Test scheduler exists
    scheduler_path = ROOT / "scheduler.py"
    if scheduler_path.exists():
        ok("scheduler.py existe")
    else:
        fail("scheduler.py nao existe")
        return False

    # Check default crons
    if "crons" in state:
        ok("Secao crons existe no estado")
    else:
        fail("Secao crons nao encontrada")

    return True


# ============================================================
# NIVEL 7 — Schema v2.0.0 completo?
# ============================================================

def validate_level_7():
    section("Nivel 7 — Schema v2.0.0: todas as secoes existem?")

    from state import read_state
    state = read_state()

    required_sections = [
        "meta", "clients", "tasks", "modules", "crons", "llm",
        "ahri", "intentions", "pending_actions", "results", "calendar_sync",
        "proactivity", "integrations"
    ]

    missing = [s for s in required_sections if s not in state]
    if missing:
        fail(f"Secoes ausentes: {', '.join(missing)}")
        return False

    ok(f"Todas as {len(required_sections)} secoes existem")

    # Check ahri sub-fields
    ahri = state.get("ahri", {})
    ahri_fields = ["audit_mode", "audit_scope", "audit_expires_at", "conversation_history", "auto_approved_patterns"]
    missing_ahri = [f for f in ahri_fields if f not in ahri]
    if missing_ahri:
        fail(f"Campos ahri ausentes: {', '.join(missing_ahri)}")
        return False

    ok(f"Ahri: todos os {len(ahri_fields)} campos existem")

    # Check version
    version = state.get("meta", {}).get("version", "")
    if version == "2.0.0":
        ok("Versao do schema: 2.0.0")
    else:
        fail(f"Versao do schema: {version} (esperava 2.0.0)")
        return False

    return True


# ============================================================
# NIVEL 8 — Auditoria e LLM no estado?
# ============================================================

def validate_level_8():
    section("Nivel 8 — Auditoria e LLM: mecanismos existem?")

    try:
        from agents.ahri import start_audit, stop_audit, is_audit_active
        ok("Funcoes de auditoria importaveis")
    except ImportError as e:
        fail(f"Funcoes de auditoria nao importaveis: {e}")
        return False

    from state import read_state
    state = read_state()

    # Check LLM section
    llm = state.get("llm", {})
    if llm.get("current_model"):
        ok(f"Secao LLM existe: modelo atual = {llm['current_model']}")
    else:
        fail("Secao LLM incompleta")
        return False

    # Test audit flow
    start_audit("general", duration_minutes=5)
    state = read_state()
    if state["ahri"]["audit_mode"]:
        ok("start_audit() ativa modo auditoria")
    else:
        fail("start_audit() nao ativou auditoria")
        return False

    stop_audit()
    state = read_state()
    if not state["ahri"]["audit_mode"]:
        ok("stop_audit() desativa modo auditoria")
    else:
        fail("stop_audit() nao desativou auditoria")
        return False

    return True


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Validate v2 — Checks objetivos")
    parser.add_argument("--level", type=int, default=None,
                        help="Nivel especifico (0-8). Default: todos os niveis.")
    args = parser.parse_args()

    print("\n==================================================")
    print("  OpenClaw — Validate v2")
    print("==================================================")

    levels = {
        0: ("Estado (state + merge + atomico)", validate_level_0),
        1: ("Ahri conversacional", validate_level_1),
        2: ("Tool registry unificado", validate_level_2),
        3: ("Memoria com filtros rigorosos", validate_level_3),
        4: ("Executor: ciclo de vida", validate_level_4),
        5: ("Autonomia correta", validate_level_5),
        6: ("Proatividade e prioridade", validate_level_6),
        7: ("Schema v2.0.0 completo", validate_level_7),
        8: ("Auditoria e LLM", validate_level_8),
    }

    if args.level is not None:
        if args.level not in levels:
            print(f"\n  [X] Nivel invalido: {args.level}. Use 0-8.\n")
            return
        name, fn = levels[args.level]
        passed = fn()
        status = "PASSOU" if passed else "FALHOU"
        print(f"\n  [{status}] Nivel {args.level} ({name})\n")
    else:
        results = {}
        for level, (name, fn) in levels.items():
            passed = fn()
            results[level] = passed
            mark = "OK" if passed else " X"
            print(f"  [{mark}] Nivel {level} ({name})")
        print(f"\n  Total: {sum(results.values())}/{len(results)} passaram\n")


if __name__ == "__main__":
    main()