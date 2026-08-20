import { Skeleton } from "./skeleton";
import { cn } from "@/lib/utils";

/**
 * Skeleton de lista/tabela — para as páginas legadas migradas na Fase 2, cuja maioria é
 * lista/tabela (Orders, Stock, Vendas, Financeiro, Clientes, etc.).
 * @param {{ rows?: number, className?: string }} props
 */
export function ListSkeleton({ rows = 6, className }) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full rounded-lg" />
      ))}
    </div>
  );
}

/**
 * Skeleton de grid de cards — generalização do grid de KPIs já validado em `Dashboard.jsx` (PR #46).
 * @param {{ count?: number, className?: string }} props
 */
export function CardGridSkeleton({ count = 4, className }) {
  return (
    <div
      className={cn(
        "grid grid-cols-2 sm:grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-4",
        className
      )}
    >
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className="h-[104px] rounded-xl" />
      ))}
    </div>
  );
}
