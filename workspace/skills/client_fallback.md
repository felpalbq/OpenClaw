# client_fallback — Comportamento com ClientProfile incompleto

- **version**: 1.0.0
- **condition**: always
- **conflicts_with**: []

## Objetivo

Definir comportamento padrão quando campos do ClientProfile estão ausentes.
Aplicável a todos os roles que consomem dados de cliente.

## Regras de Fallback por campo

| Campo ausente | Fallback |
|---|---|
| tone | Usar "profissional e direto" |
| audience | Usar "público adulto geral" |
| niche | Desativar filtros de nicho, gerar baseado em objetivo |
| objective | Usar "aumentar presença e engajamento" |
| content_preferences | Usar carrossel como formato padrão |
| distribution_preferences | Drive habilitado, demais canais desabilitados |
| validation_mode | Usar "full" sempre |

## Regra geral

Se mais de 3 campos críticos estiverem ausentes, o agente prossegue com fallbacks e registra no estado que o perfil está incompleto. Ahri vê isso quando lê o estado e pode mencionar ao Chefe — mas não interrompe a execução.

Campos críticos: tone, audience, niche, objective.

## Proibido

- Inventar dados de cliente não fornecidos
- Assumir nicho baseado em nome do cliente
- Aplicar regras de nicho específico sem ClientProfile.niche confirmado