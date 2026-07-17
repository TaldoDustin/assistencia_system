import { Sparkles } from "lucide-react";
import { PreviewBadge } from "@/components/ui/preview-badge";
import { DEMO_INSIGHTS } from "@/lib/demoData";

const CARD_COLOR = {
  primary: "border-primary/30 bg-primary/10",
  green: "border-emerald-500/30 bg-emerald-500/10",
  amber: "border-amber-500/30 bg-amber-500/10",
  blue: "border-blue-500/30 bg-blue-500/10",
};

export default function Insights() {
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Fluxoly Insights
          </h1>
          <p className="text-muted-foreground text-sm">Recomendações para tomada de decisão</p>
        </div>
        <PreviewBadge />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {DEMO_INSIGHTS.map((insight) => (
          <div
            key={insight.titulo}
            className={`rounded-xl border p-5 ${CARD_COLOR[insight.cor] || "border-border bg-card"}`}
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">{insight.titulo}</p>
            <p className="text-card-foreground">{insight.texto}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
