import { Wallet, TrendingUp, TrendingDown, Percent } from "lucide-react";
import {
  AreaChart, Area, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { PreviewBadge } from "@/components/ui/preview-badge";
import KpiCard from "@/components/dashboard/KpiCard";
import { formatCurrency } from "@/lib/constants";
import { DEMO_FINANCEIRO } from "@/lib/demoData";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-popover/95 backdrop-blur-sm border border-border rounded-lg p-3 shadow-xl text-sm">
      <p className="font-semibold text-foreground">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color || entry.fill }} className="mt-1">
          <span className="text-muted-foreground">{entry.name}:</span> <span className="font-medium">{formatCurrency(entry.value)}</span>
        </p>
      ))}
    </div>
  );
}

export default function Financeiro() {
  const { fluxoCaixa, contasReceber, contasPagar, margemMedia, ultimos30dias } = DEMO_FINANCEIRO;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Financeiro</h1>
          <p className="text-muted-foreground text-sm">Fluxo de caixa, contas e margem</p>
        </div>
        <PreviewBadge />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Fluxo de Caixa" value={fluxoCaixa} icon={Wallet} color="blue" />
        <KpiCard title="Contas a Receber" value={contasReceber} icon={TrendingUp} color="green" />
        <KpiCard title="Contas a Pagar" value={contasPagar} icon={TrendingDown} color="red" />
        <KpiCard title="Margem Média" value={`${(margemMedia * 100).toFixed(0)}%`} isCurrency={false} icon={Percent} color="amber" />
      </div>

      <div className="bg-card rounded-xl border border-border p-5">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-card-foreground">Faturamento e Margem (últimos 30 dias)</h3>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={ultimos30dias} margin={{ top: 5, right: 15, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="colorFaturamento" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorMargem" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 47% 19%)" vertical={false} style={{ opacity: 0.5 }} />
            <XAxis dataKey="dia" tick={{ fill: "hsl(215 20% 55%)", fontSize: 12 }} tickLine={false} axisLine={false} />
            <YAxis
              tick={{ fill: "hsl(215 20% 55%)", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="faturamento" name="Faturamento" stroke="#3B82F6" fill="url(#colorFaturamento)" strokeWidth={2.5} />
            <Area type="monotone" dataKey="margem" name="Margem" stroke="#10B981" fill="url(#colorMargem)" strokeWidth={2.5} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
