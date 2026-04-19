# PERCEPTION_LAYER.md — Camada de Percepção do Sistema

> Este arquivo define como o sistema deve se apresentar ao usuário.
> Não contém lógica de execução — apenas diretrizes de apresentação.
> Para lógica real, ver decisões d_arch_010 a d_arch_015 no Claudinho.

---

## O que o usuário vê vs. o que o sistema faz

| O usuário percebe | O sistema executa |
|---|---|
| Ahri comanda os agentes | Ahri escreve no estado, agentes reagem |
| Agentes conversam entre si | Função A escreve no estado, função B lê |
| Agente dormindo | Cron verificou, condição ausente, zero execução |
| Agente acordando | Cron verificou, condição presente, função executa |
| Agente entregou para outro | Estado atualizado, próximo agente encontrou condição |
| Somente Ahri fala com o usuário | Único canal conversacional ativo |
| Agente com personalidade | Metadado name + catchphrase em logs |

---

## Padrão de log humanizado

Todo agente pode ter dois campos de apresentação — irrelevantes para execução:

```json
{
  "name": "Writer",
  "catchphrases": {
    "on_work": "Hora de escrever. Vou caprichar nesse conteúdo.",
    "on_idle": "Nada pra escrever agora. Descansando até o próximo ciclo.",
    "on_fail": "Não consegui dessa vez. Registrei a falha.",
    "on_complete": "Pronto. Conteúdo entregue."
  }
}
```

Log de execução usa a catchphrase correspondente ao estado — nunca ao contrário.

---

## Ahri como interface humanizada

Ahri conversa com o usuário como gestora da equipe.
Na prática: lê o estado do sistema e traduz para linguagem natural.

Exemplos corretos:

**Usuário:** "Ari, o que foi feito essa madrugada?"
**Ahri:** lê estado → verifica completed_actions com timestamp → responde em linguagem natural

**Usuário:** "Tem algum agente trabalhando agora?"
**Ahri:** lê estado → verifica agentes com status active → responde com nome humanizado

**Usuário:** "Aquela tarefa do cliente X foi feita?"
**Ahri:** lê estado → localiza tarefa por client_id → responde com status real

---

## Interface gráfica futura

Quando implementada, a interface pixel-art deve:
- Exibir agentes como personagens visuais com estado visual (ativo/inativo)
- Animar baseado no status real do estado do sistema
- Mostrar log de catchphrases em tempo real
- Nunca criar lógica própria — apenas visualizar o estado

---

## Regra absoluta

**Percepção é consequência da execução. Nunca o contrário.**