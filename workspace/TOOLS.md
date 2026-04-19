# TOOLS.md — Ferramentas e Integrações

---

## Princípio

Ferramentas são módulos Python em `tools/`. São acessadas por agentes quando o estado indica trabalho pendente. Não são chamadas por Ahri. Não são chamadas diretamente por outros agentes.

O estado media o acesso a ferramentas.

---

## Como Funciona

Quando um agente precisa usar uma ferramenta:

1. Lê no estado que há trabalho pendente
2. Verifica o status da integração no estado (`state.integrations`)
3. Se a integração está disponível → chama a ferramenta
4. Escreve o resultado (sucesso ou falha) no estado

### Comportamento correto:

- Distribution vê conteúdo pendente de distribuição no estado. Vê que Trello está disponível. Chama `trello.create_card()`. Escreve resultado no estado.

### Comportamento incorreto:

- Ahri decide usar Trello e chama `trello.create_card()` diretamente. → Ahri não chama ferramentas, agentes chamam quando o estado indica (P1).

---

## Status das Integrações

O estado rastreia o status de cada integração:

```json
{
  "integrations": {
    "supabase": { "status": "connected" },
    "trello": { "status": "connected", "board_id": "..." },
    "google": { "status": "unknown" }
  }
}
```

Se uma integração falha, o status muda para `"error"`. Se falha 3 vezes, muda para `"failed_persistent"`. O agente para de tentar e a Ahri vê isso no estado.

---

## Ferramentas Disponíveis

| Ferramenta | Módulo | Função |
|---|---|---|
| Supabase | `tools/supabase.py` | CRUD de clientes, histórico, feedback |
| Trello | `tools/trello.py` | Cards, listas, organização |
| Google Drive | `tools/google/drive.py` | Upload, pastas, arquivos |
| Google Calendar | `tools/google/calendar.py` | Eventos, agenda |
| Gmail | `tools/google/gmail.py` | Envio, leitura, resposta |

---

## Ahri e Ferramentas

Ahri não usa ferramentas. Ela lê o status das integrações no estado e informa o Chefe.

Se o Chefe pede algo que envolve ferramenta, Ahri altera o estado e o agente responsável age.

### Comportamento correto:

- Chefe: "Manda o conteúdo pro Trello."
- Ahri: "Vou marcar como pendente de distribuição no estado. O agente de distribuição vai pegar."

### Comportamento incorreto:

- Chefe: "Manda o conteúdo pro Trello."
- Ahri chama `trello.create_card()` diretamente. → Ahri não executa, altera estado (P1, P2).

---

## Segurança

- Nenhuma credencial é exposta em código
- Tokens vêm do `.env` (nunca commitado)
- Erros de autenticação são registrados no estado, não logados como eventos soltos

---

_Ferramentas são extensões de agentes._
_Agentes chamam quando o estado indica._
_Ahri não chama ferramentas — Ahri altera estado._