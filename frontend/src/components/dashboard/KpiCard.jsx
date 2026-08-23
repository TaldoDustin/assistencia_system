import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/constants";

// Cores migradas para os tokens de tema (Fase 3.1 -- corrige KI-050: as classes anteriores
// (emerald/amber/red/blue-400) eram calibradas só para o Dark Mode anterior à Fase 3.0 e caíam
// para contraste ~1,5:1 em fundo claro). Mesmo resultado visual em Dark Mode -- os tokens já
// foram calibrados para ficar próximos das cores anteriores (Fase 3.0, ver theme-tokens.js).
const colorMap = {
  primary: "bg-gradient-to-br from-info/20 to-info/10 border-info/20 text-info",
  green:   "bg-gradient-to-br from-success/20 to-success/10 border-success/20 text-success",
  amber:   "bg-gradient-to-br from-warning/20 to-warning/10 border-warning/20 text-warning",
  red:     "bg-gradient-to-br from-destructive/20 to-destructive/10 border-destructive/20 text-destructive",
  blue:    "bg-gradient-to-br from-info/20 to-info/10 border-info/20 text-info",
};

const iconColorMap = {
  primary: "bg-info/15 text-info",
  green:   "bg-success/15 text-success",
  amber:   "bg-warning/15 text-warning",
  red:     "bg-destructive/15 text-destructive",
  blue:    "bg-info/15 text-info",
};

export default function KpiCard({ title, value, icon: Icon, isCurrency = true, color = "primary", subtitle }) {
  return (
    <div className={cn(
      "bg-card rounded-xl border p-5 transition-all duration-300 ease-out",
      "hover:shadow-lg hover:scale-[1.02] hover:border-opacity-100",
      "group",
      colorMap[color] || colorMap.primary
    )}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0 space-y-1">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest opacity-80 truncate">
            {title}
          </p>
          <p
            className="text-2xl font-bold text-card-foreground tracking-tight group-hover:text-foreground transition-colors truncate"
            title={isCurrency ? formatCurrency(value) : (value ?? "—")}
          >
            {isCurrency ? formatCurrency(value) : (value ?? "—")}
          </p>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-2 opacity-80 truncate">
              {subtitle}
            </p>
          )}
        </div>
        {Icon && (
          <div className={cn(
            "h-12 w-12 rounded-lg flex items-center justify-center shrink-0",
            "group-hover:scale-110 transition-transform duration-300",
            iconColorMap[color] || iconColorMap.primary
          )}>
            <Icon className="h-6 w-6" />
          </div>
        )}
      </div>
    </div>
  );
}
