import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/constants";

const colorMap = {
  primary: "bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-blue-500/20 text-blue-400",
  green:   "bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border-emerald-500/20 text-emerald-400",
  amber:   "bg-gradient-to-br from-amber-500/20 to-amber-600/10 border-amber-500/20 text-amber-400",
  red:     "bg-gradient-to-br from-red-500/20 to-red-600/10 border-red-500/20 text-red-400",
  blue:    "bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-blue-500/20 text-blue-400",
};

const iconColorMap = {
  primary: "bg-blue-500/15 text-blue-400",
  green:   "bg-emerald-500/15 text-emerald-400",
  amber:   "bg-amber-500/15 text-amber-400",
  red:     "bg-red-500/15 text-red-400",
  blue:    "bg-blue-500/15 text-blue-400",
};

export default function KpiCard({ title, value, icon: Icon, isCurrency = true, color = "primary", subtitle }) {
  return (
    <div className={cn(
      "bg-card rounded-xl border p-5 transition-all duration-300 ease-out",
      "hover:shadow-lg hover:scale-[1.02] hover:border-opacity-100",
      "group",
      colorMap[color] || colorMap.primary
    )}>
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-1">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest opacity-80">
            {title}
          </p>
          <p className="text-3xl font-bold text-card-foreground tracking-tight group-hover:text-foreground transition-colors">
            {isCurrency ? formatCurrency(value) : (value ?? "—")}
          </p>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-2 opacity-80">
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
