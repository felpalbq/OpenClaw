# AGENTS.md — Módulos Acopláveis do Sistema

> **Nota de implementação (para o Claude Code):**
> Este arquivo descreve módulos do ponto de vista da PERCEPÇÃO DO USUÁRIO.
> Na execução real: módulos são funções Python acopláveis com crons.
> Interface padrão: condition(state) → bool, act(state, context) → result, write_state(result).
> Acoplamento = cron registrada + LLM configurada + skills carregadas.
> Desacoplamento = cron suspensa + LLM não chamada + skills descarregadas.
> Comunicação entre módulos = leitura e escrita no estado. Nunca chamada direta.
> "Agente contratado por Ahri" = módulo acoplado via estado. Não há chamada direta.
> Ver d_arch_011 e d_arch_014 no Claudinho.

---

## Princípio

Agentes não são cargos fixos. Não são roles. Não são posições em um organograma.

Cada agente é definido por três coisas:

1. **O que lê** no estado
2. **Quando age** (condição)
3. **O que escreve** de volta no estado

Agentes não se chamam. Não dependem de comando. Não esperam instrução da Ahri.

---

## Como Agentes Funcionam

Um agente age quando sua condição é atendida. Não age quando não é.

A condição é uma verificação do estado: "há algo para eu fazer?"

Se a verificação retorna verdadeiro → age.
Se retorna falso → não faz nada. Próximo ciclo verifica de novo.

### Comportamento correto:

- Writer verifica o estado, vê que há estratégia pronta sem texto, escreve.

### Comportamento incorreto:

- Writer espera a Ahri enviar um sinal de "agora pode escrever". → agentes agem por condição, não por comando (P2).

---

## Dependência entre Agentes

Agentes não dependem de chamadas diretas entre si. Mas dependem do estado conter condições válidas.

O Writer não depende do Architect diretamente. Mas depende do estado conter algo para escrever.

### Comportamento correto:

- Architect age, escreve estratégia no estado. Writer verifica no próximo ciclo, vê estratégia sem texto, age. Nenhum dos dois chamou o outro.

### Comportamento incorreto:

- Architect chama `writer.execute(plan)`. → agentes se comunicam pelo estado, nunca diretamente (P1).

---

## Validação

Conteúdo rejeitado volta ao estado como "rejeitado, motivo X". O agente responsável decide o que fazer.

Nenhum gate bloqueia o sistema. Validação informa, não trava (P8).

### Comportamento correto:

- Estratégia rejeitada → estado marca "rejeitada: tom inadequado". Architect vê no próximo ciclo e reescreve.

### Comportamento incorreto:

- Gate rejeita texto → toda produção para até aprovação manual. → validação não é bloqueio (P8).

---

## Estado Incompleto

Se faltam dados para agir, o agente não age e não reclama. O próximo ciclo verifica de novo. Quem resolve inconsistências é a Ahri (P5).

### Comportamento correto:

- Writer vê demanda sem estratégia → faz nada, próximo ciclo verifica.

### Comportamento incorreto:

- Writer gera estratégia improvisada porque a oficial não existe. → agente não improvisa, não reclama (P5).

---

## Falha

Ação que falha é registrada com contador. Após 3 tentativas, marca como falha persistente e para. Ahri resolve (P4).

### Comportamento correto:

- API do Trello falha 3 vezes → estado marca "falha_persistente", Distribution para de tentar aquele canal.

### Comportamento incorreto:

- Distribution tenta entregar infinitamente a cada ciclo. → falha tem limite (P4).

---

## Agentes Atuais

| Agente | Lê | Condição | Escreve |
|---|---|---|---|
| Client Sync | clients, integrations.supabase | Supabase não conectado + sem sync recente | clients, integrations.supabase |
| Trend Detection | trends, clients | Cron tick | trends.opportunities, trends.notified |
| Content Strategy | clients, content.ideas, content.in_progress, trends | Há ideia sem estratégia para o cliente | content.in_progress |
| Content Writer | content.in_progress, clients | Há item com estratégia pronta sem texto | content.pending_review, content.in_progress |
| Distribution | content.pending_distribution, distributions, integrations | Há conteúdo aprovado pendente + integração não falhou | distributions, content.distributed, integrations |
| Task Org | tasks, clients, content | Há tarefas abertas sem prioridade ou bloqueadas sem motivo | tasks |

---

## Adicionar um Novo Agente

1. Criar módulo Python em `agents/`
2. Definir: o que lê, condição, o que escreve
3. Registrar no cron_runner
4. Pronto. Sem handshake, sem registro central, sem aprovação (P10).

---

## Remover um Agente

1. Apagar o módulo
2. Remover do cron_runner
3. Pronto.

---

_Agentes são funções._
_Lêem, verificam, agem._
_Não esperam comando. Não chamam ninguém._
_O estado é o único mediador._