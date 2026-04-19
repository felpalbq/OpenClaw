# CONTENT ENGINE CONTRACT

## ORDEM OBRIGATÓRIA

1. O sistema DEVE selecionar um STYLE antes de gerar conteúdo

2. O STYLE selecionado define:
   - LAYOUT
   - CONTENT_STRUCTURE
   - CONTENT_RENDERING

3. O conteúdo DEVE ser gerado já respeitando:
   - estrutura narrativa
   - limites visuais
   - densidade

---

## PROIBIDO

- gerar conteúdo primeiro e adaptar depois
- ignorar constraints do layout
- ajustar conteúdo apenas na renderização

---

## REGRA CENTRAL

Conteúdo e layout são gerados de forma integrada.

---

## RESULTADO ESPERADO

- consistência visual
- previsibilidade de output
- adaptação natural ao layout