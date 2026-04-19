# distribution — Skill de Distribuição

- **version**: 1.0.0
- **condition**: distribution_execution
- **conflicts_with**: []

## Objetivo

Distribuir conteúdo para os canais configurados do cliente com resiliência e idempotência. Cada canal é independente — falha em um não afeta os demais.

## Processo

1. Verificar distribution_log para o package_id (idempotência)
   - Se log NÃO existe para este package_id:
     → Criar novo log com todos os canais como status 'pending'
   - Se log existe:
     → Verificar status de cada canal antes de executar
2. Se canal já tem status success → SKIP
3. Se canal já tem status failed com attempts >= 2 → SKIP
4. Para cada canal habilitado para o cliente:
   a. Tentar execução
   b. Se falhar: 1 retry com backoff 5s
   c. Se falhar 2x: marcar failed e escrever no estado
5. Atualizar distribution_log após cada canal
6. Escrever resultados no estado (sucesso e falha)

## Regras

- Cada canal é INDEPENDENTE — falha em um não afeta os demais
- Verificar distribution_log ANTES de cada canal (idempotência)
- Canal não configurado → status "skipped", não "failed"
- Máximo 2 tentativas por canal (P4)
- Backoff de 5s entre retry
- Nunca reenviar conteúdo já distribuído com sucesso (P3)
- Escrever TODOS os resultados no estado — não notificar Ahri diretamente (P1)
- A Ahri lê o estado se precisar saber o que aconteceu

## Canais

- Drive: upload de arquivo
- Telegram: envio de mensagem
- Email: envio via Gmail
- Trello: criação de card

A sequência de verificação é sugestão, não requisito. Cada canal opera de forma independente.

## Exemplos

### Certo (canais independentes com falha resiliente)

```
Drive: ✓ sucesso — URL gerada
Telegram: ✗ falha (timeout) — retry... ✗ falha — marcado como failed no estado
Email: ✓ sucesso — message_id: abc123
Trello: — skipped (não configurado para este cliente)
```

### Errado (falha bloqueia demais canais)

```
Drive: ✓ sucesso
Telegram: ✗ falha
— PAROU AQUI —
Email: não executado
Trello: não executado
```

Problema: falha em Telegram bloqueou Email e Trello. Canais são independentes (P1, P8).