/**
 * Dados fictícios para as telas de preview comercial (Vendas, Financeiro, Insights).
 * Consistentes entre si (mesma loja fictícia de iPhones premium) para bater nos números
 * ao navegar entre telas durante uma demonstração. Nunca usados nas telas reais
 * (Dashboard, Ordens, Estoque, Compras, Clientes).
 */

export const DEMO_APARELHOS = [
  { modelo: "iPhone 16 Pro", imei: "35" + "912345678901", preco: 8990, garantiaDias: 90 },
  { modelo: "iPhone 15 Pro", imei: "35" + "812345678902", preco: 6990, garantiaDias: 90 },
  { modelo: "iPhone 15", imei: "35" + "712345678903", preco: 5490, garantiaDias: 90 },
  { modelo: "iPhone 14", imei: "35" + "612345678904", preco: 4290, garantiaDias: 90 },
  { modelo: "AirPods Pro 2", imei: "35" + "512345678905", preco: 1890, garantiaDias: 30 },
];

export const DEMO_FORMAS_PAGAMENTO = ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"];

export const DEMO_CLIENTES_SUGERIDOS = [
  "Marcos Andrade",
  "Fernanda Lima",
  "Ricardo Souza",
  "Juliana Prado",
];

export const DEMO_DASHBOARD_COMERCIAL = {
  vendasHoje: 18420,
  lucroHoje: 5310,
  ticketMedio: 1984,
  vendasNoMes: 312840,
};

export const DEMO_FINANCEIRO = {
  fluxoCaixa: 47250,
  contasReceber: 18900,
  contasPagar: 9420,
  margemMedia: 0.24,
  ultimos30dias: [
    { dia: "Sem 1", faturamento: 68200, margem: 15200 },
    { dia: "Sem 2", faturamento: 74500, margem: 17800 },
    { dia: "Sem 3", faturamento: 81900, margem: 19100 },
    { dia: "Sem 4", faturamento: 88240, margem: 21400 },
  ],
};

export const DEMO_INSIGHTS = [
  {
    titulo: "Estoque parado",
    texto: "3 unidades de iPhone 15 Pro estão há mais de 45 dias em estoque.",
    cor: "amber",
  },
  {
    titulo: "Margem por modelo",
    texto: "Sua margem média em iPhone 15 Pro é de 18% — abaixo da meta de 25% da categoria.",
    cor: "blue",
  },
  {
    titulo: "Faturamento por categoria",
    texto: "AirPods representam 22% do faturamento desta semana.",
    cor: "green",
  },
  {
    titulo: "Recomendação de precificação",
    texto: "Recomendação: aumentar o preço do iPhone 16 Pro em R$ 150 com base na demanda recente.",
    cor: "primary",
  },
];
