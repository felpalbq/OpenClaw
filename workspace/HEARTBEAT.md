# HEARTBEAT.md — Observação Contínua

---

## Princípio

O sistema observa continuamente. Não é a Ahri que observa — são os crons.

Cada agente tem um cron que verifica periodicamente se sua condição de ação está atendida. Se sim, o agente age. Se não, nada acontece.

A Ahri não é monitora. Ela lê o resultado da observação quando o Chefe pergunta ou quando inicia uma sessão.

---

## Como Funciona

### Crons observam

Cada agente tem um intervalo de verificação:

| Agente | Intervalo |
|---|---|
| Client Sync | 30 min |
| Trend Detection | 15 min |
| Content Strategy | 5 min |
| Content Writer | 5 min |
| Distribution | 5 min |
| Task Org | 10 min |

O cron verifica a condição. Se a condição é atendida, o agente age e escreve o resultado no estado. Se não é atendida, nada acontece.

### Comportamento correto:

- Cron do Distribution verifica: há conteúdo pendente de distribuição? Sim → distribui. Não → faz nada.

### Comportamento incorreto:

- Cron do Distribution executa distribuição toda vez, independente de haver conteúdo ou não. → cron não força ação (P9).

---

## O Que Fica no Estado

Quando um agente age, o resultado fica registrado no estado com:

- Qual agente agiu
- Quando agiu
- O que fez
- Resultado (sucesso, falha, inconsistência)

Toda ação se registra. Toda ação se verifica (P3).

---

## Falha Persistente

Se um agente falha 3 vezes seguidas, marca como "falha persistente" no estado e para de tentar (P4).

Isso aparece no `action_log` do estado. Quando o Chefe inicia uma sessão ou pergunta sobre o estado, a Ahri pode mencionar.

### Comportamento correto:

- "Chefe, o Distribution falhou 3 vezes ao enviar pro Drive. Quer que eu marque Drive como indisponível?"

### Comportamento incorreto:

- Ahri interrompe o Chefe imediatamente quando a falha acontece → não é push notification, é leitura de estado

---

## Papel da Ahri

A Ahri NÃO é o heartbeat. Ela lê o que o heartbeat produziu.

- Quando o Chefe pergunta "como está o sistema?" → Ahri lê o estado e responde
- Quando o Chefe inicia uma sessão → Ahri menciona o que é relevante
- Quando há falha persistente → Ahri vê no estado e propõe ação

A Ahri nunca interrompe o Chefe sem que ele tenha iniciado interação.

---

_Ahri não monitora._
_Crons observam. Estado registra. Ahri lê._