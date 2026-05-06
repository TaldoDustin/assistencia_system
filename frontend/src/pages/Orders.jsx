import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Plus, Loader2 } from "lucide-react";
import { ordens as ordensApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import OrderFilters from "@/components/orders/OrderFilters";
import OrderTable from "@/components/orders/OrderTable";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";

function extractMeta(ordens) {
  const tecnicos = [...new Set(ordens.map((o) => o.tecnico).filter(Boolean))];
  const vendedores = [...new Set(ordens.map((o) => o.vendedor).filter(Boolean))];
  return { tecnicos, vendedores };
}

function applyFilters(ordens, filters) {
  return ordens.filter((o) => {
    if (filters.search) {
      const q = filters.search.toLowerCase();
      if (
        !o.cliente?.toLowerCase().includes(q) &&
        !o.modelo?.toLowerCase().includes(q) &&
        !o.imei?.includes(q)
      ) return false;
    }
    if (filters.status && o.status !== filters.status) return false;
    if (filters.tipo && o.tipo !== filters.tipo) return false;
    if (filters.tecnico && o.tecnico !== filters.tecnico) return false;
    if (filters.vendedor && o.vendedor !== filters.vendedor) return false;
    return true;
  });
}

export default function Orders() {
  const [ordens, setOrdens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [deleteId, setDeleteId] = useState(null);

  const fetchOrdens = async (opts = {}) => {
    const { silent = false } = opts;
    if (!silent) setLoading(true);
    try {
      const res = await ordensApi.list();
      if (res?.ok) setOrdens(res.ordens || []);
      else if (!silent) toast.error("Erro ao carregar ordens");
    } catch {
      if (!silent) toast.error("Erro ao carregar ordens");
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => { 
    fetchOrdens();
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(() => fetchOrdens({ silent: true }), 30000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      const res = await ordensApi.delete(deleteId);
      if (res?.ok) {
        toast.success("Ordem excluída");
        setOrdens((prev) => prev.filter((o) => o.id !== deleteId));
      } else {
        toast.error(res?.erro || "Erro ao excluir ordem");
      }
    } catch {
      toast.error("Erro ao excluir ordem");
    } finally {
      setDeleteId(null);
    }
  };

  const filtered = applyFilters(ordens, filters);
  const { tecnicos, vendedores } = extractMeta(ordens);
  const abertas = ordens.filter((o) => o.status === "Em andamento" || o.status === "Aguardando peca").length;
  const finalizadas = ordens.filter((o) => o.status === "Finalizado").length;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Ordens de Serviço</h1>
          <p className="text-muted-foreground text-sm">Gerencie as ordens de serviço</p>
        </div>
        <Link to="/ordens/nova">
          <Button><Plus className="h-4 w-4 mr-2" />Nova OS</Button>
        </Link>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Total", value: ordens.length, color: "text-foreground" },
          { label: "Em aberto", value: abertas, color: "text-amber-400" },
          { label: "Finalizadas", value: finalizadas, color: "text-emerald-400" },
        ].map((s) => (
          <div key={s.label} className="bg-card border border-border rounded-xl p-4 text-center">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      <OrderFilters filters={filters} setFilters={setFilters} tecnicos={tecnicos} vendedores={vendedores} />

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : (
        <OrderTable orders={filtered} onDelete={setDeleteId} />
      )}

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir Ordem?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. A ordem e todas suas informações serão removidas permanentemente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
