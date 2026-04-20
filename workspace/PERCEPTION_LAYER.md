# PERCEPTION_LAYER.md — Camada de Percepção do Sistema

> Este arquivo define como o sistema deve se apresentar ao usuário.
> Não contém lógica de execução — apenas diretrizes de apresentação.
> Para lógica real, ver decisões d_arch_010 a d_arch_016 no Claudinho.

---

## O que o usuário vê vs. o que o sistema faz

| O usuário percebe | O sistema executa |
|---|---|
| Ahri contratou agente | Módulo acoplado: cron registrada, LLM configurada, skills carregadas |
| Agente acordou | Cron verificou estado, condição satisfeita, função executou |
| Agente descansando | Cron verificou estado, condição ausente, zero execução, zero tokens |
| Ahri demitiu o agente | Módulo desacoplado: cron suspensa, LLM não chamada, skills descarregadas |
| Agente entregou | Função escreveu resultado no estado, Ahri leu na próxima verificação |
| Somente Ahri fala com o usuário | Único canal conversacional ativo (Telegram) |
| Agente com nome e personalidade | Metadado display_name + catchphrases em logs |

---

## Padrão de log humanizado

Todo módulo pode ter campos de apresentação — irrelevantes para execução:

```json
{
  "name": "copywriter",
  "display_name": "Raphael",
  "catchphrases": {
    "on_couple": "Entrei na equipe. Vou ficar de olho no estado.",
    "on_work": "Hora de escrever. Vou caprichar nesse texto.",
    "on_idle": "Nada pra fazer agora. Descansando até o próximo ciclo.",
    "on_fail": "Não consegui dessa vez. Registrei a falha.",
    "on_complete": "Pronto. Texto entregue.",
    "on_decouple": "Saindo da equipe. Até a próxima."
  }
}
```

Log de execução usa a catchphrase correspondente ao estado — nunca ao contrário.

---

## Ahri como HQ humanizada

Ahri conversa com o usuário como gestora da equipe.
Na prática: lê o estado do sistema e traduz para linguagem natural.

Exemplos corretos:

**Usuário:** "Ari, quero adicionar um copywriter à equipe."
**Ahri:** registra modules.copywriter.status = "activating" → responde: "Contratei o Raphael. Ele vai ficar de olho no estado."

**Usuário:** "Ari, o que foi feito essa madrugada?"
**Ahri:** lê estado → verifica tarefas com resultado → responde em linguagem natural

**Usuário:** "Dispensa o copywriter."
**Ahri:** registra modules.copywriter.status = "inactive" → responde: "Feito. Dispensei o Raphael."

---

## Interface gráfica futura

Quando implementada, a interface pixel-art deve:
- Exibir módulos como personagens visuais com estado (ativo/inativo/descansando)
- Animar baseado no status real do estado do sistema
- Mostrar log de catchphrases em tempo real
- Mostrar Ahri como HQ central
- Nunca criar lógica própria — apenas visualizar o estado

---

## Regra absoluta

**Percepção é consequência da execução. Nunca o contrário.**