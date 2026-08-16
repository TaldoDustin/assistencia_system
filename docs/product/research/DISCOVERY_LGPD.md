# DISCOVERY — LGPD

**Data:** 2026-08-16
**Tipo de documento:** Discovery somente-leitura (`ADR-010`, etapa 1). Registra fatos verificados no
código/docs e separa decisões pendentes do CTO — **não decide, não implementa, não altera código, branch
ou infraestrutura**. Nenhum arquivo de código foi tocado nesta etapa.
**Método:** pesquisa read-only conduzida por agente dedicado sobre o repositório real (schema, código,
config, docs) em 2026-08-16 — não é análise jurídica, é levantamento técnico de fatos.
**Aviso importante:** este documento mapeia **o que o sistema faz hoje com dado pessoal**. Ele não
determina o que a LGPD exige legalmente — essa é uma pergunta jurídica, fora do que pode ser respondido
por análise de código. Recomenda-se revisão por assessoria jurídica antes de qualquer certificação formal
de conformidade, especialmente antes do primeiro cliente pagante real.

---

## 1. Quais dados pessoais o Fluxoly armazena

| Tabela | Campos pessoais | Observação |
|---|---|---|
| `clientes` | `nome` (obrigatório, schema `NOT NULL`), `telefone`, `email`, `cpf_cnpj` (todos opcionais no schema) | Regra de negócio (não-schema, `fluxoly_clientes_service.py`) exige `nome` + ao menos um de `telefone`/`email`; `cpf_cnpj` nunca é obrigatório em lugar nenhum. Frontend não valida formato de nenhum desses campos. |
| `os` | `cliente` (TEXT livre, **não FK**, obrigatório), `imei` (opcional) | Campo duplicado/desnormalizado do cadastro estruturado — OS antigas têm só o texto, sem vínculo a `clientes.id` (`cliente_id` é nullable, sem backfill). Corrigir/apagar o dado de um cliente em `clientes` não corrige as cópias em texto livre já gravadas em `os`. |
| `vendas` | `cliente_id` (FK obrigatória para `clientes.id`) | Sem dado pessoal direto na própria tabela — nome/telefone ficam só em `clientes`. |
| `usuarios` | `nome`, `usuario` (login) | Dado pessoal de **funcionário**, não de cliente final. `senha_hash` nunca é retornado pela API. |
| `tipos_garantia` | Nenhum | É catálogo de política (nome + duração), não guarda dado de pessoa. |
| `unidades_serializadas` | `imei` (UNIQUE) | Sem FK direta para `clientes` — relação com pessoa só existe indiretamente via `vendas_itens` → `vendas.cliente_id`. |
| `audit_log` | Snapshot completo de qualquer entidade alterada, incluindo `clientes` | `valor_anterior`/`valor_novo` gravam o registro inteiro em JSON — inclui nome/telefone/email/CPF sempre que um cliente é criado/editado/excluído. |

**Achado de documentação:** `os_reparos.tipo_garantia_id`/`os_reparos.garantia_data_fim`, usados ativamente
em `api_garantias.py`, não constam em `docs/engineering/DATABASE.md` — o schema documentado está
desatualizado nesse ponto (fora do escopo desta Discovery corrigir, registrado aqui para conhecimento).

## 2. Onde os dados ficam

- **`database.db`** — disco persistente do Render (`IR_FLOW_DATA_DIR=/data`, `DEPLOY.md`), sem
  criptografia em repouso além da que o provedor de infraestrutura oferecer por padrão.
- **Backups** — cópia binária não-criptografada do banco inteiro, com até três destinos possíveis: disco
  local (`backups/`), pasta local sincronizada com Google Drive (`IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR`, se
  configurada) e anexo de e-mail via SMTP (`IR_FLOW_BACKUP_EMAIL_SENHA`, se configurada) — **nenhum dos
  três criptografa o arquivo** (ver **KI-043**, registrado nesta Discovery). Retenção de 90 arquivos
  `backup-auto-*.db` existe, mas é limpeza de arquivo, não do dado pessoal em si.
- **Histórico git (KI-029, já conhecido, reconfirmado hoje)** — `backup-20260429-015724.db` e
  `database-pre-cleanup-20260517-123834.db` **continuam rastreados em `main` hoje** (2026-08-16), contendo
  dado operacional real de um snapshot antigo. Sidecars `-shm`/`-wal` citados na atualização de 2026-07-31
  do KI-029 não aparecem mais em `git ls-files` — parecem ter sido destrackeados em algum momento, não
  investigado a fundo aqui.
- **Logs estruturados** (`fluxoly_logging.py`) — não foi encontrado nenhum log que grave nome/telefone/
  e-mail de cliente em texto puro; os únicos campos correlatos encontrados em `extra={}` são nome de
  **arquivo** de backup e e-mail de **configuração** do sistema, não de cliente.
- **Sentry** — `send_default_pii=False` explícito em `app.py`, comentado como decisão deliberada. Não
  identificado nenhum breadcrumb manual que injete PII de cliente (busca não exaustiva).

## 3. Quais dados são obrigatórios

No schema, só `clientes.nome` é `NOT NULL`. Na prática (regra de negócio, não schema), a criação de
cliente exige `nome` + ao menos um de `telefone`/`email`. `cpf_cnpj` nunca é obrigatório. `os.cliente`
(texto livre) é obrigatório para abrir uma OS, independente de o cliente existir como registro estruturado
em `clientes`.

## 4. Retenção

**Fato negativo confirmado:** não existe nenhum mecanismo de TTL/expiração/arquivamento automático de
dado de cliente, OS ou venda. O único uso real de "retenção" no código é limpeza de arquivos de backup
antigos (90 arquivos), não do dado de negócio. Isso também vale para `audit_log` — cresce indefinidamente,
sem limite.

## 5. Exclusão/anonimização

Existe `DELETE /api/clientes/<id>` (admin-only), mas:
1. É **bloqueado** (409) se o cliente tiver qualquer OS vinculada — ou seja, nenhum cliente com histórico
   real de atendimento pode ser removido hoje. Não existe caminho de anonimização alternativo.
2. Mesmo quando a exclusão ocorre (cliente órfão), o snapshot completo sobrevive em `audit_log` em texto
   puro, sem prazo.

Registrado como **KI-044** nesta Discovery — não é bug de comportamento (o bloqueio por integridade
referencial é razoável, o log de auditoria existe por design), mas significa que **hoje não existe nenhum
mecanismo real de apagamento ou anonimização de dado pessoal**.

## 6. Exportação

**Fato negativo confirmado:** não existe nenhum endpoint de exportação/portabilidade formal de dados de
um cliente específico. O mais próximo é a tela "Perfil do Cliente" (`frontend/src/pages/Clientes.jsx`),
que agrega em tela (não em arquivo baixável) cadastro + histórico de OS + garantias — visualização, não
portabilidade de dado no sentido formal.

## 7. Controle de acesso

`GET/POST/PUT /api/clientes` exigem só `usuario_logado()` — **qualquer perfil autenticado**
(`admin`/`tecnico`/`vendedor`/`estoque`) pode ler e escrever nome/telefone/e-mail/CPF de qualquer cliente,
sem segregação por perfil. `GET /api/garantias` tem o mesmo padrão. Só `DELETE` é restrito a `admin`. Isso
é mais amplo que o padrão já usado para outras entidades sensíveis do sistema (Financeiro, Usuários).
Registrado como **KI-045** nesta Discovery.

## 8. Logs e backups

Ver seção 2 acima — resumo: logs não vazam PII estruturado (fato positivo); backups vazam por ausência de
criptografia em todos os destinos possíveis, incluindo dois arquivos reais ainda hoje presentes no
histórico git (KI-029, ainda aberto).

## 9. Dados de terceiros/integradores (MercadoPhone)

Toda comunicação com a API do MercadoPhone é **inbound** (importação/leitura) — não foi encontrada nenhuma
chamada de escrita para a API externa. O webhook que recebe OS do MercadoPhone também é inbound. Os únicos
campos pessoais confirmados trafegando nesse fluxo são **nome do cliente** e **IMEI do aparelho** — não
foram encontrados telefone, e-mail, endereço ou CPF trafegando com o MercadoPhone. Isso significa que o
MercadoPhone é uma fonte de dado pessoal que entra no Fluxoly, não um destino para onde o Fluxoly envia
dado de cliente.

## 10. Responsabilidades entre Fluxoly e o cliente (a loja)

**Questão em aberto, não uma decisão técnica** — típica de LGPD/GDPR: o Fluxoly, como fornecedor de
software para a loja, provavelmente atua como **operador** do dado (processa em nome da loja), enquanto a
loja (cliente pagante do Fluxoly) é a **controladora** do dado dos clientes finais dela. Essa divisão de
papéis não está documentada em lugar nenhum do projeto hoje (nenhum contrato de processamento de dados,
nenhuma cláusula de responsabilidade identificada). Isso tem implicação prática real: o que o Fluxoly é
obrigado a implementar tecnicamente (ex.: função de exportar/apagar) pode ser diferente do que é
responsabilidade contratual da loja fazer/pedir. **Decisão pendente do CTO, provavelmente com apoio
jurídico** — não é algo que este levantamento técnico resolve sozinho.

---

## Riscos identificados, por ordem de relevância

1. **KI-029** (já conhecido, reconfirmado hoje) — dado real de cliente ainda presente no histórico git de
   `main`.
2. **KI-043** (novo) — nenhum backup é criptografado, em nenhum dos três destinos possíveis.
3. **KI-044** (novo) — não existe mecanismo real de apagamento/anonimização de dado pessoal.
4. **KI-045** (novo) — controle de acesso a PII de cliente mais amplo que o padrão do resto do sistema.
5. Ausência total de retenção, exportação e aviso/consentimento de privacidade (fatos negativos, sem KI
   dedicado — são ausência de feature, não defeito de comportamento).
6. `os.cliente` como texto livre desnormalizado do cadastro estruturado — risco de inconsistência caso
   uma correção/exclusão de dado precise se propagar (mencionado aqui, sem KI dedicado nesta Discovery).

## O que parece necessário para o primeiro cliente (proposta — não é decisão)

Com base só nos fatos acima, os itens que mais diretamente afetam se dá para colocar dado real de um
cliente pagante em produção sem risco desnecessário:

- Resolver KI-029 (mesma trilha, já teria que ser decidido de qualquer forma).
- Decidir o mínimo de aviso/base legal para tratar o dado do cliente final da loja (mesmo que simples).
- Decidir se KI-043 (backup sem criptografia) precisa de mitigação antes do primeiro cliente ou se é risco
  aceitável documentado nesta fase.
- Decidir se KI-044 (sem apagamento/anonimização real) é bloqueante — depende de quão firme é a obrigação
  legal formal de suportar "direito ao apagamento" desde o primeiro cliente.

## O que pode ficar para fase posterior (proposta — não é decisão)

- KI-045 (segregação de acesso a PII por perfil) — é uma melhoria de princípio de minimização, não um gap
  crítico identificado como exigência imediata.
- Exportação/portabilidade formal de dado — pode ser resolvida via processo manual (extração assistida)
  na fase inicial, sem precisar de feature dedicada.
- Correção do `os.cliente` desnormalizado — débito técnico à parte, não bloqueia LGPD por si só.

---

## Decisões em aberto para o CTO

1. Confirmar (ou corrigir) o entendimento de responsabilidades Fluxoly-operador / loja-controladora
   (seção 10) — idealmente com apoio jurídico.
2. Decidir prioridade e escopo de KI-029, KI-043, KI-044, KI-045 (quais entram no caminho crítico do
   primeiro cliente, quais ficam para depois).
3. Decidir se algum documento formal de privacidade/termo de uso é necessário antes do primeiro cliente,
   e quem o redige (jurídico, não este repositório).
4. Confirmar se este levantamento técnico é suficiente para embasar um Plano Técnico, ou se falta
   consulta jurídica antes de prosseguir.

## Decisões do CTO (2026-08-16)

Baseline aprovada para as 7 decisões em aberto (seção anterior). Registro da decisão, não implementação —
o "como" de cada item fica para o Plano Técnico (`docs/engineering/plans/PLAN-LGPD-Compliance.md`).

**Ressalva geral, válida para todas as decisões abaixo:** implementar os controles técnicos aqui aprovados
**não equivale a declarar conformidade jurídica com a LGPD**. Esta baseline é a posição conservadora
provisória da engenharia enquanto a validação jurídica formal (decisão 7) corre em paralelo.

| # | Decisão | Aprovado |
|---|---|---|
| 1 | Escopo mínimo LGPD | **Intermediário, com ressalva:** KI-029 + KI-043 + KI-044 + KI-045 + documentação mínima de privacidade — não ficou defensável tratar KI-044/KI-045 como risco aceito às vésperas de guardar dado real de cliente. |
| 2 | KI-029 | **Corrigir antes do piloto** — obrigatório. Plano deve separar: impedir novos `.db`/sidecars, remover arquivos indevidos do estado atual, avaliar necessidade de reescrita de histórico, preservar evidências necessárias, verificar exposição adicional. Qualquer operação destrutiva no histórico continua exigindo confirmação explícita separada (`CLAUDE.md`), mesmo dentro deste plano aprovado. |
| 3 | KI-043 | **Conter, não criptografar ainda.** Desabilitar temporariamente os destinos externos de backup (Google Drive, e-mail) até existir uma solução de criptografia com gestão de chave/rotação/recuperação projetada corretamente. Backup local permanece. |
| 4 | KI-044 | **Anonimização, não hard-delete.** Preserva a integridade histórica de OS/vendas/garantias, mascara/remove PII. `audit_log` recebe tratamento próprio (ver decisão 6). |
| 5 | KI-045 | **Restringir campos sensíveis, principalmente CPF** — admin/financeiro mantêm acesso completo; demais perfis recebem só o necessário para suas funções. Antes de restringir, mapear todo consumidor de `cpf_cnpj` (feito nesta rodada do Plano Técnico, ver seção "Impacto no Backend/Frontend" — achado: uso é restrito a `fluxoly_clientes_controller.py`/`_service.py`/`_repository.py` e `frontend/src/pages/Clientes.jsx`, nenhum comprovante/PDF/relatório/venda/OS/garantia referencia CPF). |
| 6 | Retenção do `audit_log` | **Mascaramento + expurgo, com política definida no Plano Técnico.** Prazo não decidido aqui — entra como parâmetro configurável, não hardcoded, aguardando orientação jurídica/operacional. |
| 7 | Jurídico | **Posição conservadora provisória + validação jurídica em paralelo** — evita parar a engenharia esperando parecer, e evita presumir conformidade sem validação especializada. |

**Baseline consolidada:**

- 🔴 **Antes do primeiro cliente:** KI-029, KI-043 (contenção), KI-044 (anonimização), KI-045 (controle de
  acesso), política de retenção/anonimização do `audit_log`, documentação mínima de privacidade, definição
  contratual/operacional Fluxoly × loja (com validação jurídica).
- 🟡 **Depois do primeiro cliente:** solução completa de backup criptografado (chave/rotação/recuperação),
  melhorias adicionais de privacidade, controles mais sofisticados de auditoria, funcionalidades LGPD que
  não sejam necessárias ao primeiro cliente.

**Mudança de estratégia de execução:** um único ciclo `ADR-010` (Discovery → Plano Técnico → Implementação
→ Testes → QA → Revisão Arquitetural → Encerramento) cobre KI-029 + KI-043 + KI-044 + KI-045 juntos, em vez
de quatro sprints isoladas tratando sintomas do mesmo problema — mesmo padrão já usado em
`PLAN-preview-seguro-inc003-ki035.md` (INC-003 Frente B + KI-035 + KI-036 num único plano).

## Próximo passo

Discovery encerrada com decisão do CTO. Plano Técnico consolidado em
`docs/engineering/plans/PLAN-LGPD-Compliance.md` — parado ao final do Plano Técnico para revisão do CTO,
antes de qualquer implementação, conforme `ADR-010`.

## Documentos relacionados

- `docs/product/research/DISCOVERY_RELEASE_1.0_RESTANTE.md` — Discovery que originou esta (LGPD como
  bloqueador nº 1 identificado)
- `docs/operations/KNOWN_ISSUES.md` — KI-029, KI-043, KI-044, KI-045
- `docs/engineering/DATABASE.md`, `docs/engineering/DATA_DICTIONARY.md` — schema e governança de dado
- `docs/engineering/adr/ADR-010.md` — ciclo Discovery → Plano Técnico → Implementação
