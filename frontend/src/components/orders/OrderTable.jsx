import { Link } from "react-router-dom";
import { Pencil, Trash } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { interactiveRowClassName } from "@/lib/interaction";
import OrderStatusBadge from "./OrderStatusBadge";
import { formatCurrency, getOrderDisplayNumber } from "@/lib/constants";

export default function OrderTable({ orders = [], onDelete, onEditClick }) {
  if (orders.length === 0) {
    return (
      <EmptyState
        title="Nenhuma ordem encontrada"
        description="Ajuste os filtros ou crie uma nova ordem de serviço."
      />
    );
  }

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">#ID</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Cliente</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Modelo / Cor</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Técnico</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Data</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Valor</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {orders.map((os) => (
              <tr
                key={os.id}
                className={interactiveRowClassName}
                data-testid={`order-row-${os.id}`}
                data-context-row={os.id}
              >
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                  #{getOrderDisplayNumber(os)}
                </td>
                <td className="px-4 py-3 font-medium text-card-foreground max-w-[140px] truncate">
                  {os.cliente}
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  <span className="block">{os.modelo}</span>
                  {os.cor && <span className="text-xs">{os.cor}</span>}
                </td>
                <td className="px-4 py-3 text-muted-foreground">{os.tecnico || "—"}</td>
                <td className="px-4 py-3">
                  <OrderStatusBadge status={os.status} />
                </td>
                <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                  {os.data_os ? new Date(os.data_os).toLocaleDateString("pt-BR") : "—"}
                </td>
                <td className="px-4 py-3 text-card-foreground font-medium whitespace-nowrap">
                  {formatCurrency(os.valor_cobrado || os.valor_descontado || 0)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1 justify-end">
                    <Link to={`/ordens/editar/${os.id}`} onClick={() => onEditClick?.(os.id)}>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        aria-label={`Editar ordem ${getOrderDisplayNumber(os)}`}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive hover:text-destructive"
                      aria-label={`Excluir ordem ${getOrderDisplayNumber(os)}`}
                      onClick={() => onDelete?.(os.id)}
                    >
                      <Trash className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
