// Cores semânticas do Light Mode, recalibradas para WCAG AA (Fase 3.0 -- ver
// docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md secao 3). Mesmo
// matiz (hue) das versões de Dark Mode já em produção, luminosidade reduzida até passar
// 4.5:1 no cenário real de uso: badge.jsx renderiza essas cores como texto direto sobre um
// fundo do próprio tom a 10% de opacidade ("bg-<cor>/10 text-<cor>"), composto sobre a
// superfície clara por baixo -- não contra branco puro. `success` e `warning` recalibrados
// na revisão final da Fase 3.0 (2026-08-20) depois que o teste passou a medir o par
// texto-vs-tint-composto (pior caso entre as duas superfícies reais, card #FFFFFF e fundo
// de página #F5F6FA) em vez de texto-vs-branco puro.
//
// Estas constantes são a fonte de verdade do CÁLCULO de contraste (testado em
// theme-tokens.test.js). Os valores literais equivalentes em frontend/src/index.css
// (bloco @media (prefers-color-scheme: dark) e :root[data-theme="dark"] usam os valores
// ORIGINAIS, inalterados -- só o Light Mode precisava de recalibração) precisam ser
// mantidos manualmente em sincronia com este arquivo -- Tailwind v4 (@theme) não importa
// constantes JS em tempo de build.
export const LIGHT_SURFACE = "#FFFFFF";

export const LIGHT_SEMANTIC = {
  destructive: "#BD290F",
  success: "#1E754D",
  warning: "#8F5D07",
  info: "#0F61B3",
};
