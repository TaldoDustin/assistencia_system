# PRODUCT_GLOSSARY — Glossário de Termos da Fluxoly

**Status:** Vigente
**Autor:** Claude (Principal Engineer), a pedido do usuário (CTO)
**Data:** 2026-07-23

---

## Por que existe

Decisão de governança (`docs/README.md`): nenhum documento novo sem responder "que decisão ele ajuda
a tomar?". Este resolve uma confusão real e recorrente — nesta mesma semana de trabalho, "produto",
"estoque", "unidade", "IMEI" e "aparelho" foram usados de forma ambígua em conversas e specs mais de
uma vez, e a linha entre "Estoque" (peças de reparo) e "Produtos" (catálogo comercial) já causou
retrabalho real (ver `docs/company/DECISION_LOG.md`, 2026-07-20). Um glossário único evita que a mesma
ambiguidade se repita quando o Épico Vendas trouxer termos novos (Venda, Reserva, Comissão).

Cada definição abaixo é extraída do código e da documentação real do sistema — não é aspiracional.
Onde o conceito existe só como especificação (ainda não implementado), está marcado explicitamente.

---

## Glossário

| Termo | Definição | Status |
|---|---|---|
| **Fluxoly** | Nome da marca/produto (nome legado no código e infraestrutura: Assistência System). Plataforma de gestão para lojas especializadas em dispositivos móveis premium. | — |
| **OS (Ordem de Serviço)** | Registro do ciclo completo de um reparo/atendimento: abertura, técnico responsável, peças consumidas, status, finalização. Tabela `os`. Não confundir com **Venda** — OS é sobre *consertar* um aparelho, Venda é sobre *vender* um. | ✅ Implementado |
| **Estoque** | Peças e insumos usados em reparo (tela, bateria, conector, etc.) — controle agregado por quantidade. Tabela `estoque`. **Não é** o catálogo de aparelhos à venda — ver **Produto**. | ✅ Implementado |
| **Produto** | Item do catálogo comercial à venda (iPhone, Apple Watch, AirPods, Acessório) — categoria, marca, modelo, cor, capacidade, condição, preço. Tabela `produtos`, domínio **separado** de Estoque desde a Sprint Comercial 0.1 (decisão documentada em `docs/company/DECISION_LOG.md`, 2026-07-20). | ✅ Implementado |
| **Unidade Serializada** | Instância física individual de um Produto ou item de Estoque, identificada por IMEI/serial único — ex.: "este iPhone 15 Pro específico, IMEI 3529...". Tabela `unidades_serializadas`. Tem origem em Estoque OU Produto, nunca os dois ao mesmo tempo (**Regra de Ouro**, `ADR-007`). | ✅ Implementado |
| **IMEI / Serial** | Identificador único de uma Unidade Serializada. Mesmo campo (`unidades_serializadas.imei`) serve para os dois — não existe coluna separada para "serial" de acessórios sem IMEI. Tratado como **imutável** após o cadastro (decisão do usuário/CTO, Sprint Comercial 1.3.4). | ✅ Implementado |
| **Origem** (de uma Unidade Serializada) | De onde a unidade veio: `estoque` (peça de reparo com rastreio) ou `produto` (aparelho do catálogo comercial). Determina quais campos do item de origem aparecem no detalhe/busca (ex.: `marca` só existe para origem `produto`). | ✅ Implementado |
| **Lote** | Agrupamento de itens de Estoque comprados juntos (mesma nota, mesmo fornecedor, mesma data) — usado para custo médio e FIFO de consumo. Tabela `estoque_lotes`. | ✅ Implementado |
| **Reparo** | Tipo de serviço realizado numa OS (ex.: "Troca de Tela", "Troca de Bateria"). Lista fechada em `REPAROS_PADRAO`. | ✅ Implementado |
| **Cliente** | Pessoa física/jurídica com nome + telefone ou e-mail. Tabela `clientes`. Hoje ligado a OS só via campo de texto solto (`os.cliente`); `os.cliente_id` existe mas nenhum fluxo o preenche ainda — infraestrutura pronta para Vendas, não em uso pelo fluxo atual de OS. | ✅ Implementado (fundação) |
| **Fornecedor** | Quem vendeu um item de Estoque ou uma Unidade Serializada para a loja — campo de texto livre hoje, sem cadastro próprio. | Parcial (texto livre) |
| **Perfil** | Papel de um usuário no sistema: `admin`, `tecnico`, `vendedor`. Controla o que cada tela/rota permite. | ✅ Implementado |
| **Aparelho** | Termo genérico usado em conversa para "o dispositivo físico" — **evitar em spec/código**, é ambíguo entre Unidade Serializada (uma unidade específica com IMEI), Produto (o modelo comercial) e Estoque (uma peça). Preferir o termo específico. | Termo a evitar |
| **Garantia (de reparo)** | Prazo de cobertura pós-reparo de uma OS — hoje **90 dias fixos** para todo tipo de reparo (`GARANTIA_DIAS` hardcoded, dívida técnica registrada). | ✅ Implementado (hardcoded) |
| **Venda** | Transação comercial de venda de um Produto/Unidade Serializada a um Cliente. Especificada em `docs/product/features/VENDAS.md` — **ainda não implementada** (Épico Vendas). | 📋 Especificado, não implementado |
| **Reserva** | Estado temporário de uma Unidade Serializada durante um atendimento de venda em andamento, com expiração automática — evita vender o mesmo aparelho duas vezes sem travar o estoque indefinidamente. Estados `reservado`/`vendido` já existem no schema de `unidades_serializadas`, mas nenhum fluxo os produz ainda. | 📋 Especificado, não implementado |
| **Garantia (de venda)** | Cobertura pós-venda de um aparelho vendido — prazo **próprio**, não reaproveita os 90 dias hardcoded de reparo (decisão já tomada em `VENDAS.md`, valor exato ainda `TODO` do Product Owner). Termo distinto de "Garantia (de reparo)" acima — mesma palavra, dois conceitos, cuidado ao usar. | 📋 Especificado, não implementado |
| **Comissão** | Percentual sobre a margem (venda − custo) pago ao vendedor — decisão já tomada de que a base é margem, não valor bruto; percentual exato ainda `TODO` do Product Owner. | 📋 Especificado, não implementado |

---

## Termos que ainda não têm definição formal

Citados em conversa, sem spec própria ainda — não assumir significado até existir decisão registrada:

- **Financeiro / Caixa** — `VENDAS.md` já decide que o V1 do Épico Vendas registra pagamento simples,
  sem caixa formal (abertura/fechamento, sangria, suprimento); caixa formal é um épico futuro à parte.
- **Multiempresa / Empresa** — estratégia ainda não decidida (`ADR-005`, `PROPOSTA`).

---

## Documentos relacionados

- `docs/engineering/DOMAIN_MODEL.md` — descrição técnica completa de cada domínio (tabelas, lógica, testes)
- `docs/product/features/VENDAS.md` — spec do Épico Vendas, fonte de Venda/Reserva/Comissão/Garantia de venda
- `docs/product/features/IMEI.md` — spec original de Unidade Serializada (ainda com o nome antigo `estoque_unidades` no título, conteúdo desatualizado pelo `ADR-007`)
- `docs/product/features/CLIENTES.md` — spec de Cliente
- `docs/engineering/adr/ADR-007.md` — Regra de Ouro e Princípio da Responsabilidade de Transição
- `docs/company/DECISION_LOG.md` — decisão de separar Produto de Estoque (2026-07-20)
