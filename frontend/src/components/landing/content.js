// Fonte única da copy da Landing Page institucional — texto extraído literalmente de
// docs/product/features/LANDING_PAGE.md (Parte 3). Itens ainda não decididos pelo negócio
// permanecem como placeholder `[DEFINIR]`, nunca preenchidos com dado inventado.
// Mantém os componentes de components/landing/*.jsx puramente apresentacionais.

export const NAV_LINKS = [
  { label: "Produto", href: "#funcionalidades" },
  { label: "Como funciona", href: "#como-funciona" },
  { label: "Planos", href: "#planos" },
  { label: "FAQ", href: "#faq" },
  { label: "Contato", href: "#cta-final" },
];

export const NAV_CTA = "Começar agora";

export const HERO = {
  title: "O fluxo inteligente da sua loja de celulares.",
  subtitle:
    "Vendas, estoque, ordens de serviço e financeiro em um único sistema — sem planilha, sem caderno, sem retrabalho.",
  primaryCta: "Começar agora",
  secondaryCta: "Ver como funciona",
};

export const PROBLEM = {
  title: "Sua loja roda no improviso?",
  cards: [
    "Planilha que ninguém atualiza a tempo",
    "Estoque que só é conferido quando falta peça",
    "Ordem de serviço anotada em papel, perdida entre um cliente e outro",
    "Caixa fechado sem saber de onde veio o resultado do mês",
  ],
  closing:
    "O Fluxoly existe para substituir isso por um fluxo único — não para adicionar mais uma ferramenta à pilha.",
};

export const SOLUTION = {
  title: "Um único fluxo para toda a operação.",
  text: "O Fluxoly reúne vendas, estoque, financeiro e assistência técnica em um só lugar — sem planilha paralela, sem sistema que não conversa com o outro.",
};

export const BENEFITS = {
  title: "O que muda na prática.",
  items: [
    {
      lead: "Menos tempo perdido com tarefas manuais",
      text: "o que hoje é digitado duas vezes passa a ser digitado uma.",
    },
    {
      lead: "Decisão com dado real",
      text: "não com a planilha que alguém esqueceu de atualizar.",
    },
    {
      lead: "Atendimento mais rápido",
      text: "histórico do cliente e da OS num só lugar, sem procurar em outro sistema.",
    },
    {
      lead: "Controle real do estoque",
      text: "sem contar peça na mão pra saber o que tem na loja.",
    },
  ],
};

export const FEATURES = {
  title: "Um sistema, todas as frentes da loja.",
  subtitle: "Vendas, Estoque, Financeiro, Assistência Técnica e Inteligência — os 6 pilares do Fluxoly.",
  pillars: [
    { icon: "ShoppingCart", name: "Vendas", text: "Fechamento rápido, do primeiro contato ao recibo." },
    { icon: "Package", name: "Operação", text: "Estoque sob controle, sem contagem manual de última hora." },
    { icon: "CurrencyDollar", name: "Financeiro", text: "Caixa e resultado real, sempre visíveis." },
    {
      icon: "UserCircle",
      name: "Relacionamento",
      text: "Histórico completo de cada cliente, sem precisar perguntar de novo.",
    },
    { icon: "Wrench", name: "Serviços", text: "Ordem de serviço organizada do check-in à entrega." },
    { icon: "ChartBar", name: "Inteligência", text: "Decisão com dado real, não com achismo." },
  ],
};

export const HOW_IT_WORKS = {
  title: "Do improviso ao controle, em 3 passos.",
  steps: [
    { icon: "ClipboardText", name: "Cadastre", text: "clientes, estoque e catálogo, uma vez só." },
    { icon: "PlayCircle", name: "Opere", text: "abra OS, registre vendas, controle o caixa, tudo no mesmo lugar." },
    { icon: "ChartLineUp", name: "Acompanhe", text: "veja o resultado real da loja, sem planilha paralela." },
  ],
};

export const SYSTEM_PREVIEW = {
  title: "Veja o Fluxoly de verdade.",
  subtitle: "Sem mockup genérico — a tela que você vai usar todos os dias.",
};

export const DIFFERENTIATORS = {
  title: "Por que usar o Fluxoly?",
  rows: [
    { fluxoly: "Operação centralizada", traditional: "Ferramentas separadas" },
    { fluxoly: "Visão da operação", traditional: "Informações dispersas" },
    { fluxoly: "Controle de estoque", traditional: "Controle manual" },
    { fluxoly: "Financeiro integrado", traditional: "Planilhas" },
    { fluxoly: "Assistência técnica organizada", traditional: "Processos separados" },
  ],
};

export const SOCIAL_PROOF = {
  title: "Quem usa, recomenda",
  placeholder: "[DEFINIR — aguardando primeiro cliente/piloto citável]",
};

export const PRICING = {
  title: "Um plano para cada estágio da sua loja.",
  placeholder:
    "[DEFINIR — faixas e valores dependem da decisão de monetização em docs/company/PRODUCT_REQUIREMENTS.md]",
  ctaPrimary: "Começar agora",
  ctaSecondary: "Falar com o time",
};

export const FAQ = {
  title: "Perguntas frequentes",
  items: [
    {
      question: "O que é o Fluxoly?",
      answer:
        "O Fluxoly é uma plataforma de gestão para lojas especializadas em dispositivos móveis premium — reúne vendas, estoque, financeiro, assistência técnica e inteligência de negócio em um único sistema.",
    },
    {
      question: "Preciso trocar todo o meu processo para usar o Fluxoly?",
      answer: "Não. O Fluxoly se adapta à operação da loja — não o contrário.",
    },
    {
      question: "O Fluxoly serve para qualquer tipo de loja?",
      answer:
        "O Fluxoly é feito especificamente para lojas especializadas em dispositivos móveis premium, não para varejo genérico.",
    },
    {
      question: "Existe um período de teste?",
      answer: "[DEFINIR — depende da estratégia comercial em docs/company/RELEASE_STRATEGY.md]",
    },
    {
      question: "Como funciona o suporte?",
      answer: "[DEFINIR]",
    },
  ],
};

export const CTA_FINAL = {
  title: "Pronto para organizar sua operação?",
  cta: "Começar agora",
};

export const FOOTER = {
  links: [
    { label: "Produto", href: "#funcionalidades" },
    { label: "Sobre", href: "#" },
    { label: "Planos", href: "#planos" },
    { label: "FAQ", href: "#faq" },
    { label: "Contato", href: "#cta-final" },
  ],
  copyright: "© Fluxoly, todos os direitos reservados.",
};
