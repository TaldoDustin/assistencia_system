import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/constants";

const colorMap = {
  primary: "bg-primary/10 text-primary",
  green:   "bg-emerald-500/10 text-emerald-400",
  amber:   "bg-amber-500/10 text-amber-400",
  red:     "bg-red-500/10 text-red-400",
  blue:    "bg-blue-500/10 text-blue-400",
};

export default function KpiCard({ title, value, icon: Icon, isCurrency = true, color = "primary", subtitle }) {
  return (
    <div className="bg-card rounded-xl border border-border p-5 hover:shadow-lg transition-shadow duration-300">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">{title}</p>
          <p className="text-2xl font-bold text-card-foreground">
            {isCurrency ? formatCurrency(value) : (value ?? "—")}
          </p>
          {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
        </div>
        {Icon && (
          <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center shrink-0", colorMap[color] || colorMap.primary)}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  );
}
