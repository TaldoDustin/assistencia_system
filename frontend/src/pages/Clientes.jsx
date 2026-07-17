import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { Loader2, Plus, Pencil, Trash2, Search } from "lucide-react";
import { clientes as clientesApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";

const EMPTY_FORM = { nome: "", telefone: "", email: "", cpf_cnpj: "", observacoes: "" };

export default function Clientes() {
  const { user } = useAuth();
  const isAdmin = user?.perfil === "admin";

  const [clientes, setClientes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchClientes = useCallback((termo = busca) => {
    setLoading(true);
    clientesApi.list({ q: termo }).then((res) => {
      if (res?.ok) {
        setClientes(res.items || []);
        setTotal(res.total || 0);
      } else toast.error("Erro ao carregar clientes");
      setLoading(false);
    });
  }, [busca]);

  useEffect(() => { fetchClientes(""); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleBuscar = (e) => {
    e.preventDefault();
    fetchClientes(busca);
  };

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (c) => {
    setForm({
      nome: c.nome || "",
      telefone: c.telefone || "",
      email: c.email || "",
      cpf_cnpj: c.cpf_cnpj || "",
      observacoes: c.observacoes || "",
    });
    setEditId(c.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = editId ? await clientesApi.update(editId, form) : await clientesApi.create(form);
      if (res?.ok) {
        toast.success(editId ? "Cliente atualizado!" : "Cliente criado!");
        setDialogOpen(false);
        fetchClientes(busca);
      } else toast.error(res?.erro || "Erro ao salvar cliente");
    } catch { toast.error("Erro ao salvar cliente"); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const res = await clientesApi.delete(deleteId);
      if (res?.ok) {
        toast.success("Cliente excluído");
        setClientes((prev) => prev.filter((c) => c.id !== deleteId));
        setTotal((prev) => Math.max(0, prev - 1));
      } else toast.error(res?.erro || "Erro ao excluir cliente");
    } catch { toast.error("Erro ao excluir cliente"); }
    finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Clientes</h1>
          <p className="text-muted-foreground text-sm">{total} {total === 1 ? "cliente cadastrado" : "clientes cadastrados"}</p>
        </div>
        <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Novo Cliente</Button>
      </div>

      <form onSubmit={handleBuscar} className="flex items-center gap-2 max-w-md">
        <Input
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por nome, telefone ou e-mail..."
        />
        <Button type="submit" variant="outline" size="icon" aria-label="Buscar">
          <Search className="h-4 w-4" />
        </Button>
      </form>

      {loading ? (
        <div className="flex items-center justify-center h-40"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
      ) : clientes.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">Nenhum cliente encontrado.</div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Nome", "Telefone", "E-mail", "CPF/CNPJ", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {clientes.map((c) => (
                  <tr key={c.id} className="hover:bg-accent/30 transition-colors" data-testid={`cliente-row-${c.id}`}>
                    <td className="px-4 py-3 font-medium text-card-foreground">{c.nome}</td>
                    <td className="px-4 py-3 text-muted-foreground">{c.telefone || "—"}</td>
                    <td className="px-4 py-3 text-muted-foreground">{c.email || "—"}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{c.cpf_cnpj || "—"}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        <Button variant="ghost" size="icon" className="h-7 w-7" aria-label={`Editar cliente ${c.id}`} onClick={() => openEdit(c)}>
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        {isAdmin && (
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" aria-label={`Excluir cliente ${c.id}`} onClick={() => setDeleteId(c.id)}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        )}
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
          <DialogHeader><DialogTitle>{editId ? "Editar Cliente" : "Novo Cliente"}</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label htmlFor="cliente-nome">Nome *</Label>
              <Input id="cliente-nome" value={form.nome} onChange={(e) => setForm((p) => ({ ...p, nome: e.target.value }))} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="cliente-telefone">Telefone</Label>
                <Input id="cliente-telefone" value={form.telefone} onChange={(e) => setForm((p) => ({ ...p, telefone: e.target.value }))} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="cliente-email">E-mail</Label>
                <Input id="cliente-email" type="email" value={form.email} onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))} />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">Informe ao menos um contato (telefone ou e-mail).</p>
            <div className="space-y-1.5">
              <Label htmlFor="cliente-documento">CPF/CNPJ</Label>
              <Input id="cliente-documento" value={form.cpf_cnpj} onChange={(e) => setForm((p) => ({ ...p, cpf_cnpj: e.target.value }))} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cliente-observacoes">Observações</Label>
              <Textarea id="cliente-observacoes" value={form.observacoes} onChange={(e) => setForm((p) => ({ ...p, observacoes: e.target.value }))} rows={3} />
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} disabled={submitting}>Cancelar</Button>
              <Button type="submit" disabled={submitting} data-testid="clientes-save-button">
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {submitting ? "Salvando..." : "Salvar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir Cliente?</AlertDialogTitle>
            <AlertDialogDescription>Esta ação não pode ser desfeita. Clientes com OS vinculada não podem ser excluídos.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} disabled={deleting} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              {deleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {deleting ? "Excluindo..." : "Excluir"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
