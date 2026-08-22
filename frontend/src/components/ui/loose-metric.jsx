import { cn } from "@/lib/utils";

/**
 * Recipiente "métrica solta" da Fase 3.1 (Foundation v2) — número + rótulo pequeno, sem moldura
 * nenhuma (spec §7/§8, ex.: "Vendas hoje / Ticket médio / OS abertas" lado a lado no Dashboard).
 */
export function LooseMetric({ label, value, className, valueClassName, labelClassName }) {
  return (
    <div className={cn("flex flex-col gap-0.5", className)}>
      <span className={cn("text-2xl font-bold text-card-foreground tracking-tight", valueClassName)}>
        {value}
      </span>
      <span className={cn("text-xs text-muted-foreground", labelClassName)}>{label}</span>
    </div>
  );
}
