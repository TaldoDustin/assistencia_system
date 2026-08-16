# DISCOVERY — Release 1.0, gaps restantes ("Parte C restante")

**Data:** 2026-08-16
**Tipo de documento:** Discovery somente-leitura (`ADR-010`, etapa 1) — registra o estado real e separa
bloqueadores de débitos técnicos, sem decidir nem implementar nada. Decisão de sequência é do CTO.
**Fonte primária:** `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` (revisão 2026-08-16) e
`docs/operations/KNOWN_ISSUES.md` (12 KIs abertos na data desta Discovery).
**Gatilho:** após a Homologação Interna Controlada ser aprovada (2026-08-15) e a decisão do CTO
(2026-08-16) de manter o Ambiente Demo interno por enquanto, era necessário decidir o que vem depois —
esta Discovery existe para evitar escolher a próxima sprint só pelo maior % faltante.

---

## Estado consolidado em 2026-08-16

- **Release 1.0:** ~65% (checklist recalculado em 2026-08-16, ver histórico no próprio
  `RELEASE_1.0_MASTER_CHECKLIST.md`).
- **Ambiente Demo:** ✅ tecnicamente concluído (14/14 critérios do DoD do `ADR-012`) e **homologado
  internamente** (Homologação Interna Controlada aprovada em 2026-08-15, ver
  `docs/engineering/plans/ROTEIRO-homologacao-interna-controlada.md`).
- **Homologação Externa** (homologador humano de fora da equipe): Discovery e Plano concluídos
  (`docs/engineering/plans/PLAN-homologacao-externa-demo.md`), **Preparação pausada** — decisão do CTO
  (2026-08-16) de manter o Demo como ambiente interno por enquanto, sem prospect definido.
- **KI-041** (seed do Demo sem Tipo de Garantia): ✅ resolvido e revalidado no Demo real (2026-08-15).
- **KIs abertos:** 12, nenhum crítico (KI-002, KI-005, KI-006, KI-007, KI-019, KI-029, KI-030, KI-031,
  KI-033, KI-034, KI-040, KI-042).
- **Produção:** intocada e saudável durante toda a sequência.
- **PR #22:** aberta, não mergeada — preserva evidência do INC-003 (decisão pendente de disposição).
- **PR #24:** Dry-Run 2B concluído, PR descartável preservada, não mergeada.

---

## Classificação dos gaps restantes

### Bloqueadores reais para o primeiro cliente pagante

| Item | Estado real | Por que bloqueia |
|---|---|---|
| **LGPD** | ~0% — nenhum documento existe no projeto (`docs/`, `GO_LIVE_PLAN.md`, `PRODUCT_BACKLOG.md` sem nenhuma menção) | O sistema vai guardar dado pessoal real de cliente de um terceiro pagante — obrigação legal no Brasil, não uma opção técnica |
| **KI-029** — backups `.db` + sidecars WAL com dado operacional real versionados no histórico git | Aberto, decisão pendente desde 2026-07-31 | Mesma trilha de LGPD: dado real de cliente exposto no histórico é exatamente o tipo de achado que uma auditoria de compliance sinaliza primeiro |
| **Manual do usuário** | ~5% | Sem ele, nenhum piloto opera o sistema sozinho — pré-requisito prático de qualquer piloto, não risco técnico |
| **Cliente piloto homologou** | 0% | Por definição, resultado dos três itens acima — não é trabalho paralelo, é o gate final |

### Riscos de segurança/compliance

Os mesmos dois itens acima (LGPD, KI-029). `Segurança revisada` já está ✅ 100% no checklist — nenhuma
pendência nesse item específico.

### Débitos técnicos (não bloqueiam o primeiro cliente, mas acumulam risco)

| KI | Resumo | Risco real hoje |
|---|---|---|
| KI-005 | Sem paginação em `GET /api/ordens` | Degrada só com volume alto — sem sintoma reportado hoje |
| KI-006 | Falha de backup automático não gera alerta visível ao operador | Perda de dado silenciosa, sem detecção |
| KI-034 | Ajuste Comercial (admin, BR-043) não resincroniza `movimentacoes_caixa` | Inconsistência real de saldo, mas exige ação deliberada e pouco frequente |
| KI-031 / KI-033 | Relatórios e Reparos sem nenhum teste automatizado | Regressão silenciosa possível, sem sintoma hoje |
| KI-040 | Condição de corrida em `criar_admin_padrao()` sob `--workers 2` | Só warning de log, sem dado inconsistente resultante |
| KI-019 | Modo processo único quebrado (assets 404) | Zero impacto — produção real (Render+Vercel separados) não usa esse modo |
| KI-030 | Teste `test_sentry_init.py` falha só localmente no Windows | Cosmético, não reproduz no CI (Linux) |
| KI-042 | Menu expõe tela além do escopo do perfil (backend bloqueia a escrita) | Inconsistência de UX, sem bypass de autorização confirmado |
| KI-002 | Token de checklist público sem expiração | Link some fica válido indefinidamente após a OS encerrar |
| KI-007 | Mensagens de commit pré-Conventional-Commits no histórico antigo | Rastreabilidade histórica, sem efeito em produção |

### Itens de operação

- **Rollback:** falta testar o lado Vercel/frontend do rollback coordenado e um conflito de infraestrutura
  real (só o mecanismo Git local foi testado com conflito real, no Dry-Run 1B).
- **Teste de carga:** só existe validação ad-hoc feita durante a investigação do INC-001 — não é suíte
  formal repetível, não integrada ao CI.

### Itens que podem ficar pós-release

- **Dashboard Executivo** (~65%) — falta "OS atrasadas" e "top vendedores".
- **Comercial completo** (~65%) — troca/avaliação de usado e timeout de reserva de IMEI dependem de
  decisões de produto ainda não tomadas pelo Product Owner.
- **Configurações** (~40%) — tela de "empresa" só faz sentido pós-Multiempresa; configuração de
  integrações via UI (hoje só variável de ambiente).

---

## Dependências

- **Cliente piloto** ← Manual do usuário **+** decisão de LGPD **+** decisão de KI-029. O Ambiente Demo já
  não é mais uma dependência (concluído).
- **Homologação Externa** (retomar a Preparação) ← decisão de negócio já tomada em 2026-08-16 (manter
  interno por enquanto) — não é dependência técnica no momento.
- Os débitos técnicos (KI-005, KI-006, KI-019, KI-030, KI-031, KI-033, KI-034, KI-040, KI-002, KI-007,
  KI-042) são **todos isolados entre si** — nenhum bloqueia outro, nenhum bloqueia LGPD/KI-029/Manual.

## Esforço relativo (qualitativo — P/M/G, não pontos de história)

| Item | Esforço |
|---|---|
| Discovery de LGPD | P (esta é a próxima etapa, ver `DISCOVERY_LGPD.md`) |
| Implementação das medidas de LGPD | Depende do escopo decidido na Discovery — pode variar de M a G |
| Decisão + correção do KI-029 | Decisão é P; sidecars WAL (destrackear + `.gitignore`) é P; os dois backups reais é M e **destrutivo** (reescrita de histórico) |
| Manual do usuário | M — é conteúdo, não código |
| KI-040 / KI-034 / KI-031 / KI-033 | P cada, isolados, já têm correção candidata descrita no próprio KI |
| Rollback Vercel + teste de carga formal | M — exige janela de infraestrutura dedicada |
| KI-005 (paginação) | M — muda contrato de API + frontend |

## Ordem recomendada (proposta — decisão de sequência é do CTO)

1. **Discovery de LGPD** — sozinha, é o maior risco desconhecido hoje (~0% de informação).
2. **Decisão do CTO sobre KI-029** — pequena e rápida, resolve um risco real de compliance com pouco
   esforço técnico; diretamente conectada à Discovery de LGPD.
3. Sprint de limpeza curta e isolada: KI-040 + KI-034 + KI-031/KI-033 (testes) — todos P, sem mistura de
   escopo entre si.
4. **Manual do usuário** — pode correr em paralelo, não bloqueia nada tecnicamente.
5. Rollback Vercel + teste de carga formal — quando houver janela de infraestrutura dedicada.
6. KI-005 — só quando o volume real justificar.
7. **Cliente piloto** — só depois de 1, 2 e 4 resolvidos, no mínimo.

**O que este documento explicitamente não decide:** não começa por KI-005/KI-040/KI-034 (débitos reais,
mas não determinam se dá para colocar o primeiro cliente pagante no sistema); não inicia o piloto antes de
LGPD + KI-029 + Manual estarem resolvidos.

---

## Próximo passo

Discovery de LGPD, somente leitura, sem código/branch/infraestrutura — ver
`docs/product/research/DISCOVERY_LGPD.md`. Ao final, para decisão do CTO conforme `ADR-010`.

## Documentos relacionados

- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — checklist de certificação (fonte primária desta Discovery)
- `docs/operations/KNOWN_ISSUES.md` — os 12 KIs abertos citados acima
- `docs/engineering/adr/ADR-012.md` — Ambiente de Demonstração
- `docs/engineering/plans/ROTEIRO-homologacao-interna-controlada.md` — Homologação Interna Controlada
- `docs/engineering/plans/PLAN-homologacao-externa-demo.md` — Homologação Externa (pausada)
- `docs/product/research/DISCOVERY_LGPD.md` — próxima Discovery (LGPD)
