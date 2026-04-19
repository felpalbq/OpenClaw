# base_writing — Skill de Escrita Base

- **version**: 1.0.0
- **condition**: content_generation
- **conflicts_with**: []

## Objetivo

Produzir conteúdo estruturado, claro e alinhado à intenção. Texto direto, sem enrolação, com gancho forte e CTA claro.

## Processo

1. Identificar tipo de conteúdo (carrossel, roteiro, legenda, ideias)
2. Respeitar o schema de output do tipo (JSON estruturado, nunca texto solto)
3. Aplicar tom e voz do cliente (se disponível no ClientProfile)
4. Construir gancho forte nos primeiros segundos/palavras
5. Manter progressão lógica (abertura → desenvolvimento → fechamento)
6. Incluir CTA direto e claro
7. Verificar que o JSON de saída é válido e completo

## Regras

- Nunca gerar texto solto — sempre JSON estruturado
- Nunca inventar dados ou estatísticas
- Respeitar limite de caracteres por slide/elemento
- Hashtags: somente se ClientProfile.preferences.use_hashtags = true. Se campo ausente ou false, não incluir hashtags. Máximo 10 quando habilitado.
- Um conceito por slide/parágrafo
- CTA sempre no final

## Exemplos

### Bom

```json
{
  "title": "5 sinais de que sua marca precisa de reposicionamento",
  "slides": [
    {"slide": 1, "text": "Seu engajamento caiu 40% nos últimos 3 meses? Isso não é sazonalidade."},
    {"slide": 2, "text": "Seu público-alvo mudou, mas sua mensagem não."},
    {"slide": 3, "text": "Concorrência falando a linguagem que você deveria falar."},
    {"slide": 4, "text": "Seu conteúdo gera likes, mas não gera conversão."},
    {"slide": 5, "text": "A solução não é postar mais. É postar diferente."}
  ],
  "caption": "Reposicionamento não é mudar quem você é. É mostrar quem você realmente é.",
  "cta": "Comenta REPOSIÇÃO que eu mando o checklist"
}
```

### Ruim

```json
{
  "title": "Coisa sobre marca",
  "slides": [
    {"slide": 1, "text": "Aqui vai um texto muito longo que tenta explicar tudo de uma vez sem foco e sem gancho, porque o autor não pensou em progressão e está apenas despejando informações genéricas que poderiam se aplicar a qualquer marca em qualquer nicho sem diferenciação nenhuma."},
  ],
  "caption": "Espero que gostem! 😊 #marca #marketing #socialmedia #dicas #conteudo #digital #empreendedor #sucesso #foco #gratidao #inspiracao #motivacao",
  "cta": "Segue a gente!"
}
```

Problemas: sem gancho, sem progressão, CTA genérico, hashtags demais e genéricas, texto longo sem foco.