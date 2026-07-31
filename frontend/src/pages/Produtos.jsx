import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Plus, Pencil, Trash2, Search, Lock } from "lucide-react";
import { produtos as produtosApi, constantes as constApi } from "@/api/client";
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

// Fallback caso /api/constantes não retorne as listas (rede/erro) — espelha
// `fluxoly_reference_data.py` (PRODUTOS_CATEGORIAS/CONDICOES), mesmo padrão de
// Stock.jsx para tipo/qualidade de estoque. Fonte de verdade real é a API.
const CATEGORIA_OPTIONS_FALLBACK = ["iPhone", "Apple Watch", "AirPods", "Acessorio"];
const CONDICAO_OPTIONS_FALLBACK = ["Novo", "Seminovo", "Vitrine"];

const CATEGORIA_BADGE = {
  "iPhone": { emoji: "🟦", label: "iPhone", className: "bg-blue-500/10 text-blue-300 border-blue-500/30" },
  "Apple Watch": { emoji: "⌚", label: "Apple Watch", className: "bg-zinc-500/10 text-zinc-300 border-zinc-500/30" },
  "AirPods": { emoji: "🎧", label: "AirPods", className: "bg-fuchsia-500/10 text-fuchsia-300 border-fuchsia-500/30" },
  "Acessorio": { emoji: "🔌", label: "Acessório", className: "bg-amber-500/10 text-amber-300 border-amber-500/30" },
};

const EMPTY_FORM = {
  categoria: "iPhone",
  condicao: "Novo",
  marca: "",
  modelo: "",
  cor: "",
  capacidade: "",
  descricao: "",
  sku: "",
  fornecedor: "",
  preco_custo: "",
  preco_venda: "",
  quantidade: "",
  requer_rastreio_unidade: false,
  ativo: true,
};

function nomeProduto(item) {
  if (item.descricao) return item.descricao;
  const partes = [item.marca, item.modelo, item.capacidade, item.cor].filter(Boolean);
  return partes.join(" ") || "Produto sem nome";
}

function categoriaBadge(categoria) {
  return CATEGORIA_BADGE[categoria] || { emoji: "📦", label: categoria || "—", className: "bg-secondary/70 text-muted-foreground border-border" };
}

function statusInfo(item) {
  if (!item.ativo) return { label: "Inativo", className: "bg-zinc-500/10 text-zinc-300 border-zinc-500/30" };
  if ((item.quantidade || 0) <= 0) return { label: "Esgotado", className: "bg-red-500/10 text-red-300 border-red-500/30" };
  return { label: "Disponível", className: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" };
}

function condicaoBadge(condicao) {
  if (condicao === "Seminovo") return "bg-amber-500/10 text-amber-300 border-amber-500/30";
  if (condicao === "Vitrine") return "bg-sky-500/10 text-sky-300 border-sky-500/30";
  return "bg-emerald-500/10 text-emerald-300 border-emerald-500/30";
}

export default function Produtos() {
  const { user } = useAuth();
  const isAdmin = user?.perfil === "admin";

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoriaFilter, setCategoriaFilter] = useState("");
  const [condicaoFilter, setCondicaoFilter] = useState("");
  const [ativoFilter, setAtivoFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [constants, setConstants] = useState(null);

  const fetchItems = async () => {
    setLoading(true);
    try {
      // per_page alto: catálogo ainda pequeno, filtros/busca abaixo são client-side
      // (server só busca em descricao/modelo/sku, não em marca/cor/capacidade).
      const res = await produtosApi.list({ per_page: 500 });
      if (res?.ok) setItems(res.items || []);
      else toast.error(res?.erro || "Erro ao carregar produtos");
    } catch {
      toast.error("Erro ao carregar produtos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  useEffect(() => {
    constApi.get().then((res) => {
      if (res?.ok) setConstants(res);
    });
  }, []);

  const categoriaOptions = constants?.produtos_categorias?.length ? constants.produtos_categorias : CATEGORIA_OPTIONS_FALLBACK;
  const condicaoOptions = constants?.produtos_condicoes?.length ? constants.produtos_condicoes : CONDICAO_OPTIONS_FALLBACK;

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (item) => {
    setForm({
      categoria: item.categoria || "iPhone",
      condicao: item.condicao || "Novo",
      marca: item.marca || "",
      modelo: item.modelo || "",
      cor: item.cor || "",
      capacidade: item.capacidade || "",
      descricao: item.descricao || "",
      sku: item.sku || "",
      fornecedor: item.fornecedor || "",
      preco_custo: item.preco_custo ?? "",
      preco_venda: item.preco_venda ?? "",
      quantidade: item.quantidade ?? "",
      requer_rastreio_unidade: !!item.requer_rastreio_unidade,
      ativo: item.ativo !== false,
    });
    setEditId(item.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        preco_custo: form.preco_custo === "" ? null : parseFloat(form.preco_custo),
        preco_venda: parseFloat(form.preco_venda) || 0,
        quantidade: parseInt(form.quantidade, 10) || 0,
      };
      const res = editId ? await produtosApi.update(editId, payload) : await produtosApi.create(payload);
      if (res?.ok) {
        toast.success(editId ? "Produto atualizado!" : "Produto criado!");
        setDialogOpen(false);
        fetchItems();
      } else {
        toast.error(res?.erro || "Erro ao salvar produto");
      }
    } catch {
      toast.error("Erro ao salvar produto");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const res = await produtosApi.delete(deleteId);
      if (res?.ok) {
        toast.success("Produto excluído");
        setItems((prev) => prev.filter((i) => i.id !== deleteId));
      } else {
        toast.error(res?.erro || "Erro ao excluir produto");
      }
    } catch {
      toast.error("Erro ao excluir produto");
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  const filtered = items.filter((item) => {
    if (categoriaFilter && item.categoria !== categoriaFilter) return false;
    if (condicaoFilter && item.condicao !== condicaoFilter) return false;
    if (ativoFilter === "ativo" && !item.ativo) return false;
    if (ativoFilter === "inativo" && item.ativo) return false;
    const termo = search.trim().toLowerCase();
    if (termo) {
      const haystack = [item.descricao, item.categoria, item.marca, item.modelo, item.cor, item.capacidade, item.sku, item.condicao]
        .filter(Boolean).join(" ").toLowerCase();
      const tokens = termo.split(/\s+/);
      if (!tokens.every((t) => haystack.includes(t))) return false;
    }
    return true;
  });

  const totalProdutos = items.length;
  const totalSeminovos = items.filter((i) => i.condicao === "Seminovo").length;
  const totalVitrine = items.filter((i) => i.condicao === "Vitrine").length;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Produtos</h1>
          <p className="text-muted-foreground text-sm">Catálogo comercial — iPhone, Apple Watch, AirPods e acessórios</p>
        </div>
        {isAdmin ? (
          <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Novo Produto</Button>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted-foreground bg-card border border-border rounded-lg px-3 py-2">
            <Lock className="h-4 w-4" />
            Somente administradores podem alterar o catálogo
          </div>
        )}
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {[
          { label: "Produtos", value: totalProdutos, color: "text-foreground" },
          { label: "Seminovos", value: totalSeminovos, color: "text-amber-400" },
          { label: "Vitrine", value: totalVitrine, color: "text-sky-400" },
        ].map((s) => (
          <div key={s.label} className="bg-card border border-border rounded-xl p-4">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Busca e filtros */}
      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Buscar por modelo, cor, capacidade, marca..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-8" />
        </div>
        <Select value={categoriaFilter || ""} onValueChange={(v) => setCategoriaFilter(v === "all" ? "" : v)}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Categoria" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as categorias</SelectItem>
            {categoriaOptions.map((c) => <SelectItem key={c} value={c}>{categoriaBadge(c).label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={condicaoFilter || ""} onValueChange={(v) => setCondicaoFilter(v === "all" ? "" : v)}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Condição" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as condições</SelectItem>
            {condicaoOptions.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={ativoFilter || ""} onValueChange={(v) => setAtivoFilter(v === "all" ? "" : v)}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os status</SelectItem>
            <SelectItem value="ativo">Ativos</SelectItem>
            <SelectItem value="inativo">Inativos</SelectItem>
          </SelectContent>
        </Select>
        <div className="ml-auto flex items-center text-xs text-muted-foreground">
          {filtered.length} {filtered.length === 1 ? "produto" : "produtos"} exibidos
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          {search || categoriaFilter || condicaoFilter || ativoFilter
            ? "Nenhum produto corresponde à busca/filtros atuais."
            : "Nenhum produto cadastrado ainda."}
        </div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Produto", "Categoria", "Condição", "Venda", "Margem", "Unidades", "Status", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((item) => {
                  const badge = categoriaBadge(item.categoria);
                  const status = statusInfo(item);
                  return (
                    <tr key={item.id} className="hover:bg-accent/30 transition-colors" data-testid={`produto-row-${item.id}`}>
                      <td className="px-4 py-3">
                        <span className="font-medium text-card-foreground">{nomeProduto(item)}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={["inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium", badge.className].join(" ")}>
                          <span>{badge.emoji}</span>{badge.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", condicaoBadge(item.condicao)].join(" ")}>
                          {item.condicao}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-card-foreground font-semibold">{formatCurrency(item.preco_venda)}</td>
                      <td className="px-4 py-3">
                        {item.margem == null ? (
                          <span className="text-muted-foreground">—</span>
                        ) : (
                          <span className={item.margem >= 0 ? "text-emerald-400 font-medium" : "text-red-400 font-medium"}>
                            {formatCurrency(item.margem)}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground italic" title="Rastreamento por unidade/IMEI chega em uma próxima sprint">—</td>
                      <td className="px-4 py-3">
                        <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", status.className].join(" ")}>
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {isAdmin && (
                          <div className="flex items-center gap-1 justify-end">
                            <Button variant="ghost" size="icon" className="h-7 w-7" aria-label={`Editar produto ${item.id}`} onClick={() => openEdit(item)}>
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" aria-label={`Excluir produto ${item.id}`} onClick={() => setDeleteId(item.id)}>
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create/Edit Dialog */}
      {isAdmin && (
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{editId ? "Editar Produto" : "Novo Produto"}</DialogTitle>
              <DialogDescription>
                Preencha os dados do produto para cadastrar ou atualizar no catálogo comercial.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-3 mt-2">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="produto-categoria">Categoria *</Label>
                  <Select value={form.categoria} onValueChange={(v) => setForm((p) => ({ ...p, categoria: v }))}>
                    <SelectTrigger className="w-full" aria-label="Categoria do produto"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {categoriaOptions.map((c) => <SelectItem key={c} value={c}>{categoriaBadge(c).label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-condicao">Condição *</Label>
                  <Select value={form.condicao} onValueChange={(v) => setForm((p) => ({ ...p, condicao: v }))}>
                    <SelectTrigger className="w-full" aria-label="Condição do produto"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {condicaoOptions.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-marca">Marca</Label>
                  <Input id="produto-marca" value={form.marca} onChange={(e) => setForm((p) => ({ ...p, marca: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-modelo">Modelo</Label>
                  <Input id="produto-modelo" value={form.modelo} onChange={(e) => setForm((p) => ({ ...p, modelo: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-cor">Cor</Label>
                  <Input id="produto-cor" value={form.cor} onChange={(e) => setForm((p) => ({ ...p, cor: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-capacidade">Capacidade</Label>
                  <Input id="produto-capacidade" value={form.capacidade} onChange={(e) => setForm((p) => ({ ...p, capacidade: e.target.value }))} />
                </div>
                <div className="col-span-2 space-y-1.5">
                  <Label htmlFor="produto-descricao">Descrição / Nome comercial</Label>
                  <Input id="produto-descricao" value={form.descricao} onChange={(e) => setForm((p) => ({ ...p, descricao: e.target.value }))} placeholder="Ex.: iPhone 15 Pro 256GB Azul Titânio" />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-sku">SKU</Label>
                  <Input id="produto-sku" value={form.sku} onChange={(e) => setForm((p) => ({ ...p, sku: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-fornecedor">Fornecedor</Label>
                  <Input id="produto-fornecedor" value={form.fornecedor} onChange={(e) => setForm((p) => ({ ...p, fornecedor: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-preco-custo">Preço de custo (R$)</Label>
                  <Input id="produto-preco-custo" type="number" step="0.01" min="0" value={form.preco_custo} onChange={(e) => setForm((p) => ({ ...p, preco_custo: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-preco-venda">Preço de venda (R$) *</Label>
                  <Input id="produto-preco-venda" type="number" step="0.01" min="0" value={form.preco_venda} onChange={(e) => setForm((p) => ({ ...p, preco_venda: e.target.value }))} required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="produto-quantidade">Quantidade</Label>
                  <Input id="produto-quantidade" type="number" min="0" value={form.quantidade} onChange={(e) => setForm((p) => ({ ...p, quantidade: e.target.value }))} />
                </div>
                <div className="flex items-center gap-2 pt-6">
                  <input
                    id="produto-ativo"
                    type="checkbox"
                    className="h-4 w-4 rounded border-border"
                    checked={form.ativo}
                    onChange={(e) => setForm((p) => ({ ...p, ativo: e.target.checked }))}
                  />
                  <Label htmlFor="produto-ativo" className="cursor-pointer">Produto ativo (visível no catálogo)</Label>
                </div>
                <div className="col-span-2 flex items-center gap-2">
                  <input
                    id="produto-rastreio"
                    type="checkbox"
                    className="h-4 w-4 rounded border-border"
                    checked={form.requer_rastreio_unidade}
                    onChange={(e) => setForm((p) => ({ ...p, requer_rastreio_unidade: e.target.checked }))}
                  />
                  <Label htmlFor="produto-rastreio" className="cursor-pointer text-muted-foreground">
                    Rastrear por unidade/IMEI (usado em sprint futura)
                  </Label>
                </div>
              </div>
              <DialogFooter className="mt-4">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} disabled={submitting}>Cancelar</Button>
                <Button type="submit" disabled={submitting} data-testid="produtos-save-button">
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {submitting ? "Salvando..." : "Salvar"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      )}

      {isAdmin && (
        <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Excluir Produto?</AlertDialogTitle>
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
