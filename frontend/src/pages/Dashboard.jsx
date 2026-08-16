import { lazy, Suspense, useState, useEffect } from "react";
import { toast } from "sonner";
import {
  CircleNotch, CurrencyDollar, TrendUp, CheckCircle, Clock, ChartBar, Wallet, Package, Tag,
  WarningCircle, Tray, ArrowClockwise,
} from "@phosphor-icons/react";
import { dashboard as dashboardApi, constantes } from "@/api/client";
import KpiCard from "@/components/dashboard/KpiCard";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/constants";

const RevenueChartCard = lazy(() => import("@/components/dashboard/RevenueChartCard"));
const TechnicianProfitChartCard = lazy(() => import("@/components/dashboard/TechnicianProfitChartCard"));
const ServicesChartCard = lazy(() => import("@/components/dashboard/ServicesChartCard"));

function ChartFallback() {
  return (
    <div className="bg-card rounded-xl border border-border p-5 flex items-center justify-center h-48 text-muted-foreground text-sm">
      <CircleNotch className="h-5 w-5 animate-spin" />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 sm:grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-[104px] rounded-xl" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[repeat(auto-fit,minmax(420px,1fr))] gap-4">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
      <div className="grid lg:grid-cols-3 gap-4">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="lg:col-span-2 h-48 rounded-xl" />
      </div>
    </div>
  );
}

function DashboardEmpty() {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <Tray className="h-10 w-10 text-muted-foreground" />
        <div>
          <p className="text-card-foreground font-medium">Nenhum dado no período selecionado</p>
          <p className="text-muted-foreground text-sm mt-1">
            Ajuste os filtros de data ou técnico para ver o resultado da operação.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function DashboardError({ message, onRetry }) {
  return (
    <Card className="border-destructive/40">
      <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <WarningCircle className="h-10 w-10 text-destructive" />
        <div>
          <p className="text-card-foreground font-medium">{message}</p>
          <p className="text-muted-foreground text-sm mt-1">Verifique sua conexão e tente novamente.</p>
        </div>
        <Button variant="outline" onClick={onRetry}>
          <ArrowClockwise className="h-4 w-4" />
          Tentar novamente
        </Button>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tecnicos, setTecnicos] = useState([]);
  const [filters, setFilters] = useState({ startDate: "", endDate: "", tecnico: "" });

  const fetchData = async (params = {}) => {
    setLoading(true);
    try {
      const res = await dashboardApi.get(Object.fromEntries(Object.entries(params).filter(([, v]) => v)));
      if (res?.ok) {
        setData(res);
        setError(null);
      } else {
        setError("Erro ao carregar dashboard.");
        toast.error("Erro ao carregar dashboard");
      }
    } catch {
      setError("Erro ao carregar dashboard.");
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

  const revenueData = data?.faturamento_por_dia?.map((item) => ({
    data: item.date,
    total: item.value,
  })) || [];

  const techData = data?.lucro_por_tecnico?.map((item) => ({
    tecnico: item.name,
    lucro: item.value,
  })) || [];

  const servicesData = data?.servicos_mais_feitos || [];

  const hasAnyData =
    revenueData.length > 0 ||
    techData.length > 0 ||
    servicesData.length > 0 ||
    Boolean(data?.faturamento_total) ||
    Boolean(data?.ordens_finalizadas) ||
    Boolean(data?.ordens_abertas);
  const isEmpty = Boolean(data) && !hasAnyData;

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
            {loading ? <CircleNotch className="h-4 w-4 animate-spin" /> : "Filtrar"}
          </Button>
        </div>
      </div>

      {loading && !data ? (
        <DashboardSkeleton />
      ) : error && !data ? (
        <DashboardError message={error} onRetry={handleSearch} />
      ) : (
        <>
          {error && (
            <Card className="border-destructive/40 bg-destructive/10">
              <CardContent className="flex items-center justify-between gap-3 py-3 flex-wrap">
                <div className="flex items-center gap-2 text-sm text-card-foreground">
                  <WarningCircle className="h-4 w-4 text-destructive shrink-0" />
                  {error}
                </div>
                <Button variant="outline" size="sm" onClick={handleSearch}>
                  <ArrowClockwise className="h-4 w-4" />
                  Tentar novamente
                </Button>
              </CardContent>
            </Card>
          )}

          {isEmpty ? (
            <DashboardEmpty />
          ) : (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-2 sm:grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-4">
                <KpiCard title="Faturamento" value={data?.faturamento_total} icon={CurrencyDollar} color="primary" />
                <KpiCard title="Lucro Bruto" value={data?.lucro_total} icon={TrendUp} color="green" />
                <KpiCard title="Finalizadas" value={data?.ordens_finalizadas} icon={CheckCircle} isCurrency={false} color="green" />
                <KpiCard title="Em Aberto" value={data?.ordens_abertas} icon={Clock} isCurrency={false} color="amber" />
                <KpiCard title="Peças Pendentes" value={data?.shopping_pendentes} icon={Package} isCurrency={false} color="amber" />
                <KpiCard title="Urgentes" value={data?.shopping_urgentes} icon={Tag} isCurrency={false} color="red" />
                <KpiCard title="Ticket Médio" value={data?.ticket_medio} icon={ChartBar} color="blue" />
                <KpiCard title="Resultado Líq." value={data?.resultado_liquido} icon={Wallet} color={data?.resultado_liquido >= 0 ? "green" : "red"} />
              </div>

              {/* Charts */}
              <Suspense fallback={<div className="grid grid-cols-1 lg:grid-cols-[repeat(auto-fit,minmax(420px,1fr))] gap-4"><ChartFallback /><ChartFallback /></div>}>
                <div className="grid grid-cols-1 lg:grid-cols-[repeat(auto-fit,minmax(420px,1fr))] gap-4">
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
            </>
          )}
        </>
      )}
    </div>
  );
}
