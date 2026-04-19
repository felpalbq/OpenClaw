# content_strategy — Skill de Estratégia de Conteúdo

- **version**: 1.0.0
- **condition**: strategy_needed
- **conflicts_with**: []

## Objetivo

Gerar ângulos estratégicos cruzados com perfil de cliente. Definir formato e criar estrutura base (pré-copy). NUNCA escrever conteúdo final.

## Processo

1. Consultar experience memory (angle_rejection, content_rejection, strategy_adjustment)
   - Se experience memory está VAZIA para este cliente:
     → Gerar ângulos baseados exclusivamente em ClientProfile (niche, tone, audience, objective)
     → Não aplicar Decision Filter (não há histórico para filtrar)
     → Registrar na justificativa: 'Cliente novo — sem histórico de experience. Ângulos baseados em perfil.'
   - Se experience memory tem entradas:
     → Usar como informação para priorizar ângulos, não como gate para bloquear
2. Priorizar ângulos com base em experience memory (aprovados primeiro, rejeitados com cuidado)
3. Gerar 2-3 ângulos estratégicos distintos
4. Cruzar cada ângulo com ClientProfile:
   - nicho, tom, público, objetivo (campos existentes)
   - voice_samples: se disponível, verificar se o ângulo é consistente com
     a voz real do cliente. Ângulo que contradiz voice_samples é descartado.
   - Se semantic_context.depth_level for "contextual" ou "deep":
     usar COGNITIVE_FRAMEWORK + skill contextual_connection em vez de
     gerar ângulos diretos. Content_strategy opera em modo de suporte.
     (Nota: esta condição vem do estado, não de chamada direta entre skills)
5. Definir formato ideal (carrossel, vídeo, legenda) baseado em ângulo e cliente
6. Criar estrutura base (pré-copy): títulos, pontos-chave, CTA placeholder
7. Justificar escolha de ângulo com dados de experience memory

## Regras

- NUNCA escrever conteúdo final — apenas estrutura
- Sempre consultar experience memory antes de gerar ângulos
- Sempre consultar Decision Filter para priorizar
- Ângulos rejeitados para este cliente são EVITADOS, não removidos — se não houver alternativa, podem ser regerados com ajuste
- Se 2+ rejeições recentes para tipo de ângulo → evitar tipo similar, mas não bloquear (P8: validação informa, não trava)
- Cada ângulo deve ter justificativa clara (por que funciona para ESTE cliente)
- Formato é escolhido com base no ângulo + client_preferences, não genérico

## Exemplos

### Bom

```json
{
  "angles": [
    {
      "angle": "Progressão realista vs idealizada",
      "format": "carrossel",
      "justification": "Cliente já aprovou ângulo de "realidade vs expectativa" em 15/04. Nicho fitness responde a progressão. Tom "direto e acessível" combina com este ângulo.",
      "structure": {
        "title_placeholder": "Progressão real: o que ninguém mostra",
        "key_points": ["Expectativa vs realidade semana 1", "Resultado visível mês 2", "O ponto de virada", "CTA: progressão real"],
        "cta_placeholder": "Comenta REAL que eu mando a progressão completa"
      },
      "score": 0.82,
      "experience_filter": "Ângulo similar aprovado em 15/04 para este cliente. Nenhuma rejeição recente."
    }
  ],
  "recommended_format": "carrossel",
  "format_reason": "ClientProfile.content_preferences mapeia carrossel para fitness. Experience: 3 aprovações de carrossel para este cliente."
}
```

### Ruim

```json
{
  "angles": [
    {
      "angle": "5 dicas de marketing",
      "format": "carrossel",
      "justification": "",
      "structure": null,
      "score": 0.5
    }
  ]
}
```

Problemas: sem justificativa, sem cruzamento com cliente, sem experience filter, sem estrutura base, ângulo genérico.