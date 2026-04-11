import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, Plus, Minus, Search } from "lucide-react";
import { constantes as constApi, reparos as reparosApi, estoque as estoqueApi, ordens as ordensApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";

const EMPTY_FORM = {
  tipo: "Assistencia",
  cliente: "",
  modelo: "",
  cor: "",
  imei: "",
  tecnico: "",
  vendedor: "",
  status: "Em andamento",
  valor_cobrado: "",
  valor_descontado: "",
  data_os: new Date().toISOString().split("T")[0],
  observacoes: "",
};

export default function NewOrder() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY_FORM);
  const [constants, setConstants] = useState(null);
  const [reparosList, setReparosList] = useState([]);
  const [estoqueList, setEstoqueList] = useState([]);
  const [selectedReparos, setSelectedReparos] = useState([]);
  const [pecas, setPecas] = useState({});
  const [stockSearch, setStockSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([constApi.get(), reparosApi.list(), estoqueApi.list()]).then(([c, r, e]) => {
      if (c?.ok) setConstants(c);
      if (r?.ok) setReparosList(r.reparos || []);
      if (e?.ok) setEstoqueList(e.items || []);
      setLoading(false);
    });
  }, []);

  const setField = (key, value) => setForm((p) => ({ ...p, [key]: value }));

  const toggleReparo = (id) => {
    setSelectedReparos((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const adjustPeca = (id, delta) => {
    setPecas((prev) => {
      const current = prev[id] || 0;
      const next = Math.max(0, current + delta);
      if (next === 0) {
        const { [id]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [id]: next };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        valor_cobrado: parseFloat(form.valor_cobrado) || 0,
        valor_descontado: parseFloat(form.valor_descontado) || 0,
        reparo_ids: selectedReparos,
        pecas: Object.fromEntries(Object.entries(pecas).map(([k, v]) => [String(k), v])),
      };
      const res = await ordensApi.create(payload);
      if (res?.ok) {
        toast.success("Ordem criada com sucesso!");
        navigate("/ordens");
      } else {
        toast.error(res?.erro || "Erro ao criar ordem");
      }
    } catch {
      toast.error("Erro ao criar ordem");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const filteredEstoque = estoqueList.filter((item) =>
    item.descricao?.toLowerCase().includes(stockSearch.toLowerCase()) ||
    item.modelo?.toLowerCase().includes(stockSearch.toLowerCase())
  );

  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Nova Ordem de Serviço</h1>
        <p className="text-muted-foreground text-sm">Preencha todos os dados da OS</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Cliente / Tipo */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Cliente</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2 space-y-1.5">
              <Label>Nome do Cliente *</Label>
              <Input value={form.cliente} onChange={(e) => setField("cliente", e.target.value)} placeholder="Nome completo" required />
            </div>
            <div className="space-y-1.5">
              <Label>Tipo de OS</Label>
              <Select value={form.tipo} onValueChange={(v) => setField("tipo", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(constants?.os_tipos || ["Assistencia", "Garantia", "Upgrade"]).map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Data da OS</Label>
              <Input type="date" value={form.data_os} onChange={(e) => setField("data_os", e.target.value)} />
            </div>
          </div>
        </section>

        {/* Aparelho */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Aparelho</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Modelo *</Label>
              <Select value={form.modelo} onValueChange={(v) => { setField("modelo", v); setField("cor", ""); }}>
                <SelectTrigger><SelectValue placeholder="Selecione o modelo" /></SelectTrigger>
                <SelectContent>
                  {(constants?.iphone_models || []).map((m) => (
                    <SelectItem key={m} value={m}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Cor</Label>
              <Select value={form.cor} onValueChange={(v) => setField("cor", v)}>
                <SelectTrigger><SelectValue placeholder="Cor do aparelho" /></SelectTrigger>
                <SelectContent>
                  {(constants?.iphone_colors?.[form.modelo] || []).map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="col-span-2 space-y-1.5">
              <Label>IMEI</Label>
              <Input value={form.imei} onChange={(e) => setField("imei", e.target.value)} placeholder="000000000000000" maxLength={16} />
            </div>
          </div>
        </section>

        {/* Serviço */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Serviço</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Técnico</Label>
              <Select value={form.tecnico} onValueChange={(v) => setField("tecnico", v)}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent>
                  {(constants?.tecnicos || []).map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Vendedor</Label>
              <Select value={form.vendedor} onValueChange={(v) => setField("vendedor", v)}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent>
                  {(constants?.vendedores || []).map((v) => (
                    <SelectItem key={v} value={v}>{v}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Status</Label>
              <Select value={form.status} onValueChange={(v) => setField("status", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(constants?.status_opcoes || ["Em andamento", "Aguardando peca", "Finalizado", "Cancelado"]).map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {reparosList.length > 0 && (
            <div className="space-y-2">
              <Label>Tipos de Reparo</Label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {reparosList.map((r) => (
                  <label key={r.id} className="flex items-center gap-2 cursor-pointer text-sm">
                    <Checkbox
                      checked={selectedReparos.includes(r.id)}
                      onCheckedChange={() => toggleReparo(r.id)}
                    />
                    <span className="text-card-foreground">{r.nome}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Financeiro */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Financeiro</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Valor Cobrado (R$)</Label>
              <Input type="number" step="0.01" min="0" value={form.valor_cobrado} onChange={(e) => setField("valor_cobrado", e.target.value)} placeholder="0,00" />
            </div>
            <div className="space-y-1.5">
              <Label>Valor com Desconto (R$)</Label>
              <Input type="number" step="0.01" min="0" value={form.valor_descontado} onChange={(e) => setField("valor_descontado", e.target.value)} placeholder="0,00" />
            </div>
          </div>
        </section>

        {/* Peças do Estoque */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Peças do Estoque</h2>
          <div className="relative">
            <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar peça..."
              value={stockSearch}
              onChange={(e) => setStockSearch(e.target.value)}
              className="pl-8"
            />
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {filteredEstoque.length === 0 ? (
              <p className="text-muted-foreground text-sm text-center py-4">Nenhuma peça encontrada</p>
            ) : (
              filteredEstoque.map((item) => (
                <div key={item.id} className="flex items-center justify-between bg-secondary rounded-lg px-3 py-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-card-foreground truncate">{item.descricao}</p>
                    <p className="text-xs text-muted-foreground">{item.modelo} • Estoque: {item.quantidade}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={() => adjustPeca(item.id, -1)}>
                      <Minus className="h-3.5 w-3.5" />
                    </Button>
                    <span className="w-6 text-center text-sm font-medium">{pecas[item.id] || 0}</span>
                    <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={() => adjustPeca(item.id, 1)}>
                      <Plus className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Observações */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Observações</h2>
          <Textarea
            value={form.observacoes}
            onChange={(e) => setField("observacoes", e.target.value)}
            placeholder="Observações adicionais sobre a OS..."
          />
        </section>

        <div className="flex gap-3">
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Criar Ordem
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate("/ordens")}>
            Cancelar
          </Button>
        </div>
      </form>
    </div>
  );
}
