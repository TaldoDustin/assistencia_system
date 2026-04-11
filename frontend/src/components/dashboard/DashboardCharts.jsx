import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { formatCurrency } from "@/lib/constants";

const COLORS = [
  "hsl(221 83% 53%)", "hsl(160 60% 45%)", "hsl(38 92% 50%)",
  "hsl(280 65% 60%)", "hsl(0 84% 60%)", "hsl(200 70% 50%)",
];

function CustomTooltip({ active, payload, label, currency }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-popover border border-border rounded-lg p-3 shadow-xl text-sm">
      {label && <p className="text-muted-foreground mb-1">{label}</p>}
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color || entry.fill }}>
          {entry.name}: {currency ? formatCurrency(entry.value) : entry.value}
        </p>
      ))}
    </div>
  );
}

export function RevenueChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card rounded-xl border border-border p-5 flex items-center justify-center h-48 text-muted-foreground text-sm">
        Sem dados de faturamento
      </div>
    );
  }
  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <h3 className="text-sm font-medium text-card-foreground mb-4">Faturamento por Dia</h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <defs>
            <linearGradient id="colorFat" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(221 83% 53%)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="hsl(221 83% 53%)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 47% 19%)" />
          <XAxis dataKey="data" tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(v) => `R$${(v/1000).toFixed(0)}k`} />
          <Tooltip content={<CustomTooltip currency />} />
          <Area
            type="monotone"
            dataKey="total"
            name="Faturamento"
            stroke="hsl(221 83% 53%)"
            fill="url(#colorFat)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TechnicianProfitChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card rounded-xl border border-border p-5 flex items-center justify-center h-48 text-muted-foreground text-sm">
        Sem dados por técnico
      </div>
    );
  }
  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <h3 className="text-sm font-medium text-card-foreground mb-4">Lucro por Técnico</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 47% 19%)" />
          <XAxis dataKey="tecnico" tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(v) => `R$${(v/1000).toFixed(0)}k`} />
          <Tooltip content={<CustomTooltip currency />} />
          <Bar dataKey="lucro" name="Lucro" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ServicesChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card rounded-xl border border-border p-5 flex items-center justify-center h-48 text-muted-foreground text-sm">
        Sem dados de serviços
      </div>
    );
  }
  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <h3 className="text-sm font-medium text-card-foreground mb-4">Serviços Mais Realizados</h3>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={80}
            paddingAngle={3}
            dataKey="value"
            nameKey="name"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(v) => <span style={{ color: "hsl(215 20% 55%)", fontSize: 11 }}>{v}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
