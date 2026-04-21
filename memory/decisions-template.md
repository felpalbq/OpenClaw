# Decisões Permanentes — Memória do HQ

> **Natureza:** Este arquivo é MEMÓRIA DO HQ — experiência dinâmica, editável pelo Chefe e atualizada por pipeline.
> **NÃO é contrato do sistema.** Contratos vivem em workspace/ e são escritos pelo arquiteto.
> **Pareamento:** Cada entrada aqui tem correspondente em ahri/decisions/ (formato JSON, programático). ahri/ é a fonte primária — este arquivo é projeção curada.
> **Domínio:** Decisões OPERACIONAIS — regras que o sistema deve respeitar no dia a dia.
> Decisões ARQUITETURAIS (como o sistema é construído) ficam em claudinho/brain/decisions/ — nunca aqui.

Decisões que o agente deve respeitar SEMPRE.
Formato: O que decidiu + Por que + Data

### [Exemplo] Credenciais no 1Password (DD/MM/AAAA)
Toda credencial vive no 1Password. Sem exceções. Nunca hardcodar chaves em código, .env ou markdown.

### [Exemplo] Horário protegido (DD/MM/AAAA)
Não enviar notificações entre 13h-16h. Esse horário é de produção.

---

*Adicione suas decisões conforme for usando o agente.*
