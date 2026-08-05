"use client";

import { use, useCallback } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { ArrowLeft } from "@phosphor-icons/react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/status-badge";
import { Separator } from "@/components/ui/separator";
import { ApiError, getOrdem } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/format";
import { useApiQuery } from "@/hooks/use-api-query";

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm text-foreground">{value || "—"}</span>
    </div>
  );
}

export default function OsDetailPage(props: PageProps<"/os/[id]">) {
  const { id } = use(props.params);

  const fetchOrdem = useCallback(async () => {
    try {
      const res = await getOrdem(id);
      return res.ordem;
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        throw new Error("OS não encontrada.");
      }
      throw new Error(err instanceof ApiError ? err.message : "Falha ao carregar a OS.");
    }
  }, [id]);
  const { data: ordem, error, loading } = useApiQuery(`ordem:${id}`, fetchOrdem);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 text-muted-foreground"
          render={<Link href="/os" />}
        >
          <ArrowLeft />
          Ordens de Serviço
        </Button>
      </div>

      {loading ? (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
      ) : error ? (
        <Card className="border-destructive/30">
          <CardContent className="py-8 text-center text-sm text-destructive">
            {error}
          </CardContent>
        </Card>
      ) : ordem ? (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="flex flex-col gap-4"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold tracking-tight">
                OS #{ordem.id} — {ordem.cliente || "Cliente não informado"}
              </h2>
              <StatusBadge status={ordem.status} />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="border-border/60 shadow-none lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Detalhes
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Tipo" value={ordem.tipo} />
                <Field label="Técnico" value={ordem.tecnico} />
                <Field label="Vendedor" value={ordem.vendedor} />
                <Field label="Aparelho" value={ordem.modelo || ordem.aparelho} />
                <Field label="Cor" value={ordem.cor} />
                <Field label="IMEI" value={ordem.imei} />
                <Field label="Data" value={formatDate(ordem.data)} />
                <Field label="Data de finalização" value={formatDate(ordem.data_finalizado)} />
                <div className="sm:col-span-2">
                  <Field label="Reparos" value={ordem.reparos.join(", ")} />
                </div>
                <div className="sm:col-span-2">
                  <Field label="Observações" value={ordem.observacoes} />
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/60 shadow-none">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Financeiro
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Valor cobrado</span>
                  <span className="tabular-nums">{formatCurrency(ordem.valor_cobrado)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Desconto</span>
                  <span className="tabular-nums">{formatCurrency(ordem.valor_descontado)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Custo de peças</span>
                  <span className="tabular-nums">{formatCurrency(ordem.custo_pecas)}</span>
                </div>
                <Separator />
                <div className="flex items-center justify-between font-medium">
                  <span>Faturamento</span>
                  <span className="tabular-nums">{formatCurrency(ordem.faturamento)}</span>
                </div>
                <div className="flex items-center justify-between font-medium text-emerald-600 dark:text-emerald-400">
                  <span>Lucro</span>
                  <span className="tabular-nums">{formatCurrency(ordem.lucro)}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {ordem.pecas_usadas.length > 0 && (
            <Card className="border-border/60 shadow-none">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Peças utilizadas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col divide-y divide-border/60">
                  {ordem.pecas_usadas.map((peca, i) => (
                    <div key={`${peca.estoque_id}-${i}`} className="flex items-center justify-between py-2.5 text-sm first:pt-0 last:pb-0">
                      <div className="flex flex-col">
                        <span className="text-foreground">{peca.descricao}</span>
                        <span className="text-xs text-muted-foreground">
                          {peca.fornecedor || "—"} · qtd. {peca.quantidade}
                        </span>
                      </div>
                      <span className="tabular-nums text-muted-foreground">
                        {formatCurrency(peca.valor)}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>
      ) : null}
    </div>
  );
}
