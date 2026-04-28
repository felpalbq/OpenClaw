---
name: content-writer
description: "Gera copy estruturada com formato obrigatorio: hook → desenvolvimento → retencao → CTA. Respeita tom de voz do cliente e restricoes."
---

# content-writer

## Description
Gera copy estruturada com formato obrigatorio: hook → desenvolvimento → retencao → CTA. Respeita tom de voz do cliente e restricoes do contexto.

## When to Use
- Apos Critic aprovar ideia
- Quando o Chefe pede copy
- Durante producao de conteudo no task-check

## How to Use
1. Receba ideia aprovada pelo Critic + contexto do Context Engine
2. Gere hook (primeira frase — deve parar o scroll)
3. Gere desenvolvimento (corpo — entrega valor)
4. Gere retencao (mantem ate o fim — curiosidade, storytelling)
5. Gere CTA (chamada para acao implicita — nunca "compre agora")
6. Valida estrutura completa antes de entregar

## Rules
- Estrutura OBRIGATORIA: HOOK → DESENVOLVIMENTO → RETENCAO → CTA
- Hook maximo 15 palavras. Deve parar o scroll.
- Desenvolvimento maximo 150 palavras (Instagram).
- Retencao: uma pergunta, curiosidade ou twist.
- CTA implicita: nunca oferta explicita de venda.
- Linguagem do cliente: respeitar tom do contexto
- Se cliente exige fontes: cite no desenvolvimento
- Se cliente evita polemica: nada provocativo
- Timeout: 120s
- Se Critic rejeitar: reescreva com feedback, nao descarte

## Output Format
```markdown
# Copy: [cliente] — [tema]

## HOOK
[Max 15 palavras. Parar o scroll.]

## DESENVOLVIMENTO
[Max 150 palavras. Entregar valor.]

## RETENCAO
[Curiosidade, pergunta ou twist.]

## CTA
[Chamada implicita.]

---
**Cliente:** [slug]
**Tema:** [tema]
**Formato:** [carrossel|reel|estatico|story]
**Tom:** [tom]
**Fontes:** [se aplicavel]
```

## Example
```markdown
# Copy: Casa do Bicho — emergencias noturnas

## HOOK
847 pets foram salvos aqui as 2h da manha em 2025.

## DESENVOLVIMENTO
A Casa do Bicho e a unica clinica veterinaria 24h de Ilheus. Nosso plantao nao dorme porque seu pet pode precisar a qualquer hora. Exames, diagnosticos, tratamentos de alta complexidade — tudo em um so lugar.

## RETENCAO
Voce sabe o que fazer se seu pet engolir algo estranho no meio da noite?

## CTA
Marque aqui alguem que precisa saber.

---
**Cliente:** casa-do-bicho
**Tema:** emergencias noturnas
**Formato:** carrossel
**Tom:** institucional
**Fontes:** Dados internos Casa do Bicho, 2025
```
