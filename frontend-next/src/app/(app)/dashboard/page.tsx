"use client";

import { useCallback } from "react";
import { motion } from "motion/react";
import {
  CurrencyDollar,
  TrendUp,
  ClipboardText,
  Package,
  ShoppingCart,
  Receipt,
} from "@phosphor-icons/react";

import { StatCard } from "@/components/stat-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ApiError, getDashboard } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import { useApiQuery } from "@/hooks/use-api-query";

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-[104px] w-full rounded-xl" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton className="h-64 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const fetchDashboard = useCallback(async () => {
    try {
      return await getDashboard();
    } catch (err) {
      throw new Error(err instanceof ApiError ? err.message : "Falha ao carregar o dashboard.");
    }
  }, []);
  const { data, error, loading } = useApiQuery("dashboard", fetchDashboard);

  if (loading) return <DashboardSkeleton />;

  if (error) {
    return (
      <Card className="border-destructive/30">
        <CardContent className="py-8 text-center text-sm text-destructive">
          {error}
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const cards = [
    {
      label: "Faturamento total",
      value: formatCurrency(data.faturamento_total),
      icon: <CurrencyDollar className="size-4" />,
      tone: "default" as const,
    },
    {
      label: "Lucro total",
      value: formatCurrency(data.lucro_total),
      icon: <TrendUp className="size-4" />,
      tone: "positive" as const,
    },
    {
      label: "Resultado líquido",
      value: formatCurrency(data.resultado_liquido),
      icon: <Receipt className="size-4" />,
      tone: data.resultado_liquido >= 0 ? ("positive" as const) : ("negative" as const),
    },
    {
      label: "Ticket médio",
      value: formatCurrency(data.ticket_medio),
      icon: <ClipboardText className="size-4" />,
    },
    {
      label: "OS finalizadas",
      value: formatNumber(data.ordens_finalizadas),
      icon: <ClipboardText className="size-4" />,
    },
    {
      label: "OS abertas",
      value: formatNumber(data.ordens_abertas),
      icon: <ClipboardText className="size-4" />,
    },
    {
      label: "Estoque (valor)",
      value: formatCurrency(data.gasto_total_estoque),
      icon: <Package className="size-4" />,
    },
    {
      label: "Compras pendentes",
      value: formatNumber(data.shopping_pendentes),
      icon: <ShoppingCart className="size-4" />,
      hint: data.shopping_urgentes > 0 ? `${data.shopping_urgentes} urgente(s)` : undefined,
      tone: data.shopping_urgentes > 0 ? ("negative" as const) : ("default" as const),
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col gap-8"
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {cards.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="border-border/60 shadow-none">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Lucro por técnico
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {data.lucro_por_tecnico.length === 0 && (
              <p className="text-sm text-muted-foreground">Sem dados no período.</p>
            )}
            {data.lucro_por_tecnico.slice(0, 6).map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <span className="text-foreground">{item.name}</span>
                <span className="font-medium tabular-nums text-muted-foreground">
                  {formatCurrency(item.value)}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-border/60 shadow-none">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Serviços mais feitos
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {data.servicos_mais_feitos.length === 0 && (
              <p className="text-sm text-muted-foreground">Sem dados no período.</p>
            )}
            {data.servicos_mais_feitos.slice(0, 6).map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <span className="text-foreground">{item.name}</span>
                <Badge variant="secondary" className="tabular-nums">
                  {formatNumber(item.value)}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {data.resumo_por_vendedor.length > 0 && (
        <Card className="border-border/60 shadow-none">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Resumo por vendedor
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col divide-y divide-border/60">
              {data.resumo_por_vendedor.map((item) => (
                <div
                  key={item.vendedor}
                  className="flex items-center justify-between py-2.5 text-sm first:pt-0 last:pb-0"
                >
                  <span className="text-foreground">{item.vendedor}</span>
                  <div className="flex items-center gap-4 text-muted-foreground">
                    <span>{item.os_total} OS</span>
                    <span className="tabular-nums">{formatCurrency(item.faturamento)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}
