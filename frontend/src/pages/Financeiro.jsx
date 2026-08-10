import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  Loader2, Lock, Plus, RotateCcw, CheckCircle2, XCircle, Pencil, Trash2,
  ChevronLeft, ChevronRight, Wallet, ArrowDownCircle, ArrowUpCircle,
} from "lucide-react";
import { caixa as caixaApi, contasPagar as contasPagarApi, contasReceber as contasReceberApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { formatCurrency } from "@/lib/constants";

const PER_PAGE = 20;

const TIPO_BADGE = {
  entrada: { label: "Entrada", className: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
  saida: { label: "Saída", className: "bg-red-500/10 text-red-300 border-red-500/30" },
};

const ORIGEM_LABEL = {
  manual: "Manual",
  venda: "Venda",
  conta_pagar: "Conta a Pagar",
  conta_receber: "Conta a Receber",
};

const STATUS_CONTA_BADGE = {
  pendente: { label: "Pendente", className: "bg-amber-500/10 text-amber-300 border-amber-500/30" },
  pago: { label: "Pago", className: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
  recebido: { label: "Recebido", className: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
  cancelado: { label: "Cancelado", className: "bg-secondary/70 text-muted-foreground border-border" },
};

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  const horaCurta = (hora || "").slice(0, 5);
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${horaCurta}`.trim() : value;
}

function formatData(value) {
  if (!value) return "—";
  const [ano, mes, dia] = value.split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : value;
}

const EMPTY_MOVIMENTACAO = { tipo: "entrada", valor: "", descricao: "" };

function Movimentacoes({ onMutate }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  const [tipoFilter, setTipoFilter] = useState("");
  const [origemFilter, setOrigemFilter] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_MOVIMENTACAO);
  const [submitting, setSubmitting] = useState(false);
  const [estornarId, setEstornarId] = useState(null);
  const [estornando, setEstornando] = useState(false);

  const buscar = useCallback(() => {
    setLoading(true);
    setErro(false);
    const params = { page, per_page: PER_PAGE };
    if (tipoFilter) params.tipo = tipoFilter;
    if (origemFilter) params.origem = origemFilter;
    if (dataInicio) params.data_inicio = dataInicio;
    if (dataFim) params.data_fim = dataFim;

    caixaApi.list(params)
      .then((res) => {
        if (res?.ok) {
          setItems(res.items || []);
          setTotal(res.total || 0);
        } else {
          setErro(true);
          toast.error(res?.erro || "Erro ao carregar movimentações");
        }
      })
      .catch(() => {
        setErro(true);
        toast.error("Erro ao carregar movimentações");
      })
      .finally(() => setLoading(false));
  }, [page, tipoFilter, origemFilter, dataInicio, dataFim]);

  useEffect(() => { buscar(); }, [buscar]);

  const handleFiltro = (setter) => (v) => { setter(v === "all" ? "" : v); setPage(1); };

  const openCreate = () => {
    setForm(EMPTY_MOVIMENTACAO);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const valor = parseFloat(form.valor);
    if (!valor || valor <= 0) {
      toast.error("Informe um valor válido.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await caixaApi.create({ tipo: form.tipo, valor, descricao: form.descricao });
      if (res?.ok) {
        toast.success("Movimentação lançada!");
        setDialogOpen(false);
        buscar();
        onMutate();
      } else {
        toast.error(res?.erro || "Erro ao lançar movimentação");
      }
    } catch {
      toast.error("Erro ao lançar movimentação");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEstornar = async () => {
    setEstornando(true);
    try {
      const res = await caixaApi.estornar(estornarId);
      if (res?.ok) {
        toast.success("Movimentação estornada");
        buscar();
        onMutate();
      } else {
        toast.error(res?.erro || "Erro ao estornar");
      }
    } catch {
      toast.error("Erro ao estornar");
    } finally {
      setEstornando(false);
      setEstornarId(null);
    }
  };

  const totalPaginas = Math.max(1, Math.ceil(total / PER_PAGE));

  return (
    <div className="space-y-4">
      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap items-center gap-3">
        <Select value={tipoFilter || "all"} onValueChange={handleFiltro(setTipoFilter)}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Tipo" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os tipos</SelectItem>
            <SelectItem value="entrada">Entrada</SelectItem>
            <SelectItem value="saida">Saída</SelectItem>
          </SelectContent>
        </Select>

        <Select value={origemFilter || "all"} onValueChange={handleFiltro(setOrigemFilter)}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Origem" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as origens</SelectItem>
            {Object.entries(ORIGEM_LABEL).map(([v, label]) => <SelectItem key={v} value={v}>{label}</SelectItem>)}
          </SelectContent>
        </Select>

        <Input type="date" value={dataInicio} onChange={(e) => { setDataInicio(e.target.value); setPage(1); }} className="w-40" aria-label="Data inicial" />
        <Input type="date" value={dataFim} onChange={(e) => { setDataFim(e.target.value); setPage(1); }} className="w-40" aria-label="Data final" />

        <Button className="ml-auto" onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Lançar</Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
      ) : erro ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          Não foi possível carregar as movimentações.
        </div>
      ) : items.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          Nenhuma movimentação encontrada.
        </div>
      ) : (
        <>
          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {["Data", "Tipo", "Valor", "Descrição", "Origem", "Status", ""].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {items.map((m) => {
                    const tipo = TIPO_BADGE[m.tipo] || { label: m.tipo, className: "" };
                    return (
                      <tr key={m.id} className="hover:bg-accent/30 transition-colors">
                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatDateTime(m.criado_em)}</td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className={tipo.className}>{tipo.label}</Badge>
                        </td>
                        <td className="px-4 py-3 font-medium text-card-foreground whitespace-nowrap">{formatCurrency(m.valor)}</td>
                        <td className="px-4 py-3 text-muted-foreground">{m.descricao || "—"}</td>
                        <td className="px-4 py-3 text-muted-foreground">{ORIGEM_LABEL[m.origem] || m.origem}</td>
                        <td className="px-4 py-3">
                          {m.estornada ? (
                            <span className="text-xs text-muted-foreground">Estornada</span>
                          ) : (
                            <span className="text-xs text-emerald-300">Ativa</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {!m.estornada && m.origem === "manual" && (
                            <Button variant="ghost" size="icon" className="h-7 w-7" title="Estornar" onClick={() => setEstornarId(m.id)}>
                              <RotateCcw className="h-3.5 w-3.5" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Página {page} de {totalPaginas} — {total} {total === 1 ? "movimentação" : "movimentações"}</span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
              </Button>
              <Button variant="outline" size="sm" disabled={page >= totalPaginas} onClick={() => setPage((p) => p + 1)}>
                Próxima <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        </>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nova Movimentação</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label>Tipo *</Label>
              <Select value={form.tipo} onValueChange={(v) => setForm((p) => ({ ...p, tipo: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="entrada">Entrada</SelectItem>
                  <SelectItem value="saida">Saída</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Valor (R$) *</Label>
              <Input type="number" step="0.01" min="0.01" value={form.valor} onChange={(e) => setForm((p) => ({ ...p, valor: e.target.value }))} required />
            </div>
            <div className="space-y-1.5">
              <Label>Descrição</Label>
              <Textarea value={form.descricao} onChange={(e) => setForm((p) => ({ ...p, descricao: e.target.value }))} />
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={submitting}>{submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Lançar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!estornarId} onOpenChange={(open) => !open && setEstornarId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Estornar movimentação?</AlertDialogTitle>
            <AlertDialogDescription>
              A movimentação permanece no histórico, mas deixa de contar no saldo. Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleEstornar} disabled={estornando} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              {estornando && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Estornar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

const EMPTY_CONTA = { descricao: "", categoria: "", valor: "", data_vencimento: "" };

const CONTAS_CONFIG = {
  pagar: {
    api: contasPagarApi,
    titulo: "Conta a Pagar",
    statusQuitado: "pago",
    acaoLabel: "Pagar",
    acaoIcon: ArrowUpCircle,
    acaoFn: (api, id) => api.pagar(id),
    vazio: "Nenhuma conta a pagar cadastrada.",
  },
  receber: {
    api: contasReceberApi,
    titulo: "Conta a Receber",
    statusQuitado: "recebido",
    acaoLabel: "Receber",
    acaoIcon: ArrowDownCircle,
    acaoFn: (api, id) => api.receber(id),
    vazio: "Nenhuma conta a receber cadastrada.",
  },
};

function ContasTab({ dominio, onMutate }) {
  const cfg = CONTAS_CONFIG[dominio];
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_CONTA);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [acaoId, setAcaoId] = useState(null);
  const [cancelarId, setCancelarId] = useState(null);
  const [processando, setProcessando] = useState(false);

  const buscar = useCallback(() => {
    setLoading(true);
    setErro(false);
    const params = { page, per_page: PER_PAGE };
    if (statusFilter) params.status = statusFilter;

    cfg.api.list(params)
      .then((res) => {
        if (res?.ok) {
          setItems(res.items || []);
          setTotal(res.total || 0);
        } else {
          setErro(true);
          toast.error(res?.erro || `Erro ao carregar ${cfg.titulo.toLowerCase()}s`);
        }
      })
      .catch(() => {
        setErro(true);
        toast.error(`Erro ao carregar ${cfg.titulo.toLowerCase()}s`);
      })
      .finally(() => setLoading(false));
  }, [cfg, page, statusFilter]);

  useEffect(() => { buscar(); }, [buscar]);

  const openCreate = () => {
    setForm(EMPTY_CONTA);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (c) => {
    setForm({
      descricao: c.descricao || "",
      categoria: c.categoria || "",
      valor: c.valor ?? "",
      data_vencimento: c.data_vencimento || "",
    });
    setEditId(c.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const valor = parseFloat(form.valor);
    if (!form.descricao.trim()) {
      toast.error("Informe a descrição.");
      return;
    }
    if (!valor || valor <= 0) {
      toast.error("Informe um valor válido.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = { ...form, valor };
      const res = editId ? await cfg.api.update(editId, payload) : await cfg.api.create(payload);
      if (res?.ok) {
        toast.success(editId ? `${cfg.titulo} atualizada!` : `${cfg.titulo} criada!`);
        setDialogOpen(false);
        buscar();
      } else {
        toast.error(res?.erro || "Erro ao salvar");
      }
    } catch {
      toast.error("Erro ao salvar");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAcao = async () => {
    setProcessando(true);
    try {
      const res = await cfg.acaoFn(cfg.api, acaoId);
      if (res?.ok) {
        toast.success(`${cfg.titulo} marcada como ${cfg.statusQuitado}!`);
        buscar();
        onMutate();
      } else {
        toast.error(res?.erro || "Erro ao processar");
      }
    } catch {
      toast.error("Erro ao processar");
    } finally {
      setProcessando(false);
      setAcaoId(null);
    }
  };

  const handleCancelar = async () => {
    setProcessando(true);
    try {
      const res = await cfg.api.cancelar(cancelarId);
      if (res?.ok) {
        toast.success(`${cfg.titulo} cancelada`);
        buscar();
      } else {
        toast.error(res?.erro || "Erro ao cancelar");
      }
    } catch {
      toast.error("Erro ao cancelar");
    } finally {
      setProcessando(false);
      setCancelarId(null);
    }
  };

  const handleDelete = async () => {
    try {
      const res = await cfg.api.delete(deleteId);
      if (res?.ok) {
        toast.success(`${cfg.titulo} excluída`);
        buscar();
      } else {
        toast.error(res?.erro || "Erro ao excluir");
      }
    } catch {
      toast.error("Erro ao excluir");
    } finally {
      setDeleteId(null);
    }
  };

  const totalPaginas = Math.max(1, Math.ceil(total / PER_PAGE));
  const AcaoIcon = cfg.acaoIcon;

  return (
    <div className="space-y-4">
      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap items-center gap-3">
        <Select value={statusFilter || "all"} onValueChange={(v) => { setStatusFilter(v === "all" ? "" : v); setPage(1); }}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os status</SelectItem>
            <SelectItem value="pendente">Pendente</SelectItem>
            <SelectItem value={cfg.statusQuitado}>{STATUS_CONTA_BADGE[cfg.statusQuitado].label}</SelectItem>
            <SelectItem value="cancelado">Cancelado</SelectItem>
          </SelectContent>
        </Select>

        <Button className="ml-auto" onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Nova {cfg.titulo}</Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
      ) : erro ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          Não foi possível carregar {cfg.titulo.toLowerCase()}s.
        </div>
      ) : items.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">{cfg.vazio}</div>
      ) : (
        <>
          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {["Descrição", "Categoria", "Valor", "Vencimento", "Status", ""].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {items.map((c) => {
                    const status = STATUS_CONTA_BADGE[c.status] || { label: c.status, className: "" };
                    const pendente = c.status === "pendente";
                    return (
                      <tr key={c.id} className="hover:bg-accent/30 transition-colors">
                        <td className="px-4 py-3 font-medium text-card-foreground">{c.descricao}</td>
                        <td className="px-4 py-3 text-muted-foreground">{c.categoria || "—"}</td>
                        <td className="px-4 py-3 font-medium text-card-foreground whitespace-nowrap">{formatCurrency(c.valor)}</td>
                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatData(c.data_vencimento)}</td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className={status.className}>{status.label}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          {pendente && (
                            <div className="flex items-center gap-1 justify-end">
                              <Button variant="ghost" size="icon" className="h-7 w-7" title={cfg.acaoLabel} onClick={() => setAcaoId(c.id)}>
                                <AcaoIcon className="h-3.5 w-3.5" />
                              </Button>
                              <Button variant="ghost" size="icon" className="h-7 w-7" title="Editar" onClick={() => openEdit(c)}>
                                <Pencil className="h-3.5 w-3.5" />
                              </Button>
                              <Button variant="ghost" size="icon" className="h-7 w-7" title="Cancelar" onClick={() => setCancelarId(c.id)}>
                                <XCircle className="h-3.5 w-3.5" />
                              </Button>
                              <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" title="Excluir" onClick={() => setDeleteId(c.id)}>
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

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Página {page} de {totalPaginas} — {total} {total === 1 ? "conta" : "contas"}</span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
              </Button>
              <Button variant="outline" size="sm" disabled={page >= totalPaginas} onClick={() => setPage((p) => p + 1)}>
                Próxima <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        </>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editId ? `Editar ${cfg.titulo}` : `Nova ${cfg.titulo}`}</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label>Descrição *</Label>
              <Input value={form.descricao} onChange={(e) => setForm((p) => ({ ...p, descricao: e.target.value }))} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Categoria</Label>
                <Input value={form.categoria} onChange={(e) => setForm((p) => ({ ...p, categoria: e.target.value }))} />
              </div>
              <div className="space-y-1.5">
                <Label>Valor (R$) *</Label>
                <Input type="number" step="0.01" min="0.01" value={form.valor} onChange={(e) => setForm((p) => ({ ...p, valor: e.target.value }))} required />
              </div>
              <div className="space-y-1.5 col-span-2">
                <Label>Vencimento</Label>
                <Input type="date" value={form.data_vencimento} onChange={(e) => setForm((p) => ({ ...p, data_vencimento: e.target.value }))} />
              </div>
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={submitting}>{submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Salvar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!acaoId} onOpenChange={(open) => !open && setAcaoId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{cfg.acaoLabel} esta conta?</AlertDialogTitle>
            <AlertDialogDescription>
              Isso gera uma {cfg.statusQuitado === "pago" ? "saída" : "entrada"} de caixa correspondente e não pode ser desfeito.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction onClick={handleAcao} disabled={processando}>
              {processando && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}{cfg.acaoLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={!!cancelarId} onOpenChange={(open) => !open && setCancelarId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancelar esta conta?</AlertDialogTitle>
            <AlertDialogDescription>A conta fica marcada como cancelada e não pode mais ser paga/recebida.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction onClick={handleCancelar} disabled={processando} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              {processando && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Cancelar conta
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir {cfg.titulo}?</AlertDialogTitle>
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

const TABS = [
  { key: "movimentacoes", label: "Movimentações" },
  { key: "contas-pagar", label: "Contas a Pagar" },
  { key: "contas-receber", label: "Contas a Receber" },
];

export default function Financeiro() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("movimentacoes");
  const [saldo, setSaldo] = useState(null);
  const [saldoLoading, setSaldoLoading] = useState(true);
  const [saldoRefreshKey, setSaldoRefreshKey] = useState(0);

  const podeAcessar = user?.perfil === "admin" || user?.perfil === "financeiro";
  const carregarSaldo = () => setSaldoRefreshKey((k) => k + 1);

  useEffect(() => {
    if (!podeAcessar) return;
    let ativo = true;

    async function buscar() {
      setSaldoLoading(true);
      const res = await caixaApi.saldo();
      if (ativo && res?.ok) setSaldo(res.saldo);
      if (ativo) setSaldoLoading(false);
    }

    buscar();
    return () => { ativo = false; };
  }, [podeAcessar, saldoRefreshKey]);

  if (!podeAcessar) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Lock className="h-10 w-10" />
        <p>Somente perfis administrador ou financeiro podem acessar o Financeiro.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Financeiro</h1>
          <p className="text-muted-foreground text-sm">Caixa, contas a pagar e contas a receber</p>
        </div>
        <div className="bg-card border border-border rounded-xl px-5 py-3 flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center">
            <Wallet className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Saldo em caixa</p>
            {saldoLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : (
              <p className={`text-lg font-bold ${saldo < 0 ? "text-red-400" : "text-foreground"}`}>{formatCurrency(saldo)}</p>
            )}
          </div>
        </div>
      </div>

      <div className="flex gap-1 bg-secondary p-1 rounded-lg w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "bg-card text-card-foreground shadow"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "movimentacoes" && <Movimentacoes onMutate={carregarSaldo} />}
      {activeTab === "contas-pagar" && <ContasTab dominio="pagar" onMutate={carregarSaldo} />}
      {activeTab === "contas-receber" && <ContasTab dominio="receber" onMutate={carregarSaldo} />}
    </div>
  );
}
