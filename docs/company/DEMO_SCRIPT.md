# DEMO_SCRIPT.md — Roteiro de Demonstração Comercial

**Status:** Primeira versão, 2026-07-17.
**Objetivo:** qualquer pessoa da equipe consegue apresentar a Fluxoly da mesma forma, sem improviso.
**Material de apoio:** `docs/company/SALES_DECK.md` (o que falar), `docs/company/FAQ_COMERCIAL.md`
(perguntas difíceis).

---

## Antes de começar

**Onde rodar:**
- Local (mais confiável, sem depender de internet do cliente): `python app.py` + `npm run dev` dentro
  de `frontend/`, acessar `http://localhost:5173`. Ver `README.md` seção "Execução Local".
- Ou a URL de preview mais recente da Vercel (branch `demo/commercial-preview`) — pegar sempre a do
  deployment mais recente no dashboard da Vercel, a URL muda a cada push.

**Login:** usuário `admin`, senha padrão do ambiente de demonstração (não usar credencial de produção
real na frente do cliente).

**Antes de entrar na chamada:** já deixar o navegador aberto e logado na tela de Dashboard — não gastar
os primeiros minutos digitando login na frente do cliente.

---

## Roteiro (12–15 minutos)

### 00:00 — Abertura (1 min)

Não falar de tecnologia. Falar da dor.

> "Hoje uma loja de iPhones normalmente usa WhatsApp, Instagram, Mercado Phone e Excel ao mesmo tempo.
> Informação espalhada, retrabalho, e o dono é quem menos tempo tem pra olhar os números. A Fluxoly
> existe pra unificar isso."

### 02:00 — Dashboard (2 min)

Tela: `/` (Dashboard).

Mostrar os KPIs reais (faturamento, lucro, OS finalizadas/abertas). Se o ambiente de demo tiver dado
real carregado, aproveitar os números de verdade — não são inventados.

Passar rápido por "Faturamento por Vendedor" (dado real por pessoa) e o bloco "Explore mais" no fim da
página — é o gancho pra falar da visão mais ampla (Vendas/Financeiro/Insights) mais adiante.

> "Isso aqui é o painel que já está em produção hoje, com dado real."

### 04:00 — Clientes (2 min)

Tela: `/clientes`.

Cadastrar um cliente **ao vivo**, na frente da pessoa. É o momento que mais gera confiança — mostra que
não é um vídeo gravado, é o sistema real respondendo.

> "Cadastro simples, busca por nome/telefone/e-mail, e qualquer venda ou OS futura já puxa o histórico
> desse cliente."

### 06:00 — Assistência (2 min)

Telas: `/ordens` e `/kanban`.

Esse é o módulo mais maduro — mostrar uma OS existente, o Kanban por status, e (se fizer sentido pro
cliente) a integração automática com Mercado Phone.

> "Esse é o módulo que já está rodando no dia a dia de assistências técnicas reais."

### 08:00 — Vendas (2 min)

Tela: `/vendas`.

Badge "Preview" visível — não esconder que é uma prévia. Mostrar o fluxo de balcão (aparelho, IMEI,
cliente, pagamento, garantia).

> "Esse é o próximo módulo que estamos finalizando. Os primeiros clientes-parceiro têm prioridade na
> definição de como ele funciona — literalmente participam da construção."

Se o cliente perguntar "isso já funciona?": responder com a verdade — é uma prévia visual do fluxo,
módulo real em construção. Ver `FAQ_COMERCIAL.md`.

### 10:00 — Fluxoly Insights (1–2 min)

Tela: `/insights`.

É a tela que mais vende a visão de longo prazo — mostra que a Fluxoly não é só operação, é decisão.

> "Essa tela já mostra a direção: recomendações automáticas baseadas no que está acontecendo na loja."

### 12:00 — Perguntas (3–5 min)

Abrir para perguntas. Ter `FAQ_COMERCIAL.md` por perto — não improvisar resposta a objeção de preço,
migração ou "já uso Mercado Phone".

---

## Variações do roteiro

- **Cliente já usa Mercado Phone (a maioria):** dar mais tempo à seção 5 do `SALES_DECK.md`
  (diferenciação direta) antes de entrar na demonstração.
- **Reunião de 5 minutos (call rápida):** Dashboard (30s) → Clientes ao vivo (1 min) → Assistência
  (1 min) → uma frase de fechamento sobre Vendas/Financeiro estarem vindo. Cortar Insights.
- **Apresentação institucional (sem demo ao vivo, só slides):** usar só o `SALES_DECK.md` com
  screenshots em vez de navegação ao vivo.
