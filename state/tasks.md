# State Machine — Fila de Tarefas

## Fila Principal
| ID | Agente | Cliente | Tarefa | Status | Timeout | Inicio | Fim |
|----|--------|---------|--------|--------|---------|--------|-----|

## Em Execucao
| ID | Agente | Cliente | Tarefa | Inicio | Timeout | Etapa |
|----|--------|---------|--------|--------|---------|-------|

## Concluidas (ultimas 24h)
| ID | Agente | Cliente | Tarefa | Score | Fim |
|----|--------|---------|--------|-------|-----|
| T-001 | Context Engine | Casa do Bicho | Carregar perfil | 10.0 | 2026-04-28 01:21 |
| T-002 | Intelligence Agent | Casa do Bicho | Pesquisar trends | 9.5 | 2026-04-28 01:23 |
| T-003 | Idea Agent | Casa do Bicho | Gerar angulos v1 | 8.5 | 2026-04-28 01:25 |
| T-004 | Critic Agent | Casa do Bicho | Validar 3 ideias | 8.0 | 2026-04-28 01:27 |
| T-005 | Idea Agent | Casa do Bicho | Gerar angulos v2 (loop) | 9.0 | 2026-04-28 01:29 |

## Bloqueadas
| ID | Agente | Cliente | Tarefa | Motivo | Desde |
|----|--------|---------|--------|--------|-------|

## Ma Experiencias (para evitar repeticao)
| ID | Cliente | Tipo | Motivo | Data |
|----|---------|------|--------|------|
| M-001 | Casa do Bicho | angulo | Reacoes dramaticas na vacina soam desrespeitosas para perfil institucional | 2026-04-28 |
| M-002 | Casa do Bicho | angulo | "5 segundos que salvam" e generico e aula no Instagram — proibido | 2026-04-28 |
