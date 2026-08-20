import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        outline: "text-foreground",
        // Variantes semânticas de status (Fase 2, PLAN-design-system-fase2.md) — estilo "soft",
        // mesmo peso visual das reimplementações manuais que existiam espalhadas pelo app
        // (ex.: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"), agora centralizado
        // nos tokens de `index.css`. Usar em vez de sobrescrever `variant="outline"` com className.
        success: "border-success/30 bg-success/10 text-success",
        warning: "border-warning/30 bg-warning/10 text-warning",
        error: "border-destructive/30 bg-destructive/10 text-destructive",
        info: "border-info/30 bg-info/10 text-info",
        neutral: "border-transparent bg-muted text-muted-foreground",
        // Variante taxonômica (Fase 2, PR 5, PLAN-design-system-fase2.md) — distinta das 5 acima
        // por design: não responde "como está indo" (severidade), responde "que tipo de coisa é
        // isso" (categoria/origem/tag). Deliberadamente uma cor neutra única, sem tom por valor —
        // cor não deve carregar significado de taxonomia arbitrária. Substitui a prática de badge
        // categórico com className cru por cor (ex.: ORIGEM_BADGE em Vendas.jsx/
        // UnidadesSerializadas.jsx, CATEGORIA_BADGE em Produtos.jsx).
        tag: "border-border bg-secondary/60 text-secondary-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export function Badge({ className, variant, ...props }) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
