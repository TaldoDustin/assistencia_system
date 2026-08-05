"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { MagnifyingGlass, Wrench } from "@phosphor-icons/react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/status-badge";
import { ApiError, getOrdens } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/format";
import { useApiQuery } from "@/hooks/use-api-query";
import { useDebouncedValue } from "@/hooks/use-debounced-value";

function OsListSkeleton() {
  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: 8 }).map((_, i) => (
        <Skeleton key={i} className="h-11 w-full rounded-md" />
      ))}
    </div>
  );
}

function EmptyState({ hasQuery }: { hasQuery: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <Wrench className="size-5" />
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-foreground">
          {hasQuery ? "Nenhuma OS encontrada" : "Nenhuma ordem de serviço"}
        </p>
        <p className="text-sm text-muted-foreground">
          {hasQuery
            ? "Tente ajustar a busca."
            : "As ordens de serviço aparecerão aqui."}
        </p>
      </div>
    </div>
  );
}

export default function OsListPage() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 250);

  const fetchOrdens = useCallback(async () => {
    try {
      const res = await getOrdens(debouncedQuery ? { q: debouncedQuery } : undefined);
      return res.ordens;
    } catch (err) {
      throw new Error(
        err instanceof ApiError ? err.message : "Falha ao carregar as ordens de serviço.",
      );
    }
  }, [debouncedQuery]);
  const { data: ordens, error, loading } = useApiQuery(`ordens:${debouncedQuery}`, fetchOrdens);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col gap-4"
    >
      <div className="flex items-center gap-2">
        <div className="relative w-full max-w-sm">
          <MagnifyingGlass className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por cliente, aparelho, técnico..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      <Card className="border-border/60 shadow-none">
        <CardContent className="px-0 py-0">
          {loading ? (
            <div className="p-4">
              <OsListSkeleton />
            </div>
          ) : error ? (
            <div className="py-16 text-center text-sm text-destructive">{error}</div>
          ) : !ordens || ordens.length === 0 ? (
            <EmptyState hasQuery={query.length > 0} />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">OS</TableHead>
                  <TableHead>Cliente</TableHead>
                  <TableHead>Aparelho</TableHead>
                  <TableHead>Técnico</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Faturamento</TableHead>
                  <TableHead className="text-right">Data</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ordens.map((os) => (
                  <TableRow key={os.id} className="group">
                    <TableCell className="font-medium text-muted-foreground">
                      #{os.id}
                    </TableCell>
                    <TableCell>
                      <Link
                        href={`/os/${os.id}`}
                        className="block font-medium text-foreground transition-colors group-hover:text-primary focus-visible:underline"
                      >
                        {os.cliente || "—"}
                      </Link>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {os.modelo || os.aparelho || "—"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {os.tecnico || "—"}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={os.status} />
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatCurrency(os.faturamento)}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {formatDate(os.data)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
