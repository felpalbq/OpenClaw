# LAYER CONTRACTS — Camadas do Sistema

---

## Visão Geral

O OpenClaw tem 3 camadas, cada uma com responsabilidade e ciclo de vida distintos. Não existe pipeline entre elas. O estado é o mediador.

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

## ESTRATÉGIA — Ahri (futuro)

**Natureza:** persistente, versionada por cliente, aprende com tempo
**Localização:** futuro — memória estratégica separada

### Responsabilidade (quando implementada)

- Histórico de decisões estratégicas
- Aprendizado por cliente
- Adaptação baseada em performance histórica

### Contrato com Estado

- Ahri lê estado para contexto imediato
- Ahri altera estado apenas nas 6 condições de P6
- Ahri NÃO orquestra agentes — agentes leem estado e agem por condição

---

## Fluxo de Dados

Não existe pipeline. O fluxo é:

```
Estado ← → Agentes (crons verificam condições, agem, escrevem resultado)
   ↑↓
  Ahri (lê estado, conversa com Chefe, altera estado quando intencional)
```

Não há setas entre agentes. Não há sequência. Há um campo compartilhado — o estado — e agentes que operam sobre ele quando podem.

### Comportamento correto:

- Architect age → escreve estratégia no estado. Writer verifica → vê estratégia → age. Nenhum chamou o outro.

### Comportamento incorreto:

- Input → Interpreter → Decider → Generator → Quality → Response. Isso é pipeline. Não é como o sistema funciona (P1).

---

## RESUMO

| Camada | O quê | Onde | Ciclo de vida |
|---|---|---|---|
| **Comportamento** | Layouts, constraints, estilos | `workspace/layouts/` | Git (código) |
| **Estado** | Hub contínuo — clientes, conteúdo, tarefas, distribuições | `state/state.json` | Persistente |
| **Estratégia** | Aprendizado, histórico, adaptação | Futuro | Permanente + versionado |