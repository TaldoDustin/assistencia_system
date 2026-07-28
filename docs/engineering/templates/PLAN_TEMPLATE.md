# PLAN-<slug> — <Nome da Feature>

**Data:** AAAA-MM-DD
**Feature:** referência à discovery correspondente (ex.: `docs/product/features/VENDAS.md` — "V1.3", `docs/product/BUSINESS_RULES.md` BR-NNN a BR-NNN)
**Status:** Rascunho | Aprovado pelo CTO | Implementado

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

---

## Objetivo

O que este plano técnico resolve, em 1-3 frases. Não repita a regra de negócio já fechada na discovery —
referencie-a.

---

## Escopo

O que este plano cobre.

---

## Fora de Escopo

O que este plano explicitamente não cobre (e por quê, se não for óbvio).

---

## Impacto no Banco

- Tabelas/colunas novas ou alteradas.
- Migração: aditiva (`ALTER TABLE ADD COLUMN`) ou requer recriação (ver `DATABASE.md` seção 1)?
- Índices novos, se houver.

---

## Impacto no Backend

- Endpoints novos ou alterados.
- Camadas afetadas (controller/service/repository — `ENGINEERING_GUIDE.md` §3.1).
- Dependências de outros domínios (service a service, nunca repository a repository).

---

## Impacto no Frontend

- Páginas/componentes novos ou alterados.
- Chamadas de API novas em `client.js`.

---

## Estratégia de Migração

Se houver mudança de schema: passo a passo de como aplicar (ordem, backup, janela de manutenção se
necessário — ver `ENGINEERING_GUIDE.md` seção 5).

---

## Testes

Quais módulos de teste serão criados/alterados, e o que cada um precisa cobrir (caso feliz + casos de
erro relevantes).

---

## Critérios de Aceite

Lista verificável — o que precisa ser verdade para considerar a implementação completa.

---

## Riscos

Riscos identificados e mitigação de cada um.

---

## Rollback

Como reverter esta mudança se algo der errado após o deploy.

---

## Questões em Aberto

Perguntas de **negócio** (não técnicas) que surgiram durante este plano e que este documento **não**
responde — por definição, um Plano Técnico nunca decide regra de negócio (`ADR-010`, "Princípio da
Separação de Decisões"). Cada item aqui pausa a etapa de Plano Técnico e volta o trabalho para Discovery
antes de prosseguir.

- *Exemplo: "e se o vendedor não tiver limite configurado?" — decisão de produto, não de implementação.*
