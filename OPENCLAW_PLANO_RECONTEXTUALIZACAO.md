# OpenClaw — Plano de Recontextualização
*Documento para o Claudinho e para o desenvolvimento do sistema*

---

## 1. Visão Central do Produto

O OpenClaw é um **assistente pessoal operacional** acessado via conversa natural pelo Telegram.

Felipe fala com Ahri como falaria com uma assistente real. Ahri entende, age, coordena e reporta. O sistema opera continuamente — com ou sem Felipe presente.

**O que o OpenClaw não é:**
- Sistema especializado em social media
- Pipeline de produção de conteúdo visual
- Substituto para ferramentas dedicadas (Claude Design, Canva AI, etc.)

**O que o OpenClaw é:**
- Base inteligente de propósito geral
- Extensível por domínio via módulos acopláveis
- Operacional 24h via estado contínuo e crons

---

## 2. A Metáfora Operacional: Ahri como HQ de uma Equipe

O sistema se comporta externamente como uma **agência com equipe própria**. Ahri é a gestora. Agentes são colaboradores especializados que ela contrata, gerencia e demite conforme a necessidade do negócio.

Essa metáfora existe em **duas camadas que nunca se misturam:**

### Camada Externa — O que Felipe percebe

| Ação | Experiência do usuário |
|---|---|
| Módulo acoplado | Ahri contrata novo agente para a equipe |
| Módulo ativo com tarefa | Agente acordou, está trabalhando |
| Módulo sem tarefa no estado | Agente está descansando |
| Módulo desacoplado | Ahri demitiu o agente |
| Resultado pronto | Agente entregou para Ahri revisar |
| Falha após 3 tentativas | Agente travou, Ahri reporta e resolve |

### Camada Interna — O que o sistema realmente faz

| Percepção externa | Realidade técnica |
|---|---|
| Ahri contrata agente | Módulo Python ativado, cron registrada, skills carregadas, LLM configurada |
| Agente acordou | Cron verificou estado, condição satisfeita, função executou |
| Agente descansando | Cron verificou estado, condição ausente, zero execução, zero tokens |
| Ahri demitiu agente | Cron desativada, LLM desconfigurada, módulo inativo |
| Agente entregou | Função escreveu resultado no estado, Ahri leu na próxima verificação |

**Regra absoluta:** a camada externa é consequência da camada interna. Nunca o contrário. Nomes, personalidades e frases dos agentes são metadados de apresentação — não afetam lógica, estrutura ou execução.

---

## 3. Estrutura do Sistema

### 3.1 Componentes Permanentes

**Ahri — HQ conversacional**
- Única interface com Felipe
- Lê e escreve no estado do sistema
- Executa tools diretamente (Google, Trello, email)
- Ativa módulos quando condição satisfeita ou quando Felipe solicita
- Tem memória operacional própria, versionada e persistente
- Opera via Telegram

**Estado Contínuo — mediador universal**
- `state/state.json` — fonte de verdade operacional em tempo real
- Todo componente se comunica exclusivamente pelo estado
- Nenhum componente chama outro diretamente
- Estrutura: clientes, tarefas, resultados, status de módulos, falhas

**Tools — capacidades básicas sempre disponíveis**
- Google Calendar, Gmail, Drive
- Trello
- Supabase (dados de clientes)
- Sempre disponíveis independente de módulos

### 3.2 Módulos Acopláveis — Estrutura Padrão

Todo módulo implementa a mesma interface:

```
condition(state) → bool       quando Ahri deve ativar este módulo
act(state, context) → result  o que o módulo executa
write_state(result)           onde o resultado vai
```

**Ao ser acoplado, um módulo ativa:**
- Cron com intervalo específico para a função
- LLM configurada para o tipo de tarefa
- Skills específicas do domínio
- Permissões para tools necessárias
- Seção própria no estado

**Ao ser desacoplado, um módulo desativa:**
- Cron suspensa
- LLM não chamada
- Skills não carregadas
- Estado limpo da seção do módulo

### 3.3 Memória da Ahri — Componente Crítico

A memória da Ahri é separada do estado do sistema e do Claudinho:

| Memória | Contém | Quem lê | Quem escreve |
|---|---|---|---|
| **Claudinho** | Decisões de arquitetura, como construir | Claude Code | Claude Code |
| **Memória da Ahri** | Histórico operacional, aprendizados, contexto de clientes | Ahri no início de cada sessão | Ahri ao registrar eventos relevantes |
| **Estado do sistema** | O que está acontecendo agora | Ahri + módulos | Ahri + módulos |

**O que a memória da Ahri armazena:**
- Tarefas concluídas com resultado e feedback de Felipe
- Decisões operacionais tomadas (com justificativa)
- Preferências de clientes identificadas com o tempo
- Padrões de uso de Felipe (horários, tipos de pedido frequentes)
- Erros cometidos e como foram resolvidos
- Performance dos módulos ao longo do tempo

**O que a memória da Ahri não armazena:**
- Estado em tempo real do sistema (isso é o state.json)
- Decisões de arquitetura (isso é o Claudinho)
- Dados brutos sem processamento
- Logs operacionais completos

**Princípio da memória:** Ahri não lembra de tudo — lembra do que importa. Cada entrada tem justificativa. Memória sem contexto é ruído.

---

## 4. Exemplo Completo: Ciclo de Vida de um Módulo

### Acoplando o módulo Copywriter

**O que Felipe faz:**
> "Ari, quero adicionar um copywriter à equipe."

**Camada interna:**
1. Ahri registra no estado: `modules.copywriter.status = "activating"`
2. Cron do copywriter é registrada (ex: verifica estado a cada 10 min)
3. LLM de refinamento configurada para o módulo
4. Skills de escrita carregadas: `base_writing`, `copy_prime`, `humanizer`
5. Estado atualizado: `modules.copywriter.status = "active"`

**Camada externa (Ahri responde):**
> "Contratei o Raphael — nosso copywriter. Ele vai ficar de olho no estado e entrar em ação quando houver texto pra produzir. Por enquanto está em stand-by."

---

### Módulo funcionando

**Tarefa chega ao estado:**
```
tasks.task_001.status = "pending_copy"
tasks.task_001.client = "Bella Estética"
tasks.task_001.brief = "caption para post de skincare"
```

**Camada interna:**
1. Cron do copywriter verifica estado
2. `condition(state)` → encontra `pending_copy` → retorna `True`
3. Módulo executa, chama LLM com skills e contexto do cliente
4. Escreve resultado: `tasks.task_001.copy = "..." ; status = "copy_done"`

**Camada externa (Ahri reporta para Felipe):**
> "Raphael terminou a copy da Bella Estética. Quer revisar antes de eu enviar pro Trello?"

---

### Desacoplando o módulo Copywriter

**O que Felipe faz:**
> "Ahri, não vou mais oferecer copy. Pode dispensar o Raphael."

**Camada interna:**
1. Cron suspensa
2. LLM não será mais chamada para este módulo
3. Skills descarregadas
4. Estado: `modules.copywriter.status = "inactive"`
5. Memória da Ahri registra: "módulo copywriter desativado em [data], motivo: serviço encerrado"

**Camada externa (Ahri responde):**
> "Feito. Dispensei o Raphael. Se precisar reativar, é só me falar."

---

## 5. Plano de Construção — Fase 1 Apenas

**Foco total desta fase:** Ahri funcional com memória versionável no github. Essa memória será viva e orgânica como um aprendizado contínuo, fazendo a Ahri sempre lembrar do que foi feito, experiências passadas e evitar erros e atividades repetidas. Nenhum módulo especialista. Ahri deverá ter a capacidade de manter sua memória versionada, sempre atualizada e sempre pareada com o estado do sistema. Mas de forma eficiente, com filtros para evitar lixo e sobrecarga e autonomia total. 

### Etapa 1 — Fundação do estado

**O que construir:**
- `state/__init__.py` com `read_state()` e `write_state()` e file lock
- `state/state.json` com estrutura base

**Estrutura base do state.json:**
```json
{
  "meta": { "last_updated": "", "version": "" },
  "clients": {},
  "tasks": {},
  "modules": {},
  "ahri": {
    "last_interaction": "",
    "current_context": ""
  },
  "integrations": {
    "google": { "status": "unknown" },
    "trello": { "status": "unknown" },
    "supabase": { "status": "unknown" },
    "telegram": { "status": "unknown" }
  }
}
```

**Critério de conclusão:** `write_state()` e `read_state()` funcionam sem corrupção em chamadas simultâneas.

---

### Etapa 2 — Ahri conversacional mínima

**O que construir:**
- `agents/ahri.py` — Ahri lê o estado e responde
- Integração com Telegram (receber e enviar mensagens)
- Ahri usando tools existentes (Gmail, Calendar, Trello, Drive)

**Comportamento mínimo esperado:**
- Felipe envia mensagem → Ahri lê estado → responde com base no estado real
- Felipe pede lista de emails → Ahri chama tool Gmail → responde
- Felipe pergunta o que há no Trello → Ahri chama tool Trello → responde
- Ahri nunca inventa — se não tem dado no estado, diz que não tem

**Critério de conclusão:** Felipe abre o Telegram, pergunta algo, Ahri responde com base em dado real.

---

### Etapa 3 — Memória persistente da Ahri

**O que construir:**
- `ahri_memory/` — diretório versionado via Git
- `ahri_memory/index.json` — índice de entradas por categoria
- `ahri_memory/interactions/` — registros de interações relevantes
- `ahri_memory/clients/` — o que Ahri aprendeu sobre cada cliente
- `ahri_memory/patterns/` — padrões de uso identificados

**Estrutura de uma entrada de memória:**
```json
{
  "id": "mem_001",
  "type": "interaction | client_learning | pattern | error",
  "date": "2026-04-19T10:00:00",
  "summary": "Felipe pediu relatório de emails às 8h — padrão matinal",
  "context": "horário de maior atividade de Felipe: 8h-10h",
  "relevance": "alta",
  "expires": null
}
```

**Quando Ahri registra:**
- Feedback explícito de Felipe (aprovação ou rejeição com motivo)
- Padrão identificado após 3+ ocorrências
- Erro resolvido (para não repetir)
- Aprendizado sobre cliente com impacto futuro

**Quando Ahri NÃO registra:**
- Conversa casual sem intenção operacional
- Dado já registrado em entrada existente
- Informação sem impacto futuro

**Critério de conclusão:** Ahri inicia sessão nova no Telegram e tem contexto de interações anteriores sem que Felipe precise repetir informações.

---

### Etapa 4 — Interface de módulos (sem módulo real)

**O que construir:**
- `agents/base.py` — contrato padrão de módulo
- Mecanismo de acoplamento/desacoplamento via estado
- Ahri reconhecendo quando um módulo está ativo/inativo

**Contrato do módulo:**
```python
class BaseModule:
    name: str           # nome do módulo
    display_name: str   # nome do agente na camada externa
    llm_tier: str       # "production" ou "refinement"
    cron_interval: int  # em segundos
    skills: list        # lista de skills

    def condition(self, state: dict) -> bool:
        # quando este módulo deve agir
        pass

    def act(self, state: dict, context: dict) -> dict:
        # o que o módulo faz — retorna resultado
        pass
```

**Critério de conclusão:** Ahri consegue dizer "não tenho nenhum agente especialista contratado ainda" com base no estado — sem módulo real implementado.

---

## 6. O que NÃO construir nesta fase

| Não construir | Motivo |
|---|---|
| Módulo copywriter | Vem na fase 2, depois de Ahri funcional |
| Módulo radar de pautas | Vem na fase 2 |
| Interface gráfica pixel-art | Capricho para depois de produção real |
| Pipeline de conteúdo visual | Ferramentas dedicadas fazem melhor |
| Sistema de agentes autônomos em paralelo | Vem depois, quando módulo acoplável estiver validado |

---

## 7. Critério de Sucesso da Fase 1

> Felipe acorda, abre o Telegram, escreve "Ari, bom dia — o que aconteceu essa madrugada?" e Ahri responde com base no estado real do sistema, com contexto de interações anteriores, sem inventar.

Se isso funcionar, a fase 1 está concluída.

---

## 8. O que o Claudinho precisa saber em toda sessão

1. **Construir Ahri primeiro.** Nenhum módulo especialista antes de Ahri funcional.
2. **Estado é o mediador.** Nenhum componente chama outro diretamente.
3. **Módulos têm interface padrão.** `condition()` + `act()` + `write_state()`.
4. **Percepção não afeta execução.** Nomes e personalidades são metadados de log.
5. **Três memórias distintas.** Claudinho = engenharia. Ahri memory = operacional. State = tempo real.
6. **Fase 1 = Ahri + memória.** Módulos especialistas são fase 2 em diante.

---

## 9. Referências de Decisões no Claudinho

| Decisão | O que define |
|---|---|
| d_arch_010 | Sistema baseado em estado, sem pipeline |
| d_arch_011 | Módulos como funções com condition/act/write |
| d_arch_012 | Ahri como HQ conversacional, não dispatcher |
| d_arch_013 | Princípios P1-P10 obrigatórios |
| d_arch_014 | Visão do produto — Ahri como base, módulos como extensões |
| d_arch_015 | Percepção vs. execução — duas camadas separadas |
| d_arch_016 | Três memórias distintas |

---

*Documento gerado em 2026-04-19 para recontextualização do projeto OpenClaw.*
*Deve ser lido pelo Claudinho no início de cada sessão de desenvolvimento desta fase.*
