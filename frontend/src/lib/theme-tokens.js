// Cores semânticas do Light Mode, recalibradas para WCAG AA (Fase 3.0 -- ver
// docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md secao 3). Mesmo
// matiz (hue) das versões de Dark Mode já em produção, luminosidade reduzida até passar
// 4.5:1 contra fundo/superfície claros (badge.jsx usa essas cores como texto direto sobre
// um fundo tintado a 10% de opacidade -- o par que precisa passar é texto-vs-branco).
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
  success: "#1F7A50",
  warning: "#9B6508",
  info: "#0F61B3",
};
