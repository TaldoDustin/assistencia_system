# Documentação — Assistência System

Bem-vindo à documentação de engenharia do Assistência System.
Se você não sabe por onde começar, siga a ordem abaixo.

---

## Começando

Leia nesta ordem:

1. [`../CLAUDE.md`](../CLAUDE.md) — Manual operacional para IA. Define o protocolo de trabalho, regras e filosofia do projeto.
2. [`ENGINEERING_GUIDE.md`](ENGINEERING_GUIDE.md) — Constituição técnica. Padrões, convenções e arquitetura. Leia uma vez e consulte sempre.
3. [`PROJECT_STATUS.md`](PROJECT_STATUS.md) — Estado atual do projeto. Sprint em andamento, score, bugs abertos.

---

## Engenharia

Documentação técnica do sistema:

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Visão arquitetural completa: camadas, módulos, fluxos de dados.
- [`DATABASE.md`](DATABASE.md) — Schema do banco, tabelas, índices, regras de migração.
- [`SECURITY.md`](SECURITY.md) — Política de segurança e checklist OWASP adaptado ao projeto.
- [`TESTING.md`](TESTING.md) — Estratégia oficial de testes: pirâmide, ferramentas, quando usar cada tipo.
- [`CODE_STYLE.md`](CODE_STYLE.md) — Guia de estilo: Python, React, Git. Elimina discussões subjetivas.
- [`QUALITY_GATES.md`](QUALITY_GATES.md) — Contrato de qualidade: critérios objetivos para aprovação de PR.

---

## Decisões Arquiteturais (ADRs)

Decisões técnicas importantes, com contexto e alternativas avaliadas:

- [`adr/ADR-001.md`](adr/ADR-001.md) — Frontend continuará React + Vite
- [`adr/ADR-002.md`](adr/ADR-002.md) — Separar API em módulos por domínio
- [`adr/ADR-003.md`](adr/ADR-003.md) — SQLite até a versão 2

→ Índice completo: [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md)  
→ Template para novas decisões: [`templates/ADR_TEMPLATE.md`](templates/ADR_TEMPLATE.md)

---

## Trabalho com IA

- [`AI_WORKFLOW.md`](AI_WORKFLOW.md) — Protocolo de trabalho para qualquer IA. Sessão, análise, implementação, documentação.

---

## Processo de Desenvolvimento

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Como contribuir: setup, branches, commits, PRs, revisão.
- [`ROADMAP.md`](ROADMAP.md) — Evolução planejada: fases, sprints, objetivos estratégicos.
- [`CHANGELOG.md`](CHANGELOG.md) — Histórico de versões e mudanças (formato Keep a Changelog).

---

## Gestão e Rastreabilidade

- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) — Bugs e issues conhecidos. Nunca apagar — apenas mover para Resolvidos.
- [`PROJECT_STATUS.md`](PROJECT_STATUS.md) — Score, cobertura, riscos, arquivos críticos. Atualizado a cada sprint.

---

## Histórico de Sprints

Retrospectivas e planos de cada sprint:

- [`SPRINTS/SPRINT_00.md`](SPRINTS/SPRINT_00.md) — MVP em Produção (concluída)
- [`SPRINTS/SPRINT_01.md`](SPRINTS/SPRINT_01.md) — Correções Críticas e Shopping List (concluída)
- [`SPRINTS/SPRINT_02.md`](SPRINTS/SPRINT_02.md) — Infraestrutura de Qualidade (em planejamento)

→ Template para novas sprints: [`templates/SPRINT_TEMPLATE.md`](templates/SPRINT_TEMPLATE.md)

---

## Templates

Modelos para documentos recorrentes:

- [`templates/SPRINT_TEMPLATE.md`](templates/SPRINT_TEMPLATE.md) — Template de sprint
- [`templates/ADR_TEMPLATE.md`](templates/ADR_TEMPLATE.md) — Template de decisão arquitetural
- [`templates/ISSUE_TEMPLATE.md`](templates/ISSUE_TEMPLATE.md) — Template de issue/bug
