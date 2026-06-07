import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatCurrency } from "@/lib/constants";

const COLORS = [
  "#3B82F6", // Azul
  "#10B981", // Verde
  "#F59E0B", // Âmbar
  "#EF4444", // Vermelho
  "#8B5CF6", // Roxo
  "#EC4899", // Rosa
  "#14B8A6", // Teal
  "#F97316", // Laranja
];

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-popover/95 backdrop-blur-sm border border-border rounded-lg p-3 shadow-xl text-sm animate-in fade-in-50 zoom-in-95 duration-200">
      <p className="font-semibold text-foreground">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color || entry.fill }} className="mt-1">
          <span className="text-muted-foreground">{entry.name}:</span> <span className="font-medium">{formatCurrency(entry.value)}</span>
        </p>
      ))}
    </div>
  );
}

export default function TechnicianProfitChartCard({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card rounded-xl border border-border p-5 flex items-center justify-center h-48 text-muted-foreground text-sm">
        Sem dados por técnico
      </div>
    );
  }

  const totalLucro = data.reduce((sum, item) => sum + item.lucro, 0);
  const avgLucro = totalLucro / data.length;

  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-card-foreground">Lucro por Técnico</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Total: <span className="text-foreground font-medium">{formatCurrency(totalLucro)}</span>
        </p>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 5, right: 15, left: 0, bottom: 5 }}>
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="hsl(222 47% 19%)" 
            vertical={false}
            style={{ opacity: 0.5 }}
          />
          <XAxis 
            dataKey="tecnico" 
            tick={{ fill: "hsl(215 20% 55%)", fontSize: 12 }} 
            tickLine={false} 
            axisLine={false}
            style={{ opacity: 0.7 }}
          />
          <YAxis 
            tick={{ fill: "hsl(215 20% 55%)", fontSize: 12 }} 
            tickLine={false} 
            axisLine={false} 
            tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
            style={{ opacity: 0.7 }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(59, 130, 246, 0.1)" }} />
          <Bar 
            dataKey="lucro" 
            name="Lucro" 
            radius={[6, 6, 0, 0]}
            isAnimationActive={true}
            animationDuration={800}
          >
            {data.map((_, i) => (
              <Cell 
                key={`cell-${i}`} 
                fill={COLORS[i % COLORS.length]}
                style={{ filter: "drop-shadow(0 1px 2px rgba(0,0,0,0.1))" }}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
