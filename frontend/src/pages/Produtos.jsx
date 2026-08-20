import { useState, useEffect } from "react";
import { toast } from "sonner";
import { CircleNotch, Plus, Pencil, Trash, MagnifyingGlass, Lock } from "@phosphor-icons/react";
import { produtos as produtosApi, constantes as constApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { ListSkeleton } from "@/components/ui/loading-state";
import { Reveal } from "@/components/ui/reveal";
import { FilterBar, FilterSelect, FilterInput } from "@/components/ui/filter-bar";
import { interactiveRowClassName } from "@/lib/interaction";
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

// CATEGORIA_BADGE — badge categórico (que tipo de produto é este), não de
// status. Migrado para o Badge taxonômico (variant="tag") no PR 5 --
// PLAN-design-system-fase2.md, seção "PR 5 -- Foundation". Cor neutra única,
// sem tom por valor -- perda intencional da diferenciação cromática por
// categoria que existia antes (decisão do CTO).
const CATEGORIA_BADGE = {
  "iPhone": { emoji: "🟦", label: "iPhone" },
  "Apple Watch": { emoji: "⌚", label: "Apple Watch" },
  "AirPods": { emoji: "🎧", label: "AirPods" },
  "Acessorio": { emoji: "🔌", label: "Acessório" },
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
  return CATEGORIA_BADGE[categoria] || { emoji: "📦", label: categoria || "—" };
}

// Disponibilidade -- status genuíno (não categórico), migrado para o Badge
// semântico normalmente.
function statusVariant(item) {
  if (!item.ativo) return "neutral";
  if ((item.quantidade || 0) <= 0) return "error";
  return "success";
}

function statusLabel(item) {
  if (!item.ativo) return "Inativo";
  if ((item.quantidade || 0) <= 0) return "Esgotado";
  return "Disponível";
}

// Condição -- também status genuíno (gradação Novo > Seminovo > Vitrine), as
// 3 cores já usadas (emerald/amber/sky) mapeiam 1:1 nos variants existentes,
// sem precisar de nenhuma cor fora da escala -- diferente do CATEGORIA_BADGE.
function condicaoVariant(condicao) {
  if (condicao === "Seminovo") return "warning";
  if (condicao === "Vitrine") return "info";
  return "success";
}

export default function Produtos() {
  const { user } = useAuth();
  const isAdmin = user?.perfil === "admin";

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
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
      if (res?.ok) {
        setItems(res.items || []);
        setLoadError(false);
      } else {
        toast.error(res?.erro || "Erro ao carregar produtos");
        setLoadError(true);
      }
    } catch {
      toast.error("Erro ao carregar produtos");
      setLoadError(true);
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

      {loading ? (
        <ListSkeleton rows={6} />
      ) : loadError && items.length === 0 ? (
        <ErrorState title="Não foi possível carregar os produtos." onRetry={fetchItems} />
      ) : (
        <Reveal className="space-y-5">
          {/* Cards de resumo */}
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            {[
              { label: "Produtos", value: totalProdutos, color: "text-foreground" },
              { label: "Seminovos", value: totalSeminovos, color: "text-warning" },
              { label: "Vitrine", value: totalVitrine, color: "text-info" },
            ].map((s) => (
              <div key={s.label} className="bg-card border border-border rounded-xl p-4">
                <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>

          {/* Busca e filtros */}
          <FilterBar className="bg-card border border-border rounded-xl p-4">
            <div className="relative flex-1 min-w-[220px]">
              <MagnifyingGlass className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <FilterInput placeholder="Buscar por modelo, cor, capacidade, marca..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-8" />
            </div>
            <FilterSelect
              value={categoriaFilter || "all"}
              onValueChange={(v) => setCategoriaFilter(v === "all" ? "" : v)}
              placeholder="Categoria"
              className="w-44"
              options={[{ value: "all", label: "Todas as categorias" }, ...categoriaOptions.map((c) => ({ value: c, label: categoriaBadge(c).label }))]}
            />
            <FilterSelect
              value={condicaoFilter || "all"}
              onValueChange={(v) => setCondicaoFilter(v === "all" ? "" : v)}
              placeholder="Condição"
              className="w-40"
              options={[{ value: "all", label: "Todas as condições" }, ...condicaoOptions.map((c) => ({ value: c, label: c }))]}
            />
            <FilterSelect
              value={ativoFilter || "all"}
              onValueChange={(v) => setAtivoFilter(v === "all" ? "" : v)}
              placeholder="Status"
              className="w-40"
              options={[
                { value: "all", label: "Todos os status" },
                { value: "ativo", label: "Ativos" },
                { value: "inativo", label: "Inativos" },
              ]}
            />
            <div className="ml-auto flex items-center text-xs text-muted-foreground">
              {filtered.length} {filtered.length === 1 ? "produto" : "produtos"} exibidos
            </div>
          </FilterBar>

          {filtered.length === 0 ? (
            <EmptyState
              title={
                search || categoriaFilter || condicaoFilter || ativoFilter
                  ? "Nenhum produto corresponde à busca/filtros atuais."
                  : "Nenhum produto cadastrado ainda."
              }
            />
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
                      return (
                        <tr key={item.id} className={interactiveRowClassName} data-testid={`produto-row-${item.id}`}>
                          <td className="px-4 py-3">
                            <span className="font-medium text-card-foreground">{nomeProduto(item)}</span>
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant="tag" className="gap-1">
                              <span>{badge.emoji}</span>{badge.label}
                            </Badge>
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant={condicaoVariant(item.condicao)}>{item.condicao}</Badge>
                          </td>
                          <td className="px-4 py-3 text-card-foreground font-semibold">{formatCurrency(item.preco_venda)}</td>
                          <td className="px-4 py-3">
                            {item.margem == null ? (
                              <span className="text-muted-foreground">—</span>
                            ) : (
                              <span className={item.margem >= 0 ? "text-success font-medium" : "text-destructive font-medium"}>
                                {formatCurrency(item.margem)}
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground italic" title="Rastreamento por unidade/IMEI chega em uma próxima sprint">—</td>
                          <td className="px-4 py-3">
                            <Badge variant={statusVariant(item)}>{statusLabel(item)}</Badge>
                          </td>
                          <td className="px-4 py-3">
                            {isAdmin && (
                              <div className="flex items-center gap-1 justify-end">
                                <Button variant="ghost" size="icon" className="h-7 w-7" aria-label={`Editar produto ${item.id}`} onClick={() => openEdit(item)}>
                                  <Pencil className="h-3.5 w-3.5" />
                                </Button>
                                <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" aria-label={`Excluir produto ${item.id}`} onClick={() => setDeleteId(item.id)}>
                                  <Trash className="h-3.5 w-3.5" />
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
        </Reveal>
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
                  <Checkbox
                    id="produto-ativo"
                    checked={form.ativo}
                    onCheckedChange={(checked) => setForm((p) => ({ ...p, ativo: Boolean(checked) }))}
                  />
                  <Label htmlFor="produto-ativo" className="cursor-pointer">Produto ativo (visível no catálogo)</Label>
                </div>
                <div className="col-span-2 flex items-center gap-2">
                  <Checkbox
                    id="produto-rastreio"
                    checked={form.requer_rastreio_unidade}
                    onCheckedChange={(checked) => setForm((p) => ({ ...p, requer_rastreio_unidade: Boolean(checked) }))}
                  />
                  <Label htmlFor="produto-rastreio" className="cursor-pointer text-muted-foreground">
                    Rastrear por unidade/IMEI (usado em sprint futura)
                  </Label>
                </div>
              </div>
              <DialogFooter className="mt-4">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} disabled={submitting}>Cancelar</Button>
                <Button type="submit" disabled={submitting} data-testid="produtos-save-button">
                  {submitting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
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
                {deleting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
                {deleting ? "Excluindo..." : "Excluir"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  );
}
