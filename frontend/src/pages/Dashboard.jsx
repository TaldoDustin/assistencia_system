import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, DollarSign, TrendingUp, CheckCircle, Clock, ShoppingCart, BarChart2, Wallet, Activity } from "lucide-react";
import { dashboard as dashboardApi, constantes } from "@/api/client";
import KpiCard from "@/components/dashboard/KpiCard";
import { RevenueChart, TechnicianProfitChart, ServicesChart } from "@/components/dashboard/DashboardCharts";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/constants";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tecnicos, setTecnicos] = useState([]);
  const [filters, setFilters] = useState({ startDate: "", endDate: "", tecnico: "" });

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
  }, []);

  const handleSearch = () => fetchData(filters);

  const revenueData = data?.faturamento_por_dia
    ? Object.entries(data.faturamento_por_dia).map(([data, total]) => ({ data, total }))
    : [];

  const techData = data?.lucro_por_tecnico
    ? Object.entries(data.lucro_por_tecnico).map(([tecnico, lucro]) => ({ tecnico, lucro }))
    : [];

  const servicesData = data?.servicos_mais_feitos
    ? Object.entries(data.servicos_mais_feitos).map(([name, value]) => ({ name, value }))
    : [];

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
            <KpiCard title="Faturamento" value={data?.faturamento} icon={DollarSign} color="primary" />
            <KpiCard title="Lucro Bruto" value={data?.lucro} icon={TrendingUp} color="green" />
            <KpiCard title="Finalizadas" value={data?.finalizadas} icon={CheckCircle} isCurrency={false} color="green" />
            <KpiCard title="Em Aberto" value={data?.abertas} icon={Clock} isCurrency={false} color="amber" />
            <KpiCard title="Ticket Médio" value={data?.ticket_medio} icon={BarChart2} color="blue" />
            <KpiCard title="Resultado Líq." value={data?.resultado_liquido} icon={Wallet} color={data?.resultado_liquido >= 0 ? "green" : "red"} />
          </div>

          {/* Charts */}
          <div className="grid lg:grid-cols-2 gap-4">
            <RevenueChart data={revenueData} />
            <TechnicianProfitChart data={techData} />
          </div>
          <div className="grid lg:grid-cols-3 gap-4">
            <ServicesChart data={servicesData} />

            {/* Cost Summary */}
            <div className="lg:col-span-2 bg-card rounded-xl border border-border p-5">
              <h3 className="text-sm font-medium text-card-foreground mb-4">Resumo Financeiro</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Custo de Peças", value: data?.custo_pecas, color: "text-red-400" },
                  { label: "Custos Operacionais", value: data?.custos_op, color: "text-amber-400" },
                  { label: "Faturamento", value: data?.faturamento, color: "text-emerald-400" },
                  { label: "Lucro Bruto", value: data?.lucro, color: "text-blue-400" },
                ].map((item) => (
                  <div key={item.label} className="bg-secondary rounded-lg p-3">
                    <p className="text-xs text-muted-foreground">{item.label}</p>
                    <p className={`text-lg font-bold ${item.color}`}>{formatCurrency(item.value)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
