# trend_detection — Skill de Detecção de Tendências

- **version**: 1.0.0
- **condition**: trend_analysis
- **conflicts_with**: []

## Objetivo

Detectar tendências relevantes e gerar opportunities com score. Analisar input do usuário para extrair oportunidades. NUNCA gerar conteúdo final.

## Processo

1. Identificar sinais de tendência no input ou contexto
2. Cruzar com perfis de clientes ativos
3. Calcular score: relevance * 0.4 + timeliness * 0.3 + engagement_potential * 0.3
4. Se score < 0.7 → descartar
5. Se 0.7 <= score < 0.85 → armazenar para consulta
6. Se score >= 0.85 → escrever no estado como "notified" — Ahri lê quando perguntar
7. Verificar dedup: opportunity similar para mesmo cliente com <7 dias → não gerar
8. Registrar em experience_memory como opportunity_detected

## Regras

- Score < 0.7 é DESCARTADO, nunca armazenado
- Score >= 0.85 é escrito no estado como "notified" — não é push notification
- Máximo 5 opportunities por ciclo
- Modelo de PRODUÇÃO apenas (nunca refinamento)
- NUNCA gerar conteúdo final — apenas opportunities
- Modo augmented: analisar input, não buscar tendências externas
- Modo on_demand: buscar tendências relevantes
- Modo cron: operar com limites de tempo/custo

Estado atual do sistema:
- Modo augmented: DISPONÍVEL — analisa input do usuário, não depende de fontes externas
- Modo on_demand: LIMITADO — usa conhecimento do LLM, sem integração com APIs de tendência
- Modo cron/opportunity_driven: NÃO IMPLEMENTADO ainda

Para uso atual: priorizar modo augmented quando usuário fornece material.
Para on_demand sem material externo: basear score em relevância de nicho e conhecimento do LLM, informar que dado é estimado, não verificado.

## Exemplos

### Bom (opportunity com score alto)

```json
{
  "title": "Tendência: rotina fitness adaptativa para iniciantes",
  "description": "Busca por "rotina fitness iniciante" cresceu 340% esta semana. Ângulo: adaptação para quem está voltando.",
  "score": 0.88,
  "relevance": 0.9,
  "timeliness": 0.85,
  "engagement_potential": 0.87,
  "client_relevance": {"client_id": "abc123", "niche": "fitness", "reason": "niche exato + histórico de aprovação em tendências fitness"},
  "suggested_angles": ["Adaptação para iniciantes", "Confronto com mito comum", "Progressão realista vs idealizada"]
}
```

### Ruim (opportunity com score baixo)

```json
{
  "title": "Coisa sobre marketing",
  "description": "Marketing digital é tendência.",
  "score": 0.3,
  "client_relevance": null,
  "suggested_angles": ["Marketing digital", "Redes sociais"]
}
```

Problemas: vago, sem dados, sem cliente específico, score abaixo do mínimo.