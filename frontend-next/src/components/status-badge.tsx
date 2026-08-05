import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// Espelha os 3 status reais de fluxoly_core.py (STATUS_EM_ANDAMENTO/FINALIZADO/CANCELADO).
const STATUS_STYLES: Record<string, string> = {
  Finalizado:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400",
  Cancelado: "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400",
  "Em andamento":
    "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400",
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? "bg-muted text-muted-foreground";
  return (
    <Badge variant="secondary" className={cn("font-normal", style)}>
      {status || "—"}
    </Badge>
  );
}
