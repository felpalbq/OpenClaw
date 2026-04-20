# Modo de Teste do OpenClaw — Fase 1

## O que é

Infraestrutura para testar o sistema sem tocar em dados reais ou integrações de produção.

**Foco da Fase 1:** Ahri funcional + memória persistente. Nenhum módulo especialista.

São dois scripts:
- **inject.py** — injeta dados sintéticos no estado
- **validate.py** — verifica condições objetivas sobre Ahri e memória

## O que NÃO é

- Não é runner de testes, não orquestra execução, não chama módulos
- **Regra de ouro:** se você apagar `tests/`, o sistema funciona igual

---

## STATE_FILE

| Variável | Valor | Significado |
|---|---|---|
| `STATE_FILE` | `state.json` | Produção |
| `STATE_FILE` | `state_test.json` | Testes |

O módulo `state/` decide qual arquivo usar. Agentes nunca sabem.

---

## Níveis de Validação (independentes)

| Nível | Pergunta | Verifica |
|---|---|---|
| 0 | O módulo state funciona? | read_state/write_state sem erro |
| 1 | Ahri responde sem inventar? | agents/ahri.py existe, ask() retorna com base no estado |
| 2 | Ahri usa tools? | tools importáveis, Ahri tem acesso |
| 3 | Memória persiste e recupera? | ahri_memory/ existe, write/read funcionam |
| 4 | Filtro de memória funciona? | should_register() aceita relevante, rejeita ruído |

---

## Uso

```bash
# Injetar dados
python tests/inject.py

# Validar nível específico
python tests/validate.py --level 0

# Validar todos
python tests/validate.py
```

---

## Estrutura de arquivos

```
tests/
├── __init__.py
├── inject.py              # Injeta dados sintéticos (merge, nunca substitui)
├── validate.py             # 5 níveis independentes (Ahri + memória)
├── MODO_DE_TESTE.md       # Este arquivo
└── fixtures/
    ├── __init__.py
    ├── client_test.json    # Cliente fictício Bella Estética
    ├── task_test.json      # 3 tarefas em diferentes estados
    └── state_test.json     # Estado base com meta, clients, tasks, modules, ahri
```