import { useEffect, useState } from "react";
import { shoppingList as shoppingApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { toast } from "sonner";

export default function ShoppingList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: "ALL", prioridade: "ALL", produto: "" });
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [total, setTotal] = useState(0);

  const fetch = async () => {
    setLoading(true);
    try {
      const params = { ...filters, page, per_page: perPage };
      if (params.status === "ALL") delete params.status;
      if (params.prioridade === "ALL") delete params.prioridade;
      const res = await shoppingApi.list(params);
      if (res?.ok) {
        setItems(res.items || []);
        setTotal(res.total || 0);
      } else toast.error("Erro ao carregar lista de compras");
    } catch {
      toast.error("Erro ao carregar lista de compras");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { setPage(1); }, [filters.status, filters.prioridade, filters.produto]);
  useEffect(() => { fetch(); }, [filters, page, perPage]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Lista de Compras</h1>
          <p className="text-sm text-muted-foreground">Gerencie as solicitações de peças</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={filters.status} onValueChange={(v) => setFilters((p) => ({ ...p, status: v }))}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todos</SelectItem>
              <SelectItem value="PENDENTE">Pendente</SelectItem>
              <SelectItem value="EM_COTACAO">Em Cotação</SelectItem>
              <SelectItem value="EM_COMPRA">Em Compra</SelectItem>
              <SelectItem value="COMPRADO">Comprado</SelectItem>
              <SelectItem value="RECEBIDO">Recebido</SelectItem>
              <SelectItem value="CANCELADO">Cancelado</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.prioridade} onValueChange={(v) => setFilters((p) => ({ ...p, prioridade: v }))}>
            <SelectTrigger className="w-32"><SelectValue placeholder="Prioridade" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todas</SelectItem>
              <SelectItem value="URGENTE">URGENTE</SelectItem>
              <SelectItem value="ALTA">ALTA</SelectItem>
              <SelectItem value="NORMAL">NORMAL</SelectItem>
              <SelectItem value="BAIXA">BAIXA</SelectItem>
            </SelectContent>
          </Select>
          <Input placeholder="Pesquisar produto..." onChange={(e) => setFilters((p) => ({ ...p, produto: e.target.value }))} />
          <Button onClick={fetch}>Aplicar</Button>
        </div>
      </div>

      <div className="bg-card rounded-xl border border-border p-4">
        {loading ? (
          <div>Carregando...</div>
        ) : items.length === 0 ? (
          <div className="text-sm text-muted-foreground">Nenhum item encontrado.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-3 py-2">Prioridade</th>
                  <th className="text-left px-3 py-2">Produto</th>
                  <th className="text-left px-3 py-2">Equipamento (OS)</th>
                  <th className="text-left px-3 py-2">Quantidade</th>
                  <th className="text-left px-3 py-2">Status</th>
                  <th className="text-left px-3 py-2">Responsável</th>
                  <th className="text-left px-3 py-2">Data</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {items.map((it) => (
                  <tr key={it.id}>
                    <td className="px-3 py-2">{it.prioridade}</td>
                    <td className="px-3 py-2">{it.produto_nome || it.produto_id || '—'}</td>
                    <td className="px-3 py-2">{it.os_id || '—'}</td>
                    <td className="px-3 py-2">{it.quantidade_solicitada}</td>
                    <td className="px-3 py-2">{it.status}</td>
                    <td className="px-3 py-2">{it.responsavel_nome || '—'}</td>
                    <td className="px-3 py-2">{it.created_at || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="flex items-center justify-between mt-3">
              <div className="text-sm text-muted-foreground">
                Mostrando {(items.length > 0) ? (((page-1)*perPage)+1) : 0} - {Math.min(page*perPage, total)} de {total}
              </div>
              <div className="flex items-center gap-2">
                <Select value={String(perPage)} onValueChange={(v) => { setPerPage(Number(v)); setPage(1); }}>
                  <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="20">20</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                  </SelectContent>
                </Select>
                <Button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p-1))}>Anterior</Button>
                <Button disabled={(page*perPage) >= total} onClick={() => setPage((p) => p+1)}>Próximo</Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
