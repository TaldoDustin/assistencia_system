import { useState, useEffect } from "react";
import { toast } from "sonner";
import { CircleNotch, Plus, Pencil, Trash, WarningCircle, MagnifyingGlass, Lock } from "@phosphor-icons/react";
import { estoque as estoqueApi, constantes as constApi } from "@/api/client";
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
import { DataTable } from "@/components/ui/data-table";
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";
import { LooseMetric } from "@/components/ui/loose-metric";
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
  requer_imei: false,
};

// Status de estoque -- vocabulário próprio desta tela (não é o mesmo de OS
// nem de venda), mesmo princípio de getStatusVariant (lib/constants.js):
// cada domínio dono do próprio significado, só a renderização é compartilhada
// (Badge). Ver docs/engineering/plans/PLAN-design-system-fase2.md PR 4.
function estoqueStatusVariant(status) {
  if (status === "disponivel") return "success";
  if (status === "esgotado_ativo") return "error";
  if (status === "esgotado") return "warning";
  if (status === "inativo") return "neutral";
  return "neutral";
}

function reposicaoPrioridadeVariant(prioridade) {
  if (prioridade === "alta") return "error";
  if (prioridade === "media") return "warning";
  return "neutral";
}

export default function Stock() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
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
    if (res?.ok) {
      setItems(res.items || []);
      setLoadError(false);
    } else {
      toast.error("Erro ao carregar estoque");
      setLoadError(true);
    }
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
      requer_imei: !!item.requer_imei,
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

      {loading ? (
        <ListSkeleton rows={6} />
      ) : loadError && items.length === 0 ? (
        <ErrorState title="Não foi possível carregar o estoque." onRetry={fetchItems} />
      ) : (
        <Reveal className="space-y-5">
          {/* Métrica dominante */}
          <Panel>
            <PanelHeader>
              <PanelTitle>Valor Total em estoque</PanelTitle>
            </PanelHeader>
            <PanelContent className="pt-0">
              <p className="text-4xl sm:text-5xl font-bold text-card-foreground tracking-tight">
                {formatCurrency(totalValor)}
              </p>
            </PanelContent>
          </Panel>

          {/* Métricas soltas -- peso secundário, sem moldura */}
          <div className="grid grid-cols-3 gap-x-6 gap-y-4">
            <LooseMetric label="Lotes" value={totalLotes} />
            <LooseMetric label="Unidades" value={totalUnidades} valueClassName="text-info" />
            <LooseMetric label="Críticos (≤2)" value={criticos} valueClassName="text-destructive" />
          </div>

          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <p className="text-sm font-semibold text-card-foreground">Reposição sugerida</p>
                <p className="text-xs text-muted-foreground">Peças com baixo saldo e consumo recente.</p>
              </div>
              <Button variant="outline" size="sm" onClick={fetchReposicao} disabled={loadingReposicao}>
                {loadingReposicao && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
                Atualizar sugestões
              </Button>
            </div>
            {reposicao.length === 0 ? (
              <p className="text-sm text-muted-foreground mt-3">Sem itens para reposição no momento.</p>
            ) : (
              <DataTable
                className="mt-3"
                columns={[
                  { key: "descricao", header: "Peça", className: "text-card-foreground" },
                  { key: "quantidade_atual", header: "Saldo", className: "text-muted-foreground" },
                  { key: "consumo_periodo", header: "Consumo 30d", className: "text-muted-foreground" },
                  { key: "sugestao_reposicao", header: "Sugestão", className: "font-semibold text-success" },
                  {
                    key: "prioridade",
                    header: "Prioridade",
                    render: (item) => <Badge variant={reposicaoPrioridadeVariant(item.prioridade)}>{item.prioridade}</Badge>,
                  },
                ]}
                rows={reposicao.slice(0, 8)}
                getRowKey={(item) => item.id}
              />
            )}
          </div>

          {/* Filters */}
          <FilterBar className="bg-card border border-border rounded-xl p-4">
            <div className="relative flex-1 min-w-[200px]">
              <MagnifyingGlass className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <FilterInput placeholder="Buscar peça..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-8" />
            </div>
            {modeloOptions.length > 0 && (
              <FilterSelect
                value={modeloFilter || "all"}
                onValueChange={(v) => setModeloFilter(v === "all" ? "" : v)}
                placeholder="Modelo"
                className="w-44"
                options={[{ value: "all", label: "Todos os modelos" }, ...modeloOptions.map((m) => ({ value: m, label: m }))]}
              />
            )}
            <FilterSelect
              value={tipoFilter || "all"}
              onValueChange={(v) => setTipoFilter(v === "all" ? "" : v)}
              placeholder="Tipo"
              className="w-44"
              options={[{ value: "all", label: "Todos os tipos" }, ...tipoOptions.map((t) => ({ value: t, label: t }))]}
            />
            <FilterSelect
              value={qualidadeFilter || "all"}
              onValueChange={(v) => setQualidadeFilter(v === "all" ? "" : v)}
              placeholder="Qualidade"
              className="w-44"
              options={[{ value: "all", label: "Todas as qualidades" }, ...qualidadeOptions.map((q) => ({ value: q, label: q }))]}
            />
            <FilterSelect
              value={statusFilter || "all"}
              onValueChange={(v) => setStatusFilter(v === "all" ? "" : v)}
              placeholder="Status de estoque"
              className="w-48"
              options={[
                { value: "all", label: "Todos os status" },
                { value: "disponivel", label: "Disponível" },
                { value: "esgotado_ativo", label: "Esgotado ativo" },
                { value: "esgotado", label: "Esgotado" },
                { value: "inativo", label: "Inativo" },
              ]}
            />
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
          </FilterBar>

          {filtered.length === 0 ? (
            <EmptyState
              title={
                search || modeloFilter || tipoFilter || qualidadeFilter || statusFilter
                  ? "Nenhum item corresponde aos filtros atuais."
                  : (incluirZerados ? "Nenhum item encontrado." : "Nenhum item disponível. Ative \"Incluir zerados\" para visualizar esgotados.")
              }
            />
          ) : (
            <DataTable
              columns={[
                {
                  key: "descricao",
                  header: "Descrição",
                  render: (item) => (
                    <div className="flex items-center gap-2">
                      {(item.quantidade || 0) <= 2 && <WarningCircle className="h-3.5 w-3.5 text-warning shrink-0" />}
                      <span className="font-medium text-card-foreground">{item.descricao}</span>
                    </div>
                  ),
                },
                { key: "modelo", header: "Modelo", className: "text-muted-foreground", render: (item) => item.modelo || "—" },
                { key: "tipo", header: "Tipo", className: "text-muted-foreground", render: (item) => item.tipo || "Outros" },
                { key: "qualidade", header: "Qualidade", className: "text-muted-foreground", render: (item) => item.qualidade || "Padrao" },
                {
                  key: "status_estoque",
                  header: "Status",
                  render: (item) => <Badge variant={estoqueStatusVariant(item.status_estoque)}>{labelStatus(item.status_estoque)}</Badge>,
                },
                {
                  key: "valor",
                  header: "Valor",
                  className: "text-card-foreground font-medium",
                  render: (item) => formatCurrency(item.valor),
                },
                { key: "fornecedor", header: "Fornecedor", className: "text-muted-foreground", render: (item) => item.fornecedor || "—" },
                {
                  key: "quantidade",
                  header: "Qtd",
                  render: (item) => (
                    <span className={`font-bold ${(item.quantidade || 0) <= 2 ? "text-destructive" : "text-success"}`}>
                      {item.quantidade}
                    </span>
                  ),
                },
                {
                  key: "data_compra",
                  header: "Compra",
                  className: "text-muted-foreground whitespace-nowrap",
                  render: (item) => (item.data_compra ? new Date(item.data_compra).toLocaleDateString("pt-BR") : "—"),
                },
                {
                  key: "acoes",
                  header: "",
                  render: (item) => (
                    <div className="flex items-center gap-1 justify-end">
                      {canManage && (
                        <Button variant="ghost" size="icon" className="h-7 w-7" aria-label={`Editar peça ${item.id}`} onClick={() => openEdit(item)}>
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                      )}
                      {canDelete && (
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" aria-label={`Excluir peça ${item.id}`} onClick={() => setDeleteId(item.id)}>
                          <Trash className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                  ),
                },
              ]}
              rows={filtered}
              getRowKey={(item) => item.id}
              getRowProps={(item) => ({ "data-testid": `stock-row-${item.id}` })}
            />
          )}
        </Reveal>
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
                <div className="col-span-2 flex items-center gap-2">
                  <Checkbox
                    id="stock-requer-imei"
                    checked={form.requer_imei}
                    onCheckedChange={(checked) => setForm((p) => ({ ...p, requer_imei: Boolean(checked) }))}
                  />
                  <Label htmlFor="stock-requer-imei" className="cursor-pointer text-muted-foreground">
                    Requer rastreabilidade (IMEI / Nº de série)
                  </Label>
                </div>
              </div>
              <DialogFooter className="mt-4">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} disabled={submitting}>Cancelar</Button>
                <Button type="submit" disabled={submitting} data-testid="stock-save-button">
                  {submitting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
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
