// Convenção de hover/foco para linhas de tabela e cards clicáveis (Fase 2 do Design System,
// PLAN-design-system-fase2.md) — transição CSS pura, não Motion (elemento sem ciclo de montagem
// próprio via Portal do Radix nem estado de entrada/saída — ver ENGINEERING_GUIDE.md §3.2 para a
// regra de quando usar cada um). Reaproveitar nestas classes em vez de reescrever a combinação a
// cada página migrada.
export const interactiveRowClassName =
  "transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

export const interactiveCardClassName =
  "transition-colors hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";
