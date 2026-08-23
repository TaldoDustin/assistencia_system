import { cn } from "@/lib/utils";
import { interactiveRowClassName } from "@/lib/interaction";

/**
 * Recipiente "bloco de lista" da Fase 3.1 (Foundation v2) — para listas de peso secundário que
 * não precisam da moldura completa do `Panel` (spec §7: "sem moldura própria, só divisor sutil
 * entre linhas"). `ListBlockItem` reaproveita `interactiveRowClassName` (hover/foco, já usado em
 * linhas de tabela desde a Fase 2) quando `interactive` é passado.
 */
export function ListBlock({ className, ...props }) {
  return <div className={cn("divide-y divide-border", className)} {...props} />;
}

export function ListBlockItem({ className, interactive = false, ...props }) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 py-3",
        interactive && interactiveRowClassName,
        className
      )}
      {...props}
    />
  );
}
