# humanizer — Skill de Humanização

- **version**: 1.0.0
- **condition**: content_generation
- **conflicts_with**: []

## Objetivo

Tornar conteúdo natural e humano. Remover linguagem robótica, genérica ou excessivamente formal. Texto que parece escrito por uma pessoa, não por um template.

## Processo

1. Identificar trechos genéricos que poderiam ser de qualquer marca
2. Substituir frases de template por expressões naturais
3. Adicionar imperfeição controlada (perguntas retóricas, pausas, quebras de padrão)
4. Verificar tom de voz contra ClientProfile
5. Remover emojis excessivos ou genéricos (🔥💪✨)
6. Garantir que cada frase soa como alguém falando, não como um manual

## Regras

- Nunca usar "Neste post vamos falar sobre..." — ir direto ao ponto
- Nunca usar "Não esqueça de..." — usar imperativo direto
- Eliminar "É muito importante" — mostrar, não dizer
- Evitar listas genéricas ("5 dicas para...") sem contexto específico
- Um emoji por slide máximo, apenas se relevante
- Perguntas retóricas devem ter resposta no próprio conteúdo
- Se ClientProfile.tone contém 'formal', 'institucional' ou 'profissional':
  - Manter estrutura mais cuidadosa
  - Reduzir perguntas retóricas
  - Evitar coloquialismos e gírias
  - Humanizar sem informalizar — clareza e proximidade sem casualidade

## Exemplos

### Bom

"Cansou de postar todo dia e ver engajamento cair? O problema não é o algoritmo. É a repetição."

Natural, direto, com pergunta que identificação e resposta imediata.

### Ruim

"Neste post iremos abordar 5 dicas importantes para melhorar seu engajamento no Instagram. É muito importante seguir estas dicas. Não esqueça de salvar este post para referência futura! 🔥💪"

Genérico, robótico, emojis excessivos, frases de template.