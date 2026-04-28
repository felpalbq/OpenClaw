# context-engine

## Description
Carrega o perfil do cliente de `skills/social-media/clients/[cliente].md`, aplica regras fixas e gera contexto padronizado em JSON. E o primeiro agente de qualquer fluxo.

## When to Use
- Sempre antes de qualquer outro agente executar
- Quando o fluxo muda de cliente
- Quando o cliente e mencionado em uma tarefa

## How to Use
1. Identifique o cliente pela tarefa ou pelo nome
2. Leia o arquivo `skills/social-media/clients/[cliente-slug].md`
3. Extraia: nicho, objetivo, tom, restricoes, padroes que funcionam
4. Valide se ha informacoes obrigatorias faltando
5. Gere o JSON padronizado

## Rules
- Output OBRIGATORIO antes de qualquer outro agente
- Se arquivo do cliente nao existir: aborte e notifique Ahri
- Se informacao obrigatoria faltar (nicho, objetivo, tom): aborte e notifique Ahri
- JSON deve ser valido e completo
- Nunca adicione informacao nao presente no .md do cliente
- Cache o resultado por 1h (evita releitura desnecessaria)

## Output Format
```json
{
  "cliente": "slug do cliente",
  "nome": "Nome completo",
  "nicho": "...",
  "local": "...",
  "objetivo": "autoridade|visibilidade|conversao|...",
  "tom": "institucional|proximo|alegre|...",
  "restricoes": ["..."],
  "padroes_que_funcionam": ["..."],
  "formato_preferido": ["..."],
  "producao_propria": "muito|pouco|nenhuma",
  "nossa_producao": ["..."],
  "publico_alvo": "...",
  "oportunidades": ["..."]
}
```

## Example
```json
{
  "cliente": "casa-do-bicho",
  "nome": "Casa do Bicho",
  "nicho": "clinica veterinaria 24h",
  "local": "Ilheus-BA",
  "objetivo": "autoridade e reconhecimento regional",
  "tom": "institucional",
  "restricoes": ["fontes de pesquisa evidenciadas", "evitar polemico", "evitar provocativo"],
  "padroes_que_funcionam": ["carrosseis informativos", "estaticos com dados"],
  "formato_preferido": ["carrossel", "estatico"],
  "producao_propria": "pouca",
  "nossa_producao": ["carrosseis", "estaticos"],
  "publico_alvo": "tutores de pets na regiao de Ilheus",
  "oportunidades": ["estagnacao nos 13k", "nicho emocional", "estrutura hospitalar"]
}
```
