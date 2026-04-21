# LAYER CONTRACTS — Camadas do Sistema

---

## Visão Geral

O OpenClaw tem 4 camadas, cada uma com responsabilidade e ciclo de vida distintos. Não existe pipeline entre elas. O estado é o mediador.

---

## COMPORTAMENTO — Layouts

**Natureza:** estática, versionada, imutável em runtime
**Localização:** `workspace/layouts/`
**Persistência:** Git (como código)

### Regras

- Layouts são código, não dados
- Nunca modificados em runtime
- Alterações viram commits, não overrides em memória

### Arquivos

- `_core/CONTENT_ENGINE_CONTRACT.md` — contrato: estilo antes de conteúdo
- `_core/GLOBAL_CONSTRAINTS.md` — constraints de texto, largura, densidade
- `_core/GLOBAL_LAYOUT_UPDATE.md` — canvas padrão e safe area
- `_core/GLOBAL_STRUCTURE_ADJUSTMENTS.md` — ideia por slide, fluxo, overlay
- `style_XX_<name>/STYLE.md` — quando usar, características
- `style_XX_<name>/LAYOUT.md` — canvas, grid, estrutura visual
- `style_XX_<name>/CONTENT_STRUCTURE.md` — blocos, organização
- `style_XX_<name>/CONTENT_RENDERING.md` — linhas visuais, espaçamento

---

## INTENÇÃO — Intent Layer

**Natureza:** transitória, linguagem natural, mediadora entre interpretação e execução
**Localização:** `state.intentions` (campo no estado)
**Persistência:** disco local (JSON, parte do estado)

### Regras

- Intenções são registradas pela Ahri em linguagem natural — nunca estruturadas
- Intent_resolver traduz intenções para ações estruturadas (tool + params)
- Intenções ambíguas ficam em status `ambiguous` — Ahri pede clarificação ao usuário
- Intenções irresolvíveis ficam em status `unresolvable`
- Intenções resolvidas vinculam-se à ação criada via `resolved_action_id`
- Cleanup automático após 1 hora para intenções terminais

### Ciclo

```
Ahri (interpreta) → state.intentions (NL) → intent_resolver (traduz + valida) → state.pending_actions (estruturado) → executor
```

### Comportamento correto:

- Ahri detecta intenção operacional → registra texto natural em intentions
- Intent_resolver lê intenção → mapeia para tool → valida → cria pending_action
- Intent_resolver incerto → marca como ambiguous → Ahri pergunta ao Chefe

### Comportamento incorreto:

- Ahri estrutura a ação (escolhe tool, monta params) — isso é papel do intent_resolver
- Intent_resolver executa a ação — ele só traduz, o executor executa
- Ahri chama ferramentas diretamente — Ahri altera estado, não executa

---

## ESTADO — State Contínuo

**Natureza:** persistente, contínuo, hub do sistema
**Localização:** `state/state.json`
**Persistência:** disco local (JSON)

### Regras

- O estado é o hub — agentes leem e escrevem aqui
- Toda mutação registra agente, timestamp e motivo (P3)
- action_log é FIFO de 50 — auditoria sem bloqueio
- Estado incompleto não é erro — agente não age e não reclama (P5)
- Estado inconsistente é marcado, não corrigido pelo agente — Ahri resolve

### Comportamento correto:

- Writer vê demanda sem estratégia → não age, próximo ciclo verifica
- Distribution falha 3 vezes → marca "falha_persistente" no estado, para de tentar
- Toda mutação tem `agent` e `reason` no action_log

### Comportamento incorreto:

- Writer improvisa estratégia porque está faltando (P5)
- Distribution tenta infinitamente (P4)
- Mutação no estado sem registrar quem fez e por quê (P3)

---

## MEMÓRIA — HQ Memory + External Memory

**Natureza:** persistente, curada, pareada
**Localização:** `memory/` (HQ — .md legível) + `ahri/` repo (externa — .json programático)

### Regras

- **HQ memory** (`memory/`): projeção operacional curada, editável pelo Chefe, formato .md. NÃO é fonte de verdade — é reflexo.
- **External memory** (`ahri/`): fonte primária de aprendizado, orgânica, versionada em Git, mantida por pipeline, formato .json. Em conflito com memory/, prevalece.
- **Pareamento:** ahri/ gera, memory/ reflete. Tudo no HQ tem correspondente no externo. Nem tudo no externo vira entrada no HQ.
- **Influência reversa indireta:** memory/ → contexto → Ahri → comportamento → sessions → pipeline → ahri/. Não inverte o pareamento — é influência operacional, não fonte de verdade.
- **São resoluções diferentes da mesma informação** — não duplicam, pareiam

### Contrato com Estado

- Ahri lê estado para contexto imediato
- Ahri altera estado apenas nas 6 condições de P6
- Ahri NÃO orquestra agentes — agentes leem estado e agem por condição
- Ahri acessa HQ memory para contexto operacional, NÃO lê sessions diretamente
- OpenClaw é funcional sem ahri_memory, Ahri é limitada sem — sistema completo depende da integração

---

## Fluxo de Dados

Não existe pipeline. O fluxo é:

```
Estado ← → Agentes (crons verificam condições, agem, escrevem resultado)
   ↑↓
  Ahri (lê estado, conversa com Chefe, registra intenção quando operacional)
   ↓
  state.intentions (linguagem natural)
   ↓
  Intent Resolver (traduz intenção → ação estruturada, valida contra registry)
   ↓
  state.pending_actions (estruturado)
   ↓
  Executor (executa, escreve resultado)
```

Não há setas entre agentes. Não há sequência. Há um campo compartilhado — o estado — e componentes que operam sobre ele quando podem.

### Comportamento correto:

- Ahri detecta intenção → registra em intentions. Intent_resolver traduz → cria pending_action. Executor executa. Nenhum chamou o outro.

### Comportamento incorreto:

- Ahri → ACTION:tool|params → pending_action → executor. Isso é pipeline + Ahri como parser. Não é como o sistema funciona.

---

## RESUMO

| Camada | O quê | Onde | Ciclo de vida |
|---|---|---|---|
| **Comportamento** | Layouts, constraints, estilos | `workspace/layouts/` | Git (código) |
| **Intenção** | Tradução NL → ação estruturada | `state.intentions` + `intent_resolver.py` | Transitório (1h) |
| **Estado** | Hub contínuo — clientes, conteúdo, tarefas, distribuições | `state/state.json` | Persistente |
| **Estratégia** | Aprendizado, histórico, adaptação | `memory/` + `ahri/` | Permanente + versionado + pareado |