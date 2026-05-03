import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Plus, Pencil, Trash2, AlertTriangle, Search, Lock } from "lucide-react";
import { estoque as estoqueApi, constantes as constApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { formatCurrency } from "@/lib/constants";

const EMPTY_FORM = {
  descricao: "",
  modelo: "",
  tipo: "Outros",
  qualidade: "Padrao",
  valor: "",
  fornecedor: "",
  quantidade: "",
  data_compra: "",
};

export default function Stock() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modeloFilter, setModeloFilter] = useState("");
  const [tipoFilter, setTipoFilter] = useState("");
  const [qualidadeFilter, setQualidadeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [incluirZerados, setIncluirZerados] = useState(false);
  const [reposicao, setReposicao] = useState([]);
  const [loadingReposicao, setLoadingReposicao] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [constants, setConstants] = useState(null);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const canManage = user?.perfil === "admin" || user?.perfil === "tecnico";
  const canDelete = user?.perfil === "admin";

  const fetchItems = async () => {
    const params = { include_zerados: incluirZerados ? "1" : "0" };
    if (statusFilter) params.status = statusFilter;
    const res = await estoqueApi.list(params);
    if (res?.ok) setItems(res.items || []);
    else toast.error("Erro ao carregar estoque");
    setLoading(false);
  };

  const fetchReposicao = async () => {
    setLoadingReposicao(true);
    try {
      const res = await estoqueApi.reposicaoSugestao({ dias: 30 });
      if (res?.ok) {
        setReposicao(res.itens || []);
      } else {
        toast.error(res?.erro || "Erro ao carregar reposição sugerida");
      }
    } catch {
      toast.error("Erro ao carregar reposição sugerida");
    } finally {
      setLoadingReposicao(false);
    }
  };

  useEffect(() => {
    fetchItems();
    fetchReposicao();
  }, [incluirZerados, statusFilter]);

  useEffect(() => {
    constApi.get().then((res) => {
      if (res?.ok) setConstants(res);
    });
  }, []);

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (item) => {
    setForm({
      descricao: item.descricao || "",
      modelo: item.modelo || "",
      tipo: item.tipo || "Outros",
      qualidade: item.qualidade || "Padrao",
      valor: item.valor || "",
      fornecedor: item.fornecedor || "",
      quantidade: item.quantidade || "",
      data_compra: item.data_compra ? item.data_compra.split("T")[0] : "",
    });
    setEditId(item.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = { ...form, valor: parseFloat(form.valor) || 0, quantidade: parseInt(form.quantidade) || 0 };
      const res = editId ? await estoqueApi.update(editId, payload) : await estoqueApi.create(payload);
      if (res?.ok) {
        toast.success(editId ? "Item atualizado!" : "Item criado!");
        setDialogOpen(false);
        fetchItems();
      } else {
        toast.error(res?.erro || "Erro ao salvar");
      }
    } catch {
      toast.error("Erro ao salvar item");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const res = await estoqueApi.delete(deleteId);
      if (res?.ok) {
        toast.success("Item excluído");
        setItems((prev) => prev.filter((i) => i.id !== deleteId));
      } else {
        toast.error(res?.erro || "Erro ao excluir");
      }
    } catch {
      toast.error("Erro ao excluir");
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  const modelos = [...new Set([...(constants?.iphone_models || []), ...items.map((i) => i.modelo).filter(Boolean)])];
  const modeloOptions = [...new Set(["Universal", ...modelos])];
  const tipoOptions = constants?.estoque_tipos || ["Tela", "Bateria", "Conector", "Camera", "Placa", "Carcaca", "Alto-falante", "Outros"];
  const qualidadeOptions = constants?.estoque_qualidades || ["Original", "Premium", "Paralelo", "Refurbished", "Padrao"];
  const normalizedFilter = modeloFilter?.toLowerCase().trim();
  const filtered = items.filter((item) => {
    const itemModelo = item.modelo?.toLowerCase().trim() || "";
    const itemTipo = item.tipo || "Outros";
    const itemQualidade = item.qualidade || "Padrao";
    if (search && !(`${item.descricao || ""} ${itemModelo}`.toLowerCase().includes(search.toLowerCase()))) return false;
    if (normalizedFilter && itemModelo !== normalizedFilter && itemModelo !== "universal") return false;
    if (tipoFilter && itemTipo !== tipoFilter) return false;
    if (qualidadeFilter && itemQualidade !== qualidadeFilter) return false;
    return true;
  });

  const labelStatus = (status) => {
    if (status === "disponivel") return "Disponível";
    if (status === "esgotado_ativo") return "Esgotado ativo";
    if (status === "inativo") return "Inativo";
    if (status === "esgotado") return "Esgotado";
    return "—";
  };

  const classesStatus = (status) => {
    if (status === "disponivel") return "bg-emerald-500/10 text-emerald-300 border-emerald-500/30";
    if (status === "esgotado_ativo") return "bg-red-500/10 text-red-300 border-red-500/30";
    if (status === "inativo") return "bg-zinc-500/10 text-zinc-300 border-zinc-500/30";
    if (status === "esgotado") return "bg-amber-500/10 text-amber-300 border-amber-500/30";
    return "bg-secondary/70 text-muted-foreground border-border";
  };

  const totalLotes = items.length;
  const totalUnidades = items.reduce((acc, i) => acc + (i.quantidade || 0), 0);
  const totalValor = items.reduce((acc, i) => acc + (i.valor || 0) * (i.quantidade || 0), 0);
  const criticos = items.filter((i) => (i.quantidade || 0) <= 2).length;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Estoque</h1>
          <p className="text-muted-foreground text-sm">Gerencie peças e insumos</p>
        </div>
        {canManage ? (
          <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Nova Peça</Button>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted-foreground bg-card border border-border rounded-lg px-3 py-2">
            <Lock className="h-4 w-4" />
            Somente técnicos e administradores podem alterar o estoque
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: "Lotes", value: totalLotes, color: "text-foreground" },
          { label: "Unidades", value: totalUnidades, color: "text-blue-400" },
          { label: "Valor Total", value: formatCurrency(totalValor), color: "text-emerald-400" },
          { label: "Críticos (≤2)", value: criticos, color: "text-red-400" },
        ].map((s) => (
          <div key={s.label} className="bg-card border border-border rounded-xl p-4">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <p className="text-sm font-semibold text-card-foreground">Reposição sugerida</p>
            <p className="text-xs text-muted-foreground">Peças com baixo saldo e consumo recente.</p>
          </div>
          <Button variant="outline" size="sm" onClick={fetchReposicao} disabled={loadingReposicao}>
            {loadingReposicao && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Atualizar sugestões
          </Button>
        </div>
        {reposicao.length === 0 ? (
          <p className="text-sm text-muted-foreground mt-3">Sem itens para reposição no momento.</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  { ["Peça", "Saldo", "Consumo 30d", "Sugestão", "Prioridade"].map((h) => (
                    <th key={h} className="text-left px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {reposicao.slice(0, 8).map((item) => (
                  <tr key={item.id}>
                    {/* SKU removido */}
                    <td className="px-3 py-2 text-card-foreground">{item.descricao}</td>
                    <td className="px-3 py-2 text-muted-foreground">{item.quantidade_atual}</td>
                    <td className="px-3 py-2 text-muted-foreground">{item.consumo_periodo}</td>
                    <td className="px-3 py-2 font-semibold text-emerald-300">{item.sugestao_reposicao}</td>
                    <td className="px-3 py-2">
                      <span className={[
                        "inline-flex rounded-full border px-2 py-0.5 text-xs font-medium",
                        item.prioridade === "alta"
                          ? "bg-red-500/10 text-red-300 border-red-500/30"
                          : item.prioridade === "media"
                            ? "bg-amber-500/10 text-amber-300 border-amber-500/30"
                            : "bg-zinc-500/10 text-zinc-300 border-zinc-500/30",
                      ].join(" ")}>
                        {item.prioridade}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Buscar peça..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-8" />
        </div>
        {modeloOptions.length > 0 && (
          <Select value={modeloFilter || ""} onValueChange={(v) => setModeloFilter(v === "all" ? "" : v)}>
            <SelectTrigger className="w-44"><SelectValue placeholder="Modelo" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os modelos</SelectItem>
              {modeloOptions.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
        )}
        <Select value={tipoFilter || ""} onValueChange={(v) => setTipoFilter(v === "all" ? "" : v)}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Tipo" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os tipos</SelectItem>
            {tipoOptions.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={qualidadeFilter || ""} onValueChange={(v) => setQualidadeFilter(v === "all" ? "" : v)}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Qualidade" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as qualidades</SelectItem>
            {qualidadeOptions.map((q) => <SelectItem key={q} value={q}>{q}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={statusFilter || ""} onValueChange={(v) => setStatusFilter(v === "all" ? "" : v)}>
          <SelectTrigger className="w-48"><SelectValue placeholder="Status de estoque" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os status</SelectItem>
            <SelectItem value="disponivel">Disponível</SelectItem>
            <SelectItem value="esgotado_ativo">Esgotado ativo</SelectItem>
            <SelectItem value="esgotado">Esgotado</SelectItem>
            <SelectItem value="inativo">Inativo</SelectItem>
          </SelectContent>
        </Select>
        <Button
          type="button"
          variant={incluirZerados ? "default" : "outline"}
          onClick={() => setIncluirZerados((v) => !v)}
          className="whitespace-nowrap"
        >
          {incluirZerados ? "Ocultar zerados" : "Incluir zerados"}
        </Button>
        <div className="ml-auto flex items-center text-xs text-muted-foreground">
          {filtered.length} {filtered.length === 1 ? "item" : "itens"} exibidos
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          {search || modeloFilter || tipoFilter || qualidadeFilter || statusFilter
            ? "Nenhum item corresponde aos filtros atuais."
            : (incluirZerados ? "Nenhum item encontrado." : "Nenhum item disponível. Ative \"Incluir zerados\" para visualizar esgotados.")}
        </div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  { ["Descrição", "Modelo", "Tipo", "Qualidade", "Status", "Valor", "Fornecedor", "Qtd", "Compra", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-accent/30 transition-colors" data-testid={`stock-row-${item.id}`}>
                    {/* SKU removido */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {(item.quantidade || 0) <= 2 && <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />}
                        <span className="font-medium text-card-foreground">{item.descricao}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{item.modelo || "—"}</td>
                    <td className="px-4 py-3 text-muted-foreground">{item.tipo || "Outros"}</td>
                    <td className="px-4 py-3 text-muted-foreground">{item.qualidade || "Padrao"}</td>
                    <td className="px-4 py-3">
                      <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", classesStatus(item.status_estoque)].join(" ")}>
                        {labelStatus(item.status_estoque)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-card-foreground font-medium">{formatCurrency(item.valor)}</td>
                    <td className="px-4 py-3 text-muted-foreground">{item.fornecedor || "—"}</td>
                    <td className="px-4 py-3">
                      <span className={`font-bold ${(item.quantidade || 0) <= 2 ? "text-red-400" : "text-emerald-400"}`}>
                        {item.quantidade}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                      {item.data_compra ? new Date(item.data_compra).toLocaleDateString("pt-BR") : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        {canManage && (
                          <Button variant="ghost" size="icon" className="h-7 w-7" aria-label={`Editar peça ${item.id}`} onClick={() => openEdit(item)}>
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        {canDelete && (
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" aria-label={`Excluir peça ${item.id}`} onClick={() => setDeleteId(item.id)}>
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

      {/* Create/Edit Dialog */}
      {canManage && (
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editId ? "Editar Peça" : "Nova Peça"}</DialogTitle>
              <DialogDescription>
                Preencha os dados da peça para cadastrar ou atualizar no estoque.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-3 mt-2">
              {/* Campo SKU removido */}
              <div className="space-y-1.5">
                <Label htmlFor="stock-descricao">Descrição *</Label>
                <Input id="stock-descricao" value={form.descricao} onChange={(e) => setForm((p) => ({ ...p, descricao: e.target.value }))} required />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="stock-modelo">Modelo compatível</Label>
                  <Select value={form.modelo} onValueChange={(v) => setForm((p) => ({ ...p, modelo: v }))}>
                    <SelectTrigger className="w-full" aria-label="Modelo compatível"><SelectValue placeholder="Selecione um modelo" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Universal">Universal (serve para qualquer modelo)</SelectItem>
                      {modeloOptions.map((m) => m && <SelectItem key={m} value={m}>{m}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="stock-tipo">Tipo *</Label>
                  <Select value={form.tipo} onValueChange={(v) => setForm((p) => ({ ...p, tipo: v }))}>
                    <SelectTrigger className="w-full" aria-label="Tipo da peça"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {tipoOptions.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="stock-qualidade">Qualidade *</Label>
                  <Select value={form.qualidade} onValueChange={(v) => setForm((p) => ({ ...p, qualidade: v }))}>
                    <SelectTrigger className="w-full" aria-label="Qualidade da peça"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {qualidadeOptions.map((q) => <SelectItem key={q} value={q}>{q}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="stock-fornecedor">Fornecedor</Label>
                  <Input id="stock-fornecedor" value={form.fornecedor} onChange={(e) => setForm((p) => ({ ...p, fornecedor: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="stock-valor">Valor (R$)</Label>
                  <Input id="stock-valor" type="number" step="0.01" min="0" value={form.valor} onChange={(e) => setForm((p) => ({ ...p, valor: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="stock-quantidade">Quantidade</Label>
                  <Input id="stock-quantidade" type="number" min="0" value={form.quantidade} onChange={(e) => setForm((p) => ({ ...p, quantidade: e.target.value }))} />
                </div>
                <div className="col-span-2 space-y-1.5">
                  <Label htmlFor="stock-data-compra">Data de Compra</Label>
                  <Input id="stock-data-compra" type="date" value={form.data_compra} onChange={(e) => setForm((p) => ({ ...p, data_compra: e.target.value }))} />
                </div>
              </div>
              <DialogFooter className="mt-4">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} disabled={submitting}>Cancelar</Button>
                <Button type="submit" disabled={submitting} data-testid="stock-save-button">
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {submitting ? "Salvando..." : "Salvar"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      )}

      {canDelete && (
        <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Excluir Item?</AlertDialogTitle>
              <AlertDialogDescription>Esta ação não pode ser desfeita.</AlertDialogDescription>
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
      )}
    </div>
  );
}
