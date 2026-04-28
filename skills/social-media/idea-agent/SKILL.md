# idea-agent

## Description
Cria angulos e hipoteses de conteudo a partir de insights estruturados. NAO cria "pautas" prontas — cria possibilidades para serem validadas pelo Critic.

## When to Use
- Apos Intelligence Agent entregar insights
- Quando o Chefe pede sugestoes de conteudo
- Durante content-radar

## How to Use
1. Receba insights do Intelligence Agent + contexto do Context Engine
2. Brainstorm angulos unicos para cada insight
3. Crie hipoteses testaveis (formato: "Se fizermos X, resultado sera Y")
4. Atribua scoring preliminar

## Rules
- Cada ideia deve ter angulo UNICO — nada generico
- Formato de hipotese: "Se [acao], entao [resultado esperado]"
- Minimo 3 ideias por insight, maximo 5
- Ideias devem respeitar restricoes do cliente (do contexto)
- Se nao conseguir angulo unico: retorne "insight_fraco" e pule
- Timeout: 60s
- Nunca gere copy, roteiro ou pauta final

## Output Format
```json
{
  "cliente": "slug",
  "data": "ISO8601",
  "ideias": [
    {
      "id": "idea_001",
      "insight_ref": "id do insight",
      "angulo": "...",
      "hipotese": "Se fizermos X, entao Y",
      "formato_sugerido": "carrossel|reel|estatico|story",
      "score_preliminar": 0.0,
      "justificativa": "..."
    }
  ],
  "total_ideias": 0,
  "melhor_score": 0.0
}
```

## Example
```json
{
  "cliente": "casa-do-bicho",
  "data": "2026-04-28T10:05:00Z",
  "ideias": [
    {
      "id": "idea_001",
      "insight_ref": "trend_001",
      "angulo": "O que acontece quando seu pet engole um objeto estranho as 2h da manha?",
      "hipotese": "Se criarmos um carrossel educativo sobre emergencias noturnas, entao aumentaremos o reconhecimento do atendimento 24h",
      "formato_sugerido": "carrossel",
      "score_preliminar": 8.5,
      "justificativa": "Combina trend de emergencias com diferencial real do cliente"
    }
  ],
  "total_ideias": 4,
  "melhor_score": 8.5
}
```
