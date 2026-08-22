import {
  AreaChart,
  Area,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import { formatCurrency } from "@/lib/constants";
import { CHART_GRID_STROKE, CHART_AXIS_TICK, CHART_CURSOR_STROKE, chartColor } from "@/lib/chart-theme";

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

export default function RevenueChartCard({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card rounded-xl border border-border p-5 flex items-center justify-center h-48 text-muted-foreground text-sm">
        Sem dados de faturamento
      </div>
    );
  }

  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-card-foreground">Faturamento por Dia</h3>
        <p className="text-xs text-muted-foreground mt-1">Evolução diária do faturamento</p>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 5, right: 15, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={chartColor(0)} stopOpacity={0.3} />
              <stop offset="95%" stopColor={chartColor(0)} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={CHART_GRID_STROKE}
            vertical={false}
            style={{ opacity: 0.5 }}
          />
          <XAxis
            dataKey="data"
            tick={CHART_AXIS_TICK}
            tickLine={false}
            axisLine={false}
            style={{ opacity: 0.7 }}
          />
          <YAxis
            tick={CHART_AXIS_TICK}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
            style={{ opacity: 0.7 }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: CHART_CURSOR_STROKE, strokeOpacity: 0.3 }} />
          <Area
            type="monotone"
            dataKey="total"
            name="Faturamento"
            stroke={chartColor(0)}
            fill="url(#colorRevenue)"
            strokeWidth={2.5}
            isAnimationActive={true}
            animationDuration={800}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
