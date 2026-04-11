import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Plus, Pencil, Trash2, Lock } from "lucide-react";
import { constantes, custos as custosApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { formatCurrency } from "@/lib/constants";

const EMPTY_FORM = {
  descricao: "",
  valor: "",
  categoria: "Outros",
  data: new Date().toISOString().split("T")[0],
  observacoes: "",
};

function groupByCategory(custos) {
  return custos.reduce((acc, c) => {
    const cat = c.categoria || "Outros";
    acc[cat] = (acc[cat] || 0) + (c.valor || 0);
    return acc;
  }, {});
}

export default function OperationalCosts() {
  const { user } = useAuth();
  const [custos, setCustos] = useState([]);
  const [categorias, setCategorias] = useState(["Outros"]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  const isAdmin = user?.perfil === "admin";

  const fetchCustos = () => {
    Promise.all([custosApi.list(), constantes.get()]).then(([custosRes, constantesRes]) => {
      if (custosRes?.ok) setCustos(custosRes.custos || []);
      else toast.error("Erro ao carregar custos");

      if (constantesRes?.ok && constantesRes.categorias_custos?.length) {
        setCategorias(constantesRes.categorias_custos);
      }

      setLoading(false);
    });
  };

  useEffect(() => { fetchCustos(); }, []);

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Lock className="h-10 w-10" />
        <p>Somente administradores podem gerenciar custos operacionais.</p>
      </div>
    );
  }

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (c) => {
    setForm({
      descricao: c.descricao || "",
      valor: c.valor || "",
      categoria: c.categoria || "Outros",
      data: c.data ? c.data.split("T")[0] : new Date().toISOString().split("T")[0],
      observacoes: c.observacoes || "",
    });
    setEditId(c.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = { ...form, valor: parseFloat(form.valor) || 0 };
      const res = editId ? await custosApi.update(editId, payload) : await custosApi.create(payload);
      if (res?.ok) {
        toast.success(editId ? "Custo atualizado!" : "Custo criado!");
        setDialogOpen(false);
        fetchCustos();
      } else toast.error(res?.erro || "Erro ao salvar");
    } catch { toast.error("Erro ao salvar custo"); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async () => {
    try {
      const res = await custosApi.delete(deleteId);
      if (res?.ok) {
        toast.success("Custo excluído");
        setCustos((prev) => prev.filter((c) => c.id !== deleteId));
      } else toast.error(res?.erro || "Erro ao excluir");
    } catch { toast.error("Erro ao excluir"); }
    finally { setDeleteId(null); }
  };

  const total = custos.reduce((acc, c) => acc + (c.valor || 0), 0);
  const thisMonth = (() => {
    const now = new Date();
    return custos
      .filter((c) => { const d = new Date(c.data); return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear(); })
      .reduce((acc, c) => acc + (c.valor || 0), 0);
  })();
  const byCategory = groupByCategory(custos);
  const sorted = [...custos].sort((a, b) => new Date(b.data) - new Date(a.data));

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Custos Operacionais</h1>
          <p className="text-muted-foreground text-sm">Controle despesas do negócio</p>
        </div>
        <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Novo Custo</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-2xl font-bold text-red-400">{formatCurrency(total)}</p>
          <p className="text-xs text-muted-foreground mt-0.5">Total</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <p className="text-2xl font-bold text-amber-400">{formatCurrency(thisMonth)}</p>
          <p className="text-xs text-muted-foreground mt-0.5">Este mês</p>
        </div>
        <div className="col-span-2 lg:col-span-1 bg-card border border-border rounded-xl p-4">
          <p className="text-xs font-medium text-muted-foreground mb-2">Por Categoria</p>
          <div className="space-y-1">
            {Object.entries(byCategory).slice(0, 4).map(([cat, val]) => (
              <div key={cat} className="flex justify-between text-xs">
                <span className="text-muted-foreground">{cat}</span>
                <span className="text-card-foreground font-medium">{formatCurrency(val)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
      ) : sorted.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">Nenhum custo cadastrado.</div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Descrição", "Categoria", "Valor", "Data", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {sorted.map((c) => (
                  <tr key={c.id} className="hover:bg-accent/30 transition-colors">
                    <td className="px-4 py-3 font-medium text-card-foreground">{c.descricao}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs bg-secondary text-secondary-foreground rounded px-2 py-0.5">{c.categoria}</span>
                    </td>
                    <td className="px-4 py-3 text-red-400 font-medium">{formatCurrency(c.valor)}</td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                      {c.data ? new Date(c.data).toLocaleDateString("pt-BR") : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(c)}>
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" onClick={() => setDeleteId(c.id)}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editId ? "Editar Custo" : "Novo Custo"}</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label>Descrição *</Label>
              <Input value={form.descricao} onChange={(e) => setForm((p) => ({ ...p, descricao: e.target.value }))} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Categoria</Label>
                <Select value={form.categoria} onValueChange={(v) => setForm((p) => ({ ...p, categoria: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{categorias.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Valor (R$) *</Label>
                <Input type="number" step="0.01" min="0" value={form.valor} onChange={(e) => setForm((p) => ({ ...p, valor: e.target.value }))} required />
              </div>
              <div className="space-y-1.5">
                <Label>Data</Label>
                <Input type="date" value={form.data} onChange={(e) => setForm((p) => ({ ...p, data: e.target.value }))} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Observações</Label>
              <Textarea value={form.observacoes} onChange={(e) => setForm((p) => ({ ...p, observacoes: e.target.value }))} />
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={submitting}>{submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Salvar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir Custo?</AlertDialogTitle>
            <AlertDialogDescription>Esta ação não pode ser desfeita.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">Excluir</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
