import { lazy, Suspense, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  Loader2, DollarSign, TrendingUp, CheckCircle, Clock, BarChart2, Wallet, Package, Tag,
  Warehouse, Users, ShoppingCart, Sparkles,
} from "lucide-react";
import { dashboard as dashboardApi, constantes, clientes as clientesApi } from "@/api/client";
import KpiCard from "@/components/dashboard/KpiCard";
import { PreviewBadge } from "@/components/ui/preview-badge";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/constants";

const RevenueChartCard = lazy(() => import("@/components/dashboard/RevenueChartCard"));
const TechnicianProfitChartCard = lazy(() => import("@/components/dashboard/TechnicianProfitChartCard"));
const ServicesChartCard = lazy(() => import("@/components/dashboard/ServicesChartCard"));

function ChartFallback() {
  return (
    <div className="bg-card rounded-xl border border-border p-5 flex items-center justify-center h-48 text-muted-foreground text-sm">
      <Loader2 className="h-5 w-5 animate-spin" />
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tecnicos, setTecnicos] = useState([]);
  const [filters, setFilters] = useState({ startDate: "", endDate: "", tecnico: "" });
  const [totalClientes, setTotalClientes] = useState(null);

  const fetchData = async (params = {}) => {
    setLoading(true);
    try {
      const res = await dashboardApi.get(Object.fromEntries(Object.entries(params).filter(([, v]) => v)));
      if (res?.ok) setData(res);
      else toast.error("Erro ao carregar dashboard");
    } catch {
      toast.error("Erro ao carregar dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    constantes.get().then((res) => {
      if (res?.ok) setTecnicos(res.tecnicos || []);
    });
    clientesApi.list().then((res) => {
      if (res?.ok) setTotalClientes(res.total ?? 0);
    });
  }, []);

  const handleSearch = () => fetchData(filters);

  const revenueData = data?.faturamento_por_dia?.map((item) => ({
    data: item.date,
    total: item.value,
  })) || [];

  const techData = data?.lucro_por_tecnico?.map((item) => ({
    tecnico: item.name,
    lucro: item.value,
  })) || [];

  const servicesData = data?.servicos_mais_feitos || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground text-sm">Visão geral do negócio</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Input
            type="date"
            value={filters.startDate}
            onChange={(e) => setFilters((p) => ({ ...p, startDate: e.target.value }))}
            className="w-36"
          />
          <Input
            type="date"
            value={filters.endDate}
            onChange={(e) => setFilters((p) => ({ ...p, endDate: e.target.value }))}
            className="w-36"
          />
          <Select value={filters.tecnico || ""} onValueChange={(v) => setFilters((p) => ({ ...p, tecnico: v === "all" ? "" : v }))}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Técnico" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {tecnicos.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button onClick={handleSearch} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Filtrar"}
          </Button>
        </div>
      </div>

      {loading && !data ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <KpiCard title="Faturamento" value={data?.faturamento_total} icon={DollarSign} color="primary" />
            <KpiCard title="Lucro Bruto" value={data?.lucro_total} icon={TrendingUp} color="green" />
            <KpiCard title="Finalizadas" value={data?.ordens_finalizadas} icon={CheckCircle} isCurrency={false} color="green" />
            <KpiCard title="Em Aberto" value={data?.ordens_abertas} icon={Clock} isCurrency={false} color="amber" />
            <KpiCard title="Peças Pendentes" value={data?.shopping_pendentes} icon={Package} isCurrency={false} color="amber" />
            <KpiCard title="Urgentes" value={data?.shopping_urgentes} icon={Tag} isCurrency={false} color="red" />
            <KpiCard title="Ticket Médio" value={data?.ticket_medio} icon={BarChart2} color="blue" />
            <KpiCard title="Resultado Líq." value={data?.resultado_liquido} icon={Wallet} color={data?.resultado_liquido >= 0 ? "green" : "red"} />
            <KpiCard title="Investido em Estoque" value={data?.gasto_total_estoque} icon={Warehouse} color="blue" />
            <KpiCard title="Clientes Cadastrados" value={totalClientes} icon={Users} isCurrency={false} color="primary" />
          </div>

          {/* Charts */}
          <Suspense fallback={<div className="grid lg:grid-cols-2 gap-4"><ChartFallback /><ChartFallback /></div>}>
            <div className="grid lg:grid-cols-2 gap-4">
              <RevenueChartCard data={revenueData} />
              <TechnicianProfitChartCard data={techData} />
            </div>
          </Suspense>
          <div className="grid lg:grid-cols-3 gap-4">
            <Suspense fallback={<ChartFallback />}>
              <ServicesChartCard data={servicesData} />
            </Suspense>

            {/* Cost Summary */}
            <div className="lg:col-span-2 bg-card rounded-xl border border-border p-5">
              <h3 className="text-sm font-medium text-card-foreground mb-4">Resumo Financeiro</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Custo de Peças", value: data?.custo_consumido_periodo, color: "text-red-400" },
                  { label: "Custos Operacionais", value: data?.custos_operacionais_periodo, color: "text-amber-400" },
                  { label: "Faturamento", value: data?.faturamento_total, color: "text-emerald-400" },
                  { label: "Lucro Bruto", value: data?.lucro_total, color: "text-blue-400" },
                ].map((item) => (
                  <div key={item.label} className="bg-secondary rounded-lg p-3">
                    <p className="text-xs text-muted-foreground">{item.label}</p>
                    <p className={`text-lg font-bold ${item.color}`}>{formatCurrency(item.value)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Faturamento por Vendedor */}
          <div className="bg-card rounded-xl border border-border p-5">
            <h3 className="text-sm font-medium text-card-foreground mb-4">Faturamento por Vendedor</h3>
            {(data?.resumo_por_vendedor || []).length === 0 ? (
              <p className="text-sm text-muted-foreground">Nenhuma OS com vendedor registrado no período.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">Vendedor</th>
                      <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">OS</th>
                      <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">Faturamento</th>
                      <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">Lucro</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {data.resumo_por_vendedor.map((v) => (
                      <tr key={v.vendedor}>
                        <td className="px-3 py-2 font-medium text-card-foreground">{v.vendedor}</td>
                        <td className="px-3 py-2 text-muted-foreground">{v.os_total}</td>
                        <td className="px-3 py-2 text-emerald-400">{formatCurrency(v.faturamento)}</td>
                        <td className="px-3 py-2 text-blue-400">{formatCurrency(v.lucro)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Explore mais */}
          <div className="bg-card rounded-xl border border-border p-5">
            <h3 className="text-sm font-medium text-card-foreground mb-4">Explore mais</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { to: "/vendas", label: "Vendas", Icon: ShoppingCart },
                { to: "/financeiro", label: "Financeiro", Icon: Wallet },
                { to: "/insights", label: "Fluxoly Insights", Icon: Sparkles },
              ].map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className="flex items-center justify-between gap-2 rounded-lg border border-border bg-secondary p-3 hover:bg-accent/40 transition-colors"
                >
                  <span className="flex items-center gap-2 text-sm font-medium text-card-foreground">
                    <item.Icon className="h-4 w-4 text-primary" />
                    {item.label}
                  </span>
                  <PreviewBadge />
                </Link>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
