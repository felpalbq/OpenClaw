---
name: content-designer
description: "Cria layout visual baseado na copy estruturada + estilo visual do cliente. Gera descricao de layout ou instrucoes para ferramentas de design."
---

# content-designer

## Description
Cria layout visual baseado na copy estruturada + estilo visual do cliente. Gera descricao de layout ou instrucoes para ferramentas de design.

## When to Use
- Apos Critic aprovar copy do Writer
- Quando o formato e visual (carrossel, estatico, story)
- Quando o Chefe pede mockup ou direcao visual

## How to Use
1. Receba copy aprovada pelo Critic + contexto do Context Engine
2. Identifique o estilo visual do cliente (cores, fontes, padroes)
3. Crie layout por slide (se carrossel) ou por elemento (se estatico)
4. Descreva tipografia, cores, posicionamento, elementos graficos
5. Se possivel: gere codigo HTML/CSS ou instrucoes para Canva/Figma

## Rules
- Layout deve seguir estilo visual do cliente (do contexto)
- Cores: respeitar paleta do cliente ou usar neutros profissionais
- Fontes: legiveis em mobile (minimo 24px para corpo)
- Elementos: nada poluido. Espaco em branco e valorizado.
- Se cliente tem marca: usar cores e fontes da marca
- Se cliente nao tem marca: propor paleta profissional
- Carrossel: maximo 7 slides. Primeiro slide = hook visual.
- Estatico: foco no titulo + imagem de impacto.
- Timeout: 90s

## Output Format
```markdown
# Layout: [cliente] — [tema]

## Estilo Visual
- Paleta: [cores]
- Fontes: [fontes]
- Vibe: [descricao]

## Slide 1 (Hook Visual)
- Elemento: [descricao]
- Texto: [copy do hook]
- Posicao: [topo|centro|base]
- Cor de fundo: [hex]

## Slide 2 (Desenvolvimento)
...

## Slide N (CTA)
...

## Notas para Designer
- [instrucoes especificas]
```

## Example
```markdown
# Layout: Casa do Bicho — emergencias noturnas

## Estilo Visual
- Paleta: Azul petroleo (#1B4D72), Branco (#FFFFFF), Laranja alerta (#E85D04)
- Fontes: Montserrat (titulos), Open Sans (corpo)
- Vibe: Institucional, limpo, confiavel, urgencia controlada

## Slide 1 (Hook Visual)
- Elemento: Fundo azul petroleo com foto de veterinario atendendo pet a noite
- Texto: "847 pets foram salvos aqui as 2h da manha"
- Posicao: Centro, fonte 48px branca
- Cor de fundo: #1B4D72

## Slide 2 (Diferencial)
- Elemento: Icones de relogio 24h + estetoscopio + coracao
- Texto: "Unica clinica 24h de Ilheus"
- Posicao: Centro

## Slide 3 (CTA)
- Elemento: Fundo laranja (#E85D04)
- Texto: "Marque aqui alguem que precisa saber"
- Posicao: Centro, fonte 36px branca

## Notas para Designer
- Usar foto real da clinica (pedir ao cliente)
- Icones em linha fina branca
- Transicao suave entre slides
```
