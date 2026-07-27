import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Search, UserCircle, Smartphone, Check, Plus, Eye, Printer } from "lucide-react";
import { clientes as clientesApi, unidadesSerializadas as unidadesApi, vendas as vendasApi } from "@/api/client";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { formatCurrency } from "@/lib/constants";

const FORMAS_PAGAMENTO = [
  { value: "pix", label: "Pix" },
  { value: "cartao", label: "Cartão" },
  { value: "dinheiro", label: "Dinheiro" },
  { value: "transferencia", label: "Transferência" },
];

const ORIGEM_BADGE = {
  estoque: { label: "Estoque", className: "bg-blue-500/10 text-blue-300 border-blue-500/30" },
  produto: { label: "Produto", className: "bg-purple-500/10 text-purple-300 border-purple-500/30" },
};

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
};

export default function Vendas() {
  const [form, setForm] = useState(EMPTY_STATE);
  const [clienteResultados, setClienteResultados] = useState([]);
  const [buscandoCliente, setBuscandoCliente] = useState(false);
  const [aparelhoResultados, setAparelhoResultados] = useState([]);
  const [buscandoAparelho, setBuscandoAparelho] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [vendaConcluida, setVendaConcluida] = useState(null);
  const [detalheVenda, setDetalheVenda] = useState(null);
  const [carregandoDetalhe, setCarregandoDetalhe] = useState(false);

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
    setDetalheVenda(null);
  };

  const verVenda = async () => {
    if (!vendaConcluida) return;
    setCarregandoDetalhe(true);
    try {
      const res = await vendasApi.get(vendaConcluida.id);
      if (res?.ok) setDetalheVenda(res);
      else toast.error(res?.erro || "Erro ao carregar venda");
    } catch {
      toast.error("Erro ao carregar venda");
    } finally {
      setCarregandoDetalhe(false);
    }
  };

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
            <Button variant="outline" onClick={verVenda} disabled={carregandoDetalhe}>
              {carregandoDetalhe ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Eye className="h-4 w-4 mr-2" />}
              Ver venda
            </Button>
            <Button variant="outline" onClick={() => toast.info("Impressão ainda não disponível — em breve.")}>
              <Printer className="h-4 w-4 mr-2" />Imprimir
            </Button>
          </div>

          {detalheVenda && (
            <div className="bg-secondary/40 rounded-lg p-4 text-left text-xs space-y-1 text-muted-foreground">
              <p className="font-medium text-card-foreground mb-1">Registro no servidor</p>
              {detalheVenda.itens.map((item) => (
                <p key={item.id}>
                  {item.produto_nome} ({item.produto_sku || "sem SKU"}) — preço de tabela {item.valor_tabela != null ? formatCurrency(item.valor_tabela) : "—"}, vendido por {formatCurrency(item.valor_unitario)}
                </p>
              ))}
            </div>
          )}
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
