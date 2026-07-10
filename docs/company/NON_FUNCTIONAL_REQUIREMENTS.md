# NON_FUNCTIONAL_REQUIREMENTS.md — Requisitos Não Funcionais

**Status:** Formulário — a preencher pelo Product Owner (com input técnico da engenharia onde marcado).
**Última revisão:** 2026-07-10

---

Até aqui a documentação da Fluxoly descreveu funcionalidades — o que o sistema faz. Este documento
responde perguntas que não aparecem em nenhuma tela, mas que decidem escolhas de arquitetura reais: se
SQLite ainda serve, que política de cache faz sentido, qual limite de upload implementar, se vale a pena
investir em suporte offline agora.

**Regra:** mesma disciplina dos outros formulários de `docs/company/` — nenhuma seção abaixo foi
preenchida com um número inventado. Onde já existe uma referência relacionada em outro documento (um
gatilho de revisão, uma meta de sprint específica), ela é citada como contexto, não como resposta — a
meta formal do produto continua `TODO` até o Product Owner decidir.

---

## Capacidade — Usuários Simultâneos

`TODO` — quantos usuários simultâneos o produto precisa suportar (por loja e agregado, se multiempresa).

*Referência existente, não é a resposta:* `docs/engineering/adr/ADR-003.md` define ">10 usuários
simultâneos em pico" como **gatilho de revisão** da decisão de manter SQLite — ou seja, é o limite onde a
arquitetura atual começa a rachar, não uma meta de capacidade desejada.

---

## Desempenho — Tempo de Resposta

`TODO` — tempo de resposta aceitável para telas e para APIs, como padrão geral do produto.

*Referência existente, não é a resposta:* `docs/operations/ROADMAP.md` (Sprint 5) define uma meta pontual
para uma única rota: `GET /api/ordens` < 200ms com 10.000+ registros. `ADR-003.md` define >500ms de
latência de listagem de OS como gatilho de revisão da arquitetura de banco. Nenhum dos dois é uma NFR
geral do produto — são específicos de uma rota/decisão.

---

## Duração da Reserva de IMEI

`TODO` — já registrado como pendente em `docs/product/features/VENDAS.md` ("Valor exato do timeout de
reserva de IMEI — TODO, decisão de Product Owner") e em `docs/product/BUSINESS_RULES.md` BR-017. Repito
aqui porque é, por definição, um requisito não funcional (tempo), mas a decisão em si mora em `VENDAS.md`
— não duplicar a resposta quando ela vier, só linkar.

---

## Disponibilidade (SLA)

`TODO` — nenhuma meta de disponibilidade (99,5%? 99,9%?) está documentada hoje em nenhum lugar do projeto.

*Contexto relevante, não é a resposta:* `docs/operations/PROJECT_STATUS.md` risco R-01 (SQLite sem
réplica em produção) e R-02 (ausência de CI/CD) afetam diretamente qual disponibilidade é realista
prometer — a meta deveria ser decidida em conjunto com esses riscos, não isoladamente.

---

## Backup e Recuperação (RTO / RPO)

`TODO` — tempo aceitável para restaurar um backup (RTO) e quanto dado se pode perder no pior caso (RPO)
não estão definidos.

*Contexto relevante:* `irflow_storage.py` já faz backup automático (local, e-mail, Google Drive — ver
`docs/engineering/DOMAIN_MODEL.md` seção 1.9), mas falhas de envio são apenas logadas sem alerta visível
(KI-006, `docs/operations/KNOWN_ISSUES.md`), e não há um processo de restore testado/documentado. Definir
RTO/RPO é pré-requisito para saber se o backup atual já é suficiente ou não.

---

## Indisponibilidade Máxima Aceitável

`TODO` — quanto tempo de sistema fora do ar é tolerável antes de virar incidente crítico, e o que
acontece nesse caso (aviso a clientes, SLA de crédito, etc.).

---

## Tamanho Máximo de Upload

`TODO` — nenhum limite de tamanho de arquivo (fotos de produto, anexos de OS) está documentado ou, pelo
que a leitura do código indica, imposto explicitamente hoje.

---

## Comportamento Offline

**Observação factual (não é meta, é o estado atual):** o frontend é uma SPA React que depende
inteiramente da API (`docs/engineering/ARCHITECTURE.md` seção 5) — não há service worker, PWA, nem
qualquer estratégia de cache/fila offline hoje. Sem conexão, o sistema simplesmente não funciona.

`TODO` — se algum nível de suporte offline é uma meta do produto (ex.: continuar operando checkout sem
internet e sincronizar depois) ou se a decisão é aceitar dependência total de conexão.

---

## Navegadores e Dispositivos Suportados

`TODO` — nenhuma política de navegadores suportados (versões mínimas, mobile vs desktop) está
documentada. Relevante para decisões de dependências frontend (`docs/engineering/ENGINEERING_GUIDE.md`
seção 2) e para o checklist de QA de qualquer sprint futura.

---

## Documentos relacionados

- `docs/engineering/adr/ADR-003.md` — gatilhos de revisão da decisão de banco, referenciados acima
- `docs/operations/ROADMAP.md` — meta de latência pontual da Sprint 5
- `docs/product/features/VENDAS.md` — timeout de reserva de IMEI, pendente na origem
- `docs/operations/KNOWN_ISSUES.md` — KI-006 (falha de backup sem alerta), relevante ao RTO/RPO
- `docs/company/DECISION_LOG.md` — quando cada NFR aqui for decidida, registrar lá com motivo e impacto
