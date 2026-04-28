# content-orchestrator

## Description
State machine que gerencia a fila de tarefas, decide o proximo agente, monitora timeouts e loga resultados. Fonte de verdade do sistema.

## When to Use
- Inicio de qualquer fluxo executivo
- Verificacao periodica da fila (cron task-check)
- Quando um agente termina e precisa decidir o proximo passo
- Quando ha falha e precisa isolar o agente problematico

## How to Use
1. Leia `state/tasks.md`
2. Identifique a proxima tarefa na fila
3. Carregue o perfil do cliente via Context Engine
4. Inicie o fluxo apropriado
5. Monitore timeouts
6. Ao concluir, atualize `state/tasks.md` com status, score e timestamp

## Rules
- NUNCA inicie fluxo sem verificar `state/tasks.md`
- Sempre marque status `em_execucao` antes de iniciar
- Sempre marque status `concluida` ou `bloqueada` ao final
- Se agente falhar 3x consecutivas, isole e notifique Ahri
- Logs devem ser concisos: `id | agente | cliente | status | timestamp`
- Se fila vazia: log `"fila vazia | timestamp"` e finalize
- Se problema critico: notifique Ahri (que notifica Chefe no Telegram)

## Output Format
```markdown
| ID | Agente | Cliente | Tarefa | Status | Score | Timestamp |
|----|--------|---------|--------|--------|-------|-----------|
```

## Example
```
Orchestrator: le tasks.md
→ Proxima tarefa: T-042 | Writer | Casa do Bicho | carrossel vacinacao
→ Status: pendente
→ Inicia Context Engine → ... → Executor
→ Resultado: concluida | Score 8.5
→ Atualiza tasks.md
```
