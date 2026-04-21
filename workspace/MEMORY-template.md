# MEMORY.md — Template

> Este arquivo é um ÍNDICE da memória do HQ.
> **Natureza:** MEMÓRIA DO HQ — experiência dinâmica, editável pelo Chefe e atualizada por pipeline.
> **NÃO é contrato do sistema.** Contratos vivem em workspace/ e são escritos pelo arquiteto.
> **Pareamento:** Tudo aqui tem correspondente em ahri/ (formato JSON, programático). Nem tudo em ahri/ vira entrada aqui.
> **Fonte de verdade:** ahri/ é a fonte primária de aprendizado. Este arquivo é PROJEÇÃO operacional curada — não fonte alternativa. ahri/ gera, memory/ reflete.
> **Influência reversa:** memory/ molda comportamento da Ahri (via contexto carregado), o que gera novas interações que voltam a ahri/ via pipeline. Não inverte o pareamento.

## 📂 Topic Files

| Arquivo | O que contém | Pareamento ahri/ |
|---------|-------------|------------------|
| `memory/decisions.md` | Decisões operacionais permanentes | ahri/decisions/ |
| `memory/lessons.md` | Lições aprendidas, erros, padrões | ahri/patterns/ + ahri/learnings/ |
| `memory/people.md` | Equipe, parceiros, contatos | ahri/context/ |
| `memory/projects.md` | Projetos ativos e concluídos | ahri/context/projects.json |
| `memory/pending.md` | Aguardando input | — |

## 🔄 Ciclo de Memória

```
Conversa (Telegram) → ahri/sessions/YYYY-MM-DD.jsonl (bruto, JSONL)
                        ↓ pipeline de extração
                   ahri/patterns/ + ahri/learnings/ + ahri/decisions/ (JSON, programático)
                        ↓ reflexo (pareamento)
                   memory/lessons.md + memory/decisions.md + memory/people.md (Markdown, legível)
                        ↓ índice atualizado
                   MEMORY.md (sumário)
```

## ⚠️ Distinção Importante

| O que é | Onde | Quem escreve | Muda em runtime? |
|---------|------|-------------|-----------------|
| Contrato do sistema | workspace/ | Arquiteto | Não |
| Memória do HQ | memory/ | Pipeline + Chefe | Sim | Projeção curada (não é fonte de verdade) |
| Memória externa | ahri/ | Pipeline | Sim | **Fonte primária** de aprendizado |
| Estado volátil | state/ | Sistema | Sim |

## 📸 Estado Atual

[PREENCHA COM O ESTADO ATUAL DOS SEUS PROJETOS E PRIORIDADES]

### Projetos Ativos
- **[PROJETO 1]** — [status]
- **[PROJETO 2]** — [status]

### Pendências
- [PENDÊNCIA 1]
- [PENDÊNCIA 2]

---

*Última atualização: [DATA]*