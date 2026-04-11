import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Plus, Pencil, Trash2, Lock } from "lucide-react";
import { usuarios as usuariosApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";

const PERFIS = ["admin", "tecnico", "vendedor"];

const EMPTY_FORM = { nome: "", usuario: "", senha: "", perfil: "tecnico", ativo: true };

export default function Users() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  const isAdmin = currentUser?.perfil === "admin";

  const fetchUsers = () => {
    usuariosApi.list().then((res) => {
      if (res?.ok) setUsers(res.usuarios || []);
      else toast.error("Erro ao carregar usuários");
      setLoading(false);
    });
  };

  useEffect(() => { fetchUsers(); }, []);

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Lock className="h-10 w-10" />
        <p>Somente administradores podem gerenciar usuários.</p>
      </div>
    );
  }

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (u) => {
    setForm({ nome: u.nome || "", usuario: u.usuario || "", senha: "", perfil: u.perfil || "tecnico", ativo: u.ativo !== false });
    setEditId(u.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = { ...form };
      if (editId && !payload.senha) delete payload.senha;
      const res = editId ? await usuariosApi.update(editId, payload) : await usuariosApi.create(payload);
      if (res?.ok) {
        toast.success(editId ? "Usuário atualizado!" : "Usuário criado!");
        setDialogOpen(false);
        fetchUsers();
      } else toast.error(res?.erro || "Erro ao salvar usuário");
    } catch { toast.error("Erro ao salvar usuário"); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async () => {
    try {
      const res = await usuariosApi.delete(deleteId);
      if (res?.ok) {
        toast.success("Usuário excluído");
        setUsers((prev) => prev.filter((u) => u.id !== deleteId));
      } else toast.error(res?.erro || "Erro ao excluir");
    } catch { toast.error("Erro ao excluir usuário"); }
    finally { setDeleteId(null); }
  };

  const perfilColor = { admin: "text-primary", tecnico: "text-blue-400", vendedor: "text-emerald-400" };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Usuários</h1>
          <p className="text-muted-foreground text-sm">Gerencie o acesso ao sistema</p>
        </div>
        <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Novo Usuário</Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
      ) : users.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">Nenhum usuário encontrado.</div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Nome", "Usuário", "Perfil", "Status", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-accent/30 transition-colors">
                    <td className="px-4 py-3 font-medium text-card-foreground">{u.nome}</td>
                    <td className="px-4 py-3 font-mono text-sm text-muted-foreground">{u.usuario}</td>
                    <td className="px-4 py-3">
                      <span className={`text-sm font-medium capitalize ${perfilColor[u.perfil] || "text-muted-foreground"}`}>{u.perfil}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${u.ativo !== false ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : "bg-red-500/20 text-red-400 border-red-500/30"}`}>
                        {u.ativo !== false ? "Ativo" : "Inativo"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(u)}>
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        {u.id !== currentUser?.id && (
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" onClick={() => setDeleteId(u.id)}>
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
          <DialogHeader><DialogTitle>{editId ? "Editar Usuário" : "Novo Usuário"}</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label>Nome *</Label>
              <Input value={form.nome} onChange={(e) => setForm((p) => ({ ...p, nome: e.target.value }))} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Usuário *</Label>
                <Input value={form.usuario} onChange={(e) => setForm((p) => ({ ...p, usuario: e.target.value }))} required />
              </div>
              <div className="space-y-1.5">
                <Label>{editId ? "Nova Senha" : "Senha *"}</Label>
                <Input
                  type="password"
                  value={form.senha}
                  onChange={(e) => setForm((p) => ({ ...p, senha: e.target.value }))}
                  required={!editId}
                  placeholder={editId ? "Deixe vazio para manter" : ""}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Perfil</Label>
                <Select value={form.perfil} onValueChange={(v) => setForm((p) => ({ ...p, perfil: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{PERFIS.map((p) => <SelectItem key={p} value={p} className="capitalize">{p}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 mt-6">
                <Checkbox
                  checked={form.ativo}
                  onCheckedChange={(checked) => setForm((p) => ({ ...p, ativo: !!checked }))}
                />
                <Label>Ativo</Label>
              </div>
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
            <AlertDialogTitle>Excluir Usuário?</AlertDialogTitle>
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
