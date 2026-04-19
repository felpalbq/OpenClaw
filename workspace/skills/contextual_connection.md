---
# contextual_connection — Skill de Conexão Contextual Criativa

- **version**: 1.0.0
- **condition**: deep_strategy
- **conflicts_with**: []
- **prerequisite**: COGNITIVE_FRAMEWORK.md (este documento é a operacionalização do framework)

## Objetivo

Transformar ressonância identificada pelo framework cognitivo em estrutura
de ângulo concreto. Esta skill não substitui o COGNITIVE_FRAMEWORK — ela
o operacionaliza após o raciocínio criativo já ter ocorrido.

## Processo

1. Receber semantic_context com connection_logic e emotional_resonance
2. Verificar depth_level — se "literal", usar content_strategy sem esta skill
3. Aplicar as 4 camadas do COGNITIVE_FRAMEWORK internamente
4. Identificar a ressonância mais autêntica (passar pelo teste de autenticidade)
5. Traduzir para formato de ângulo estruturado com justificativa de ressonância
6. Verificar cruzamento com ClientProfile — a ressonância serve o cliente?
7. Gerar estrutura base (pré-copy) com: título placeholder, pontos de ressonância,
   formato ideal, gancho derivado da conexão

## Regras

- NUNCA desenvolver conexão que não passou pelo teste de autenticidade
- NUNCA usar trend como cenário decorativo — a ressonância deve ser real
- Justificativa do ângulo DEVE incluir: qual ressonância foi identificada e por quê
  é genuína para o público DESTE cliente
- Se não encontrar ressonância autêntica após 3 tentativas nas camadas →
  reportar para Ahri: "Não encontrei conexão genuína entre [A] e [B] para
  este cliente. Sugestão: usar abordagem direta via content_strategy."
- Máximo 2 ângulos por execução quando usando conexão contextual
  (qualidade > quantidade neste modo)

## Exemplos

### Bom

Input: veterinária + BBB (confinamento de humanos)
semantic_context.connection_logic: "comportamental — confinamento e adaptação"
semantic_context.emotional_resonance: "tensão de conviver em espaço restrito"

Output:
```json
{
  "angle": "Seu pet também está no confinamento",
  "resonance": "tutores assistindo BBB reconhecem no pet os mesmos
    comportamentos de quem está confinado — ansiedade por atenção,
    adaptação à rotina restrita, dependência emocional de quem está próximo",
  "authenticity_test": "passed — tutor vive isso diariamente sem nomear",
  "format": "carrossel",
  "structure": {
    "title_placeholder": "Seu pet está no BBB há mais tempo que você",
    "resonance_points": [
      "Espaço restrito → comportamento ansioso",
      "Rotina monitorada → dependência de atenção",
      "Convivência intensa → vínculo ou conflito"
    ],
    "hook_type": "contraste",
    "cta_placeholder": "Comenta CONFINADO se seu pet também tá passando por isso"
  }
}
```

### Ruim

```json
{
  "angle": "No espírito do BBB, seu pet também tem personalidade forte",
  "resonance": "BBB tem pessoas com personalidades diferentes, pets também",
  "authenticity_test": "failed — conexão superficial, precisa de explicação",
  "format": "carrossel"
}
```

Problema: analogia intelectual sem verdade emocional. O público não
se reconhece nessa conexão sem explicação.