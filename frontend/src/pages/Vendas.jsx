import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, Search, UserCircle, Smartphone, Check, Plus, Eye, Printer, ChevronLeft, ChevronRight } from "lucide-react";
import { clientes as clientesApi, unidadesSerializadas as unidadesApi, vendas as vendasApi } from "@/api/client";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { formatCurrency, vendaStatusBadge } from "@/lib/constants";

const FORMAS_PAGAMENTO = [
  { value: "pix", label: "Pix" },
  { value: "cartao", label: "Cartão" },
  { value: "dinheiro", label: "Dinheiro" },
  { value: "transferencia", label: "Transferência" },
];

const STATUS_VENDA_OPCOES = [
  { value: "concluida", label: "Concluída" },
  { value: "cancelada", label: "Cancelada" },
];

const ORIGEM_BADGE = {
  estoque: { label: "Estoque", className: "bg-blue-500/10 text-blue-300 border-blue-500/30" },
  produto: { label: "Produto", className: "bg-purple-500/10 text-purple-300 border-purple-500/30" },
};

const SORT_OPTIONS = [
  { value: "recente", label: "Mais recente" },
  { value: "antigo", label: "Mais antigo" },
];

const PER_PAGE_HISTORICO = 20;

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  const horaCurta = (hora || "").slice(0, 5);
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${horaCurta}`.trim() : value;
}

function Historico() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [formaPagamentoFilter, setFormaPagamentoFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [sort, setSort] = useState("recente");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput); setPage(1); }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  const handleFormaPagamentoChange = (v) => { setFormaPagamentoFilter(v === "all" ? "" : v); setPage(1); };
  const handleStatusChange = (v) => { setStatusFilter(v === "all" ? "" : v); setPage(1); };
  const handleSortChange = (v) => { setSort(v); setPage(1); };
  const handleDataInicioChange = (v) => { setDataInicio(v); setPage(1); };
  const handleDataFimChange = (v) => { setDataFim(v); setPage(1); };

  useEffect(() => {
    let ativo = true;

    async function buscar() {
      setLoading(true);
      setErro(false);
      const params = { page, per_page: PER_PAGE_HISTORICO, sort };
      if (search) params.q = search;
      if (formaPagamentoFilter) params.forma_pagamento = formaPagamentoFilter;
      if (statusFilter) params.status = statusFilter;
      if (dataInicio) params.data_inicio = dataInicio;
      if (dataFim) params.data_fim = dataFim;

      try {
        const res = await vendasApi.list(params);
        if (!ativo) return;
        if (res?.ok) {
          setItems(res.items || []);
          setTotal(res.total || 0);
        } else {
          setErro(true);
          toast.error(res?.erro || "Erro ao carregar histórico de vendas");
        }
      } catch {
        if (ativo) {
          setErro(true);
          toast.error("Erro ao carregar histórico de vendas");
        }
      } finally {
        if (ativo) setLoading(false);
      }
    }

    buscar();
    return () => { ativo = false; };
  }, [page, search, formaPagamentoFilter, statusFilter, dataInicio, dataFim, sort]);

  const totalPaginas = Math.max(1, Math.ceil(total / PER_PAGE_HISTORICO));
  const filtrosAtivos = Boolean(search || formaPagamentoFilter || statusFilter || dataInicio || dataFim);

  return (
    <div className="space-y-5">
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por cliente, IMEI ou produto..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap gap-3">
        <Select value={formaPagamentoFilter || "all"} onValueChange={handleFormaPagamentoChange}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Pagamento" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as formas</SelectItem>
            {FORMAS_PAGAMENTO.map((f) => <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={statusFilter || "all"} onValueChange={handleStatusChange}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            {STATUS_VENDA_OPCOES.map((s) => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
          </SelectContent>
        </Select>

        <Input type="date" value={dataInicio} onChange={(e) => handleDataInicioChange(e.target.value)} className="w-40" aria-label="Data inicial" />
        <Input type="date" value={dataFim} onChange={(e) => handleDataFimChange(e.target.value)} className="w-40" aria-label="Data final" />

        <Select value={sort} onValueChange={handleSortChange}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Ordenar por" /></SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
          </SelectContent>
        </Select>

        <div className="ml-auto flex items-center text-xs text-muted-foreground">
          {total} {total === 1 ? "venda" : "vendas"} {filtrosAtivos ? "encontradas" : "no total"}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : erro ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          Não foi possível carregar o histórico de vendas.
        </div>
      ) : items.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          {filtrosAtivos ? "Nenhuma venda corresponde à busca/filtros atuais." : "Nenhuma venda registrada ainda."}
        </div>
      ) : (
        <>
          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {["Data", "Cliente", "Aparelho", "Vendedor", "Pagamento", "Valor", "Status"].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {items.map((item) => {
                    const primeiroItem = item.itens_resumo?.[0];
                    const status = vendaStatusBadge(item.status);
                    return (
                      <tr
                        key={item.id}
                        className="hover:bg-accent/30 transition-colors cursor-pointer"
                        data-testid={`venda-row-${item.id}`}
                        onClick={() => navigate(`/vendas/${item.id}`)}
                      >
                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatDateTime(item.criado_em)}</td>
                        <td className="px-4 py-3 font-medium text-card-foreground">{item.cliente_nome || "—"}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {primeiroItem ? (
                            <>
                              <p className="text-card-foreground">{primeiroItem.produto_nome}</p>
                              <p className="text-xs font-mono">{primeiroItem.imei || "—"}</p>
                            </>
                          ) : "—"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{item.vendedor_nome || "—"}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {FORMAS_PAGAMENTO.find((f) => f.value === item.forma_pagamento)?.label || item.forma_pagamento || "—"}
                        </td>
                        <td className="px-4 py-3 font-medium text-card-foreground whitespace-nowrap">{formatCurrency(item.valor_total)}</td>
                        <td className="px-4 py-3">
                          <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", status.className].join(" ")}>
                            {status.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Página {page} de {totalPaginas} — {total} {total === 1 ? "venda" : "vendas"}</span>
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
    </div>
  );
}

function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function aparelhoDetalhes(unidade) {
  const partes = [unidade.origem_label, unidade.produto_capacidade, unidade.produto_cor].filter(Boolean);
  return partes.join(" · ");
}

const EMPTY_STATE = {
  clienteQuery: "",
  clienteSelecionado: null,
  aparelhoQuery: "",
  aparelhoSelecionado: null,
  valorVenda: "",
  formaPagamento: "",
  observacoes: "",
  motivoDesconto: "",
};

const TABS = [
  { key: "nova", label: "Nova Venda" },
  { key: "historico", label: "Histórico" },
];

function NovaVenda() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY_STATE);
  const [clienteResultados, setClienteResultados] = useState([]);
  const [buscandoCliente, setBuscandoCliente] = useState(false);
  const [aparelhoResultados, setAparelhoResultados] = useState([]);
  const [buscandoAparelho, setBuscandoAparelho] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [vendaConcluida, setVendaConcluida] = useState(null);

  const clienteQueryDebounced = useDebounced(form.clienteQuery);
  const aparelhoQueryDebounced = useDebounced(form.aparelhoQuery);

  useEffect(() => {
    if (form.clienteSelecionado || clienteQueryDebounced.trim().length < 2) {
      setClienteResultados([]);
      return;
    }
    let ativo = true;
    setBuscandoCliente(true);
    clientesApi.list({ q: clienteQueryDebounced }).then((res) => {
      if (!ativo) return;
      setClienteResultados(res?.ok ? res.items || [] : []);
    }).finally(() => { if (ativo) setBuscandoCliente(false); });
    return () => { ativo = false; };
  }, [clienteQueryDebounced, form.clienteSelecionado]);

  useEffect(() => {
    if (!form.clienteSelecionado || form.aparelhoSelecionado || aparelhoQueryDebounced.trim().length < 2) {
      setAparelhoResultados([]);
      return;
    }
    let ativo = true;
    setBuscandoAparelho(true);
    unidadesApi.list({ q: aparelhoQueryDebounced, status: "disponivel", per_page: 10 }).then((res) => {
      if (!ativo) return;
      setAparelhoResultados(res?.ok ? res.items || [] : []);
    }).finally(() => { if (ativo) setBuscandoAparelho(false); });
    return () => { ativo = false; };
  }, [aparelhoQueryDebounced, form.clienteSelecionado, form.aparelhoSelecionado]);

  const selecionarCliente = (cliente) => {
    setForm((p) => ({ ...p, clienteSelecionado: cliente, clienteQuery: cliente.nome }));
    setClienteResultados([]);
  };

  const trocarCliente = () => {
    setForm((p) => ({ ...p, clienteSelecionado: null, clienteQuery: "", aparelhoSelecionado: null, aparelhoQuery: "", valorVenda: "" }));
  };

  const selecionarAparelho = (unidade) => {
    const precoSugerido = unidade.preco_catalogo != null ? String(unidade.preco_catalogo) : "";
    setForm((p) => ({ ...p, aparelhoSelecionado: unidade, aparelhoQuery: unidade.imei, valorVenda: precoSugerido }));
    setAparelhoResultados([]);
  };

  const trocarAparelho = () => {
    setForm((p) => ({ ...p, aparelhoSelecionado: null, aparelhoQuery: "", valorVenda: "" }));
  };

  const novaVenda = () => {
    setForm(EMPTY_STATE);
    setVendaConcluida(null);
  };

  // Desconto (BR-053): sempre permitido, sempre registrado -- nunca bloqueia
  // a venda. `desconto` só existe aqui para decidir se mostra o campo de
  // motivo (nenhum efeito de validação).
  const precoTabela = form.aparelhoSelecionado?.preco_catalogo;
  const valorVendaNum = parseFloat(form.valorVenda) || 0;
  const desconto = precoTabela != null ? Math.round((precoTabela - valorVendaNum) * 100) / 100 : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const valor = parseFloat(form.valorVenda);
    if (!form.clienteSelecionado || !form.aparelhoSelecionado) {
      toast.error("Selecione o cliente e o aparelho.");
      return;
    }
    if (!form.formaPagamento) {
      toast.error("Selecione a forma de pagamento.");
      return;
    }
    if (!valor || valor <= 0) {
      toast.error("Informe um valor de venda válido.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await vendasApi.create({
        cliente_id: form.clienteSelecionado.id,
        unidade_serializada_id: form.aparelhoSelecionado.id,
        forma_pagamento: form.formaPagamento,
        valor_unitario: valor,
        observacoes: form.observacoes,
        motivo_desconto: form.motivoDesconto,
      });
      if (res?.ok) {
        toast.success("Venda concluída!");
        setVendaConcluida({
          id: res.id,
          cliente: form.clienteSelecionado,
          aparelho: form.aparelhoSelecionado,
          valor,
          formaPagamento: form.formaPagamento,
        });
      } else {
        toast.error(res?.erro || "Erro ao concluir a venda");
      }
    } catch {
      toast.error("Erro ao concluir a venda");
    } finally {
      setSubmitting(false);
    }
  };

  if (vendaConcluida) {
    const formaLabel = FORMAS_PAGAMENTO.find((f) => f.value === vendaConcluida.formaPagamento)?.label;
    return (
      <div className="space-y-5 max-w-xl">
        <div className="bg-card border border-border rounded-xl p-6 text-center space-y-4">
          <div className="mx-auto h-12 w-12 rounded-full bg-emerald-500/10 flex items-center justify-center">
            <Check className="h-6 w-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Venda concluída</h1>
            <p className="text-muted-foreground text-sm">Venda #{vendaConcluida.id}</p>
          </div>

          <div className="bg-secondary/40 rounded-lg p-4 text-left space-y-1.5 text-sm">
            <p><span className="text-muted-foreground">Cliente:</span> {vendaConcluida.cliente.nome}</p>
            <p><span className="text-muted-foreground">Aparelho:</span> {aparelhoDetalhes(vendaConcluida.aparelho)} — IMEI {vendaConcluida.aparelho.imei}</p>
            <p><span className="text-muted-foreground">Pagamento:</span> {formaLabel}</p>
            <p><span className="text-muted-foreground">Valor:</span> {formatCurrency(vendaConcluida.valor)}</p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            <Button onClick={novaVenda}><Plus className="h-4 w-4 mr-2" />Nova venda</Button>
            <Button variant="outline" onClick={() => navigate(`/vendas/${vendaConcluida.id}`)}>
              <Eye className="h-4 w-4 mr-2" />Ver venda
            </Button>
            <Button variant="outline" onClick={() => toast.info("Impressão ainda não disponível — em breve.")}>
              <Printer className="h-4 w-4 mr-2" />Imprimir
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Nova Venda</h1>
        <p className="text-muted-foreground text-sm">Venda de um aparelho a um cliente</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Cliente */}
        <div className="bg-card border border-border rounded-xl p-4 space-y-2">
          <Label className="flex items-center gap-2"><UserCircle className="h-4 w-4" />Cliente</Label>
          {form.clienteSelecionado ? (
            <div className="flex items-center justify-between bg-secondary/40 rounded-lg px-3 py-2">
              <div>
                <p className="text-sm font-medium text-card-foreground">{form.clienteSelecionado.nome}</p>
                <p className="text-xs text-muted-foreground">{form.clienteSelecionado.telefone || form.clienteSelecionado.email || "—"}</p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={trocarCliente}>Trocar</Button>
            </div>
          ) : (
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar cliente por nome, telefone ou e-mail..."
                className="pl-8"
                value={form.clienteQuery}
                onChange={(e) => setForm((p) => ({ ...p, clienteQuery: e.target.value }))}
              />
              {buscandoCliente && <Loader2 className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />}
              {clienteResultados.length > 0 && (
                <div className="absolute z-10 mt-1 w-full bg-popover border border-border rounded-lg shadow-lg max-h-56 overflow-y-auto">
                  {clienteResultados.map((c) => (
                    <button
                      type="button"
                      key={c.id}
                      onClick={() => selecionarCliente(c)}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-accent/50 transition-colors"
                    >
                      <p className="font-medium text-card-foreground">{c.nome}</p>
                      <p className="text-xs text-muted-foreground">{c.telefone || c.email || "—"}</p>
                    </button>
                  ))}
                </div>
              )}
              {!form.clienteSelecionado && form.clienteQuery.trim().length >= 2 && !buscandoCliente && clienteResultados.length === 0 && (
                <p className="text-xs text-muted-foreground mt-1">Nenhum cliente encontrado — cadastre em Clientes antes de continuar.</p>
              )}
            </div>
          )}
        </div>

        {/* Aparelho */}
        {form.clienteSelecionado && (
          <div className="bg-card border border-border rounded-xl p-4 space-y-2">
            <Label className="flex items-center gap-2"><Smartphone className="h-4 w-4" />Aparelho</Label>
            {form.aparelhoSelecionado ? (
              <div className="flex items-center justify-between bg-secondary/40 rounded-lg px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-card-foreground">{aparelhoDetalhes(form.aparelhoSelecionado)}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-muted-foreground">IMEI {form.aparelhoSelecionado.imei}</span>
                    <Badge variant="outline" className={ORIGEM_BADGE[form.aparelhoSelecionado.origem_tipo]?.className}>
                      {ORIGEM_BADGE[form.aparelhoSelecionado.origem_tipo]?.label || "—"}
                    </Badge>
                  </div>
                </div>
                <Button type="button" variant="ghost" size="sm" onClick={trocarAparelho}>Trocar</Button>
              </div>
            ) : (
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por IMEI, modelo ou SKU..."
                  className="pl-8"
                  value={form.aparelhoQuery}
                  onChange={(e) => setForm((p) => ({ ...p, aparelhoQuery: e.target.value }))}
                />
                {buscandoAparelho && <Loader2 className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />}
                {aparelhoResultados.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-popover border border-border rounded-lg shadow-lg max-h-64 overflow-y-auto">
                    {aparelhoResultados.map((u) => (
                      <button
                        type="button"
                        key={u.id}
                        onClick={() => selecionarAparelho(u)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-accent/50 transition-colors flex items-center justify-between gap-2"
                      >
                        <div>
                          <p className="font-medium text-card-foreground">{aparelhoDetalhes(u)}</p>
                          <p className="text-xs text-muted-foreground">IMEI {u.imei} · {u.origem_sku || "sem SKU"}</p>
                        </div>
                        <span className="text-sm font-medium text-card-foreground shrink-0">
                          {u.preco_catalogo != null ? formatCurrency(u.preco_catalogo) : "—"}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
                {form.aparelhoQuery.trim().length >= 2 && !buscandoAparelho && aparelhoResultados.length === 0 && (
                  <p className="text-xs text-muted-foreground mt-1">Nenhuma unidade disponível encontrada.</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Resumo automático + preço + pagamento */}
        {form.clienteSelecionado && form.aparelhoSelecionado && (
          <div className="bg-card border border-border rounded-xl p-4 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="venda-valor">Preço da venda</Label>
                <Input
                  id="venda-valor"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.valorVenda}
                  onChange={(e) => setForm((p) => ({ ...p, valorVenda: e.target.value }))}
                  required
                />
                {form.aparelhoSelecionado.preco_catalogo != null && (
                  <p className="text-xs text-muted-foreground">
                    Preço de catálogo: {formatCurrency(form.aparelhoSelecionado.preco_catalogo)}
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="venda-pagamento">Forma de pagamento</Label>
                <Select value={form.formaPagamento} onValueChange={(v) => setForm((p) => ({ ...p, formaPagamento: v }))}>
                  <SelectTrigger id="venda-pagamento" className="w-full"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {FORMAS_PAGAMENTO.map((f) => <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {desconto != null && desconto > 0 && (
              <div className="space-y-1.5">
                <Label htmlFor="venda-motivo-desconto">Motivo do desconto (opcional)</Label>
                <Input
                  id="venda-motivo-desconto"
                  placeholder="Ex.: negociação, pagamento à vista..."
                  value={form.motivoDesconto}
                  onChange={(e) => setForm((p) => ({ ...p, motivoDesconto: e.target.value }))}
                />
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="venda-observacoes">Observações (opcional)</Label>
              <Textarea
                id="venda-observacoes"
                placeholder="Ex.: retirada amanhã, venda corporativa, NF enviada..."
                value={form.observacoes}
                onChange={(e) => setForm((p) => ({ ...p, observacoes: e.target.value }))}
                rows={2}
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-border">
              <span className="text-sm text-muted-foreground">Total</span>
              <span className="text-lg font-bold text-foreground">
                {formatCurrency(parseFloat(form.valorVenda) || 0)}
              </span>
            </div>

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {submitting ? "Confirmando..." : "Confirmar Venda"}
            </Button>
          </div>
        )}
      </form>
    </div>
  );
}

export default function Vendas() {
  const [activeTab, setActiveTab] = useState("nova");

  return (
    <div className="space-y-5">
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

      {activeTab === "nova" ? <NovaVenda /> : <Historico />}
    </div>
  );
}
