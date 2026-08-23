import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { chartColor } from "@/lib/chart-theme";

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const data = payload[0];
  
  // Calcula total dinamicamente (será passado via context no futuro)
  const value = data.value || 0;
  
  return (
    <div className="bg-popover/95 backdrop-blur-sm border border-border rounded-lg p-3 shadow-xl text-sm animate-in fade-in-50 zoom-in-95 duration-200">
      <p className="font-semibold text-foreground">{data.name}</p>
      <p className="text-xs text-muted-foreground mt-1">Total: <span className="font-medium text-foreground">{value} serviço{value !== 1 ? 's' : ''}</span></p>
    </div>
  );
}

function LegendItem({ name, color, percentage }) {
  return (
    <div className="flex items-center gap-2 py-2">
      <div
        className="w-3 h-3 rounded-full flex-shrink-0 shadow-sm"
        style={{ backgroundColor: color }}
      />
      <span className="text-xs text-muted-foreground truncate">{name}</span>
      <span className="text-xs font-medium text-foreground ml-auto">{percentage}%</span>
    </div>
  );
}

export default function ServicesChartCard({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card rounded-xl border border-border p-5 flex items-center justify-center h-48 text-muted-foreground text-sm">
        Sem dados de serviços
      </div>
    );
  }

  // Calcula total e percentuais
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const dataWithPercentage = data.map((item) => ({
    ...item,
    percentage: total > 0 ? Math.round((item.value / total) * 100) : 0,
  }));

  return (
    <div className="bg-card rounded-xl border border-border p-5 flex flex-col h-full">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-card-foreground">Serviços Mais Realizados</h3>
        <p className="text-xs text-muted-foreground mt-1">Total: {total} serviços</p>
      </div>
      
      <div className="grid grid-cols-2 gap-4 flex-1">
        {/* Gráfico */}
        <div className="col-span-2 lg:col-span-1 flex items-center justify-center">
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={dataWithPercentage}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={85}
                paddingAngle={2}
                dataKey="value"
                nameKey="name"
                animationDuration={800}
                animationEasing="ease-out"
              >
                {dataWithPercentage.map((_, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={chartColor(i)}
                    style={{ filter: "drop-shadow(0 1px 3px rgba(0,0,0,0.1))" }}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} cursor={false} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legenda em grid */}
        <div className="col-span-2 lg:col-span-1 overflow-y-auto pr-2">
          <div className="space-y-1">
            {dataWithPercentage.slice(0, 10).map((item, i) => (
              <LegendItem
                key={item.name}
                name={item.name}
                color={chartColor(i)}
                percentage={item.percentage}
              />
            ))}
            {dataWithPercentage.length > 10 && (
              <div className="text-xs text-muted-foreground pt-2 border-t border-border">
                + {dataWithPercentage.length - 10} serviços
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
