# PRD: Arquitetura de Memória (Atualizado Março 2026)

> Jogue este arquivo no agente: "Implementa esta arquitetura de memória"

## Contexto

Agentes AI esquecem tudo a cada sessão. Sem memória estruturada, você repete contexto todo dia. Esta arquitetura resolve isso com uma estrutura em subpastas que permite busca semântica precisa.

**Novidade Março 2026:** `memory_search` agora funciona nativamente — sem precisar de chave de API externa (OpenAI/Gemini). A busca por embedding é built-in.

## O que o agente carrega vs. busca

| Sempre carregado na sessão | Buscado sob demanda |
|---------------------------|---------------------|
| SOUL.md, USER.md, AGENTS.md | memory/context/decisions.md |
| MEMORY.md (índice) | memory/context/lessons.md |
| memory/sessions/ (hoje + ontem) | memory/projects/*.md |
| | skills/ (qualquer skill) |

## Tarefas

### 1. Criar estrutura de subpastas

```bash
mkdir -p memory/context memory/projects memory/sessions memory/integrations
```

### 2. Criar os arquivos de contexto

| Arquivo | Propósito |
|---------|-----------|
| `memory/context/decisions.md` | Decisões permanentes e irreversíveis |
| `memory/context/lessons.md` | Lições aprendidas, erros, padrões |
| `memory/context/people.md` | Equipe, parceiros, contatos — como interagir com cada um |
| `memory/context/business-context.md` | Contexto do negócio, produtos, clientes |

**Retenção de lições:**
- 🔒 Estratégicas = permanentes (filosofia, padrões de arquitetura)
- ⏳ Táticas = expiram em 30 dias (bugs, workarounds temporários)

### 3. Criar projetos individuais

Em vez de um `projects.md` gigante, um arquivo por projeto:

```
memory/projects/
├── meu-saas.md          ← MRR atual, próximas features, pendências
├── lançamento-maio.md   ← status, checklist, responsáveis
└── produto-b.md
```

**Por que separado?** A busca semântica acha o projeto certo sem trazer contexto de outros projetos junto.

### 4. Criar MEMORY.md (índice)

Na raiz do workspace. É o mapa — não duplica conteúdo, apenas referencia:

```markdown
# MEMORY.md

## Contexto
- Decisões: memory/context/decisions.md
- Lições: memory/context/lessons.md
- Pessoas: memory/context/people.md

## Projetos ativos
- [Nome do Projeto]: memory/projects/nome.md

## Integrações
- Mapa de ferramentas: memory/integrations/
```

### 5. Configurar ciclo de memória no AGENTS.md

```
Regras de memória:
1. Notas diárias: criar memory/sessions/YYYY-MM-DD.md a cada sessão relevante
2. Projetos: um arquivo separado por projeto em memory/projects/
3. INVIOLÁVEL: antes de compactar → extrair lições, decisões e pendências
4. Feedback: ao rejeitar sugestão → salvar motivo em memory/feedback/
```

### 6. Configurar busca semântica

O agente usa dois tools:
- `memory_search("termo")` — busca semântica em todos os arquivos (~400 tokens/chunk)
- `memory_get("arquivo.md", linha_início)` — lê só o trecho relevante

**Funciona nativamente** desde Março 2026. Não precisa de chave externa.

### 7. Configurar feedback loops (avançado)

```
memory/feedback/
├── content.json    ← sugestões de conteúdo aprovadas/rejeitadas
├── tasks.json      ← preferências de execução de tarefas
└── tone.json       ← ajustes de tom e estilo
```

Formato:
```json
{
  "entries": [
    {
      "date": "2026-03-14",
      "context": "Sugeri post LinkedIn com linguagem formal",
      "decision": "reject",
      "reason": "Tom muito corporativo — prefere direto e conversacional",
      "tags": ["linkedin", "tom"]
    }
  ]
}
```

## Exemplo de como funciona o "pedir" para ahri salvar

| Camada Externa (Visível) | Camada interna (sistema real) | Camada interna memory_ahri
|----------------|------------|
| "Lembra disso" | Salva em memory/context/decisions_context.md | Commit e Push em ahri (repo) após filtro
| "Guarda essa info" | Adiciona em memory/projects/.md | Commit e Push em ahri (repo) após filtro
| "Não esquece que..." | Registra em memory/sessions/hoje como lição | Commit e Push em ahri (repo) após filtro

## Resultado Esperado

1. Estrutura criada com subpastas organizadas
2. MEMORY.md como índice apontando para tudo
3. Teste: fechar sessão → abrir nova → perguntar algo salvo → agente encontra via memory_search
