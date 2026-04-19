# Modo de Teste do OpenClaw

## O que é

Infraestrutura para testar o sistema sem tocar em dados reais ou integrações de produção.

São dois scripts:

- **inject.py** — injeta dados sintéticos no estado
- **validate.py** — verifica condições objetivas no estado

## O que NÃO é

- Não é um runner de testes
- Não orquestra execução
- Não simula fluxo
- Não chama agentes diretamente
- Não controla quando agentes rodam

**Regra de ouro:** se você apagar `tests/`, o sistema continua funcionando igual.

---

## Como funciona o STATE_FILE

O sistema usa um arquivo de estado para ler e escrever tudo. Qual arquivo é definido no `.env`:

| Variável | Valor | Significado |
|---|---|---|
| `STATE_FILE` | `state.json` | Produção — dados reais |
| `STATE_FILE` | `state_test.json` | Testes — dados sintéticos |

O módulo `state/` lê essa variável e decide qual arquivo usar. Agentes nunca sabem qual arquivo é — eles só chamam `read_state()` e `write_state()`.

Integrações verificam se `STATE_FILE` contém "test" para decidir se retornam mock ou dados reais.

### Na prática

Para testar:

```bash
# 1. Mude no .env
STATE_FILE=state_test.json

# 2. Injete dados sintéticos
python tests/inject.py

# 3. Deixe o sistema rodar (cron ou manual)

# 4. Verifique o resultado
python tests/validate.py --level 2
```

Para voltar a produção:

```bash
# Mude no .env
STATE_FILE=state.json
```

---

## inject.py — Injeta dados, nunca substitui

O inject carrega os fixtures (`client_test.json`, `task_test.json`) e **mescla** no estado existente.

### O que ele faz

1. Lê o estado atual via `read_state()`
2. Carrega fixtures dos arquivos JSON
3. Mescla clientes e tarefas no estado existente
4. Marca `meta.test_data_injected = true` com timestamp
5. Escreve de volta via `write_state()`

### O que ele NÃO faz

- Não substitui o estado inteiro
- Não apaga dados existentes
- Não destrói a estrutura base

### Uso

```bash
python tests/inject.py
```

### Resultado esperado

```
╔══════════════════════════════════════════════════════╗
║     OpenClaw — Inject — Injeta dados sintéticos      ║
╚══════════════════════════════════════════════════════╝

  ✓ Cliente injetado: Bella Estética (TESTE)
  ✓ Tarefas injetadas: 3

  ✓ Dados sintéticos mesclados no estado.
```

Se `state/__init__.py` não existe:

```
  ✗ state/__init__.py não encontrado. Implementar antes de injetar.
    Criar state/__init__.py com read_state() e write_state().
```

---

## validate.py — Verifica, não interpreta

Cada nível responde uma pergunta objetiva sobre o estado atual. Sem inferência, sem narrativa, sem dedução.

### Níveis (independentes — pode rodar qualquer um em qualquer ordem)

| Nível | Pergunta | O que verifica |
|---|---|---|
| 0 | O módulo state funciona? | `state/__init__.py` existe, `read_state()` e `write_state()` funcionam |
| 1 | As integrações respondem? | Cada módulo de integração é importável |
| 2 | Tem resultado de agente? | Estado contém saída de algum agente |
| 3 | Ahri responde? | `agents/ahri.py` existe e `ask()` retorna string |
| 4 | Ciclo completo? | Estado tem tarefa que foi do início ao fim |

### Importante

- Nenhum nível depende de outro
- Nível 2 pode falhar porque nenhum agente rodou ainda — isso é normal, não é erro
- Nível 3 pode falhar porque Ahri não existe ainda — isso é normal
- O validate não chama agentes, não orquestra, não simula

### Uso

```bash
# Rodar nível específico
python tests/validate.py --level 0

# Rodar todos os níveis
python tests/validate.py

# Output detalhado
python tests/validate.py --level 2 --verbose
```

### Resultado esperado (todos os níveis)

```
╔══════════════════════════════════════════════════════╗
║     OpenClaw — Validate — Checks Objetivos           ║
╚══════════════════════════════════════════════════════╝

──────────────────────────────────────────────────
  Nível 0 — Estado: módulo state existe e funciona?
──────────────────────────────────────────────────
  ✓ state/__init__.py existe
  ✓ read_state() e write_state() importáveis
  ✓ write_state() executa sem erro
  ✓ read_state() retorna dado escrito

  ✓ PASSOU — Nível 0 (Estado)

──────────────────────────────────────────────────
  Nível 1 — Integrações: cada uma responde?
──────────────────────────────────────────────────
  ✓ openrouter: módulo importável, key presente
  ✓ tools/google: módulo importável
  ✓ tools/trello: módulo importável
  ✓ tools/supabase: módulo importável

  ✓ PASSOU — Nível 1 (Integrações)

──────────────────────────────────────────────────
  Nível 2 — Agente: estado contém resultado de agente?
──────────────────────────────────────────────────
  ✗ Nenhum resultado de agente encontrado no estado
  → Agente rodou via cron desde a última injeção?

  ✗ FALHOU — Nível 2 (Agente)

...

  Total: 2/5 passaram
```

---

## Dados sintéticos (fixtures)

Localizados em `tests/fixtures/`:

| Arquivo | Conteúdo | Flag |
|---|---|---|
| `client_test.json` | Cliente fictício "Bella Estética" com perfil completo | `_test_only: true` |
| `task_test.json` | 3 tarefas em diferentes estados (pending_architecture, architecture_done) | `_test_only: true` |
| `state_test.json` | Estado inicial de teste com meta, clients, tasks, integrations | `meta.mode: "test"` |

Todos os dados de teste carregam a flag `_test_only: true`. Produção nunca deve usar dados com essa flag.

---

## Fluxo de trabalho completo

### Primeiro teste (quando state/ ainda não existe)

```bash
# 1. Implementar state/__init__.py com read_state() e write_state()
# 2. Validar
python tests/validate.py --level 0
# ✓ PASSOU — módulo state funciona
```

### Teste de integrações

```bash
# 1. Configurar chaves no .env
# 2. Validar
python tests/validate.py --level 1
# ✓ PASSOU — integrações respondem
```

### Teste de agente

```bash
# 1. Injetar dados sintéticos
python tests/inject.py

# 2. Deixar o sistema rodar (cron ou manual)
# O agente lê o estado, verifica condição, age, escreve resultado

# 3. Verificar se algo aconteceu
python tests/validate.py --level 2
# ✓ PASSOU — estado contém resultado de agente
```

### Teste de Ahri

```bash
# 1. Implementar agents/ahri.py com ask()
# 2. Validar
python tests/validate.py --level 3
# ✓ PASSOU — Ahri responde com base no estado
```

### Teste de ciclo completo

```bash
# 1. Injetar dados
python tests/inject.py

# 2. Deixar o sistema rodar um ciclo completo
# (agente lê → age → escreve → outro agente lê → age → escreve)

# 3. Verificar
python tests/validate.py --level 4
# ✓ PASSOU — ciclo completo no estado
```

---

## Voltando a produção

```bash
# 1. Mudar .env
STATE_FILE=state.json

# 2. O sistema volta a ler/escrever no estado de produção
# Dados sintéticos ficam no state_test.json, não afetam produção
```

---

## Arquitetura por trás

Decisão registrada no Claudinho como **d_arch_016**.

Princípios:

1. **Infra de teste é apagável** — se deletar `tests/`, o sistema funciona igual
2. **inject mescla, nunca substitui** — dados de teste são adicionados ao estado existente
3. **validate é objetivo** — verifica chaves e valores, sem interpretar ou deduzir
4. **Níveis são independentes** — cada um pode rodar em qualquer ordem
5. **STATE_FILE elimina lógica paralela** — agentes nunca verificam se estão em teste
6. **Camada de integração mocka** — quando `STATE_FILE` contém "test", integrações retornam mock

---

## Estrutura de arquivos

```
tests/
├── __init__.py
├── inject.py          # Injeta dados sintéticos no estado
├── validate.py        # Verifica condições objetivas (5 níveis)
├── fixtures/
│   ├── __init__.py
│   ├── client_test.json   # Cliente fictício Bella Estética
│   ├── task_test.json     # 3 tarefas em diferentes estados
│   └── state_test.json    # Estado inicial de teste
└── results/            # (gitignored) resultados de validação, se usados
```