import { cn } from "@/lib/utils";
import { interactiveRowClassName } from "@/lib/interaction";

/**
 * Tabela real da Foundation (Fase 3.1) — substitui o padrão de HTML cru com bordas manuais
 * repetido por arquivo (ex.: Reports.jsx, OperationalCosts.jsx, Users.jsx). Migração tela a tela
 * a partir da Fase 3.3 (`OrderTable.jsx` é o primeiro consumidor real).
 *
 * @param {{
 *   columns: Array<{ key: string, header: string, render?: (row: any) => import("react").ReactNode, className?: string, headerClassName?: string }>,
 *   rows: Array<any>,
 *   getRowKey: (row: any) => string | number,
 *   getRowProps?: (row: any) => object,
 *   stickyHeader?: boolean,
 *   onRowClick?: (row: any) => void,
 *   className?: string,
 * }} props
 */
export function DataTable({ columns, rows, getRowKey, getRowProps, stickyHeader = false, onRowClick, className }) {
  return (
    <div className={cn("overflow-x-auto rounded-xl border border-border", className)}>
      <table className="w-full text-sm">
        <thead className={cn(stickyHeader && "sticky top-0 z-10 bg-card")}>
          <tr className="border-b border-border">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  "text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider",
                  col.headerClassName
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row) => (
            <tr
              key={getRowKey(row)}
              {...(getRowProps ? getRowProps(row) : null)}
              role={onRowClick ? "button" : undefined}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={
                onRowClick
                  ? (e) => {
                      if (e.key === "Enter") {
                        onRowClick(row);
                      } else if (e.key === " ") {
                        e.preventDefault();
                        onRowClick(row);
                      }
                    }
                  : undefined
              }
              className={cn(onRowClick && interactiveRowClassName, onRowClick && "cursor-pointer")}
            >
              {columns.map((col) => (
                <td key={col.key} className={cn("px-4 py-3", col.className)}>
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
