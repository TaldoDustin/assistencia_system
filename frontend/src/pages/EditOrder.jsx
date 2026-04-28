import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, Plus, Minus, Search, QrCode, Copy, ExternalLink } from "lucide-react";
import { constantes as constApi, reparos as reparosApi, estoque as estoqueApi, ordens as ordensApi, checklist as checklistApi, precos as precosApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { formatCurrency } from "@/lib/constants";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";

export default function EditOrder() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState(null);
  const [constants, setConstants] = useState(null);
  const [reparosList, setReparosList] = useState([]);
  const [estoqueList, setEstoqueList] = useState([]);
  const [selectedReparos, setSelectedReparos] = useState([]);
  const [pecas, setPecas] = useState({});
  const [stockSearch, setStockSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [cancelDialog, setCancelDialog] = useState(false);
  const [suggestedPrice, setSuggestedPrice] = useState(null);
  const [checklistMeta, setChecklistMeta] = useState(null);
  const [checklistDialog, setChecklistDialog] = useState(false);
  const [checklistLoading, setChecklistLoading] = useState(false);
  const initialized = useRef(false);

  useEffect(() => {
    Promise.all([
      ordensApi.get(id),
      constApi.get(),
      reparosApi.list(),
      estoqueApi.list(),
    ]).then(([osRes, constRes, rRes, eRes]) => {
      if (osRes?.ok && osRes.ordem) {
        const os = osRes.ordem;
        setForm({
          tipo: os.tipo || "Assistencia",
          cliente: os.cliente || "",
          modelo: os.modelo || "",
          cor: os.cor || "",
          imei: os.imei || "",
          tecnico: os.tecnico || "",
          vendedor: os.vendedor || "",
          status: os.status || "Em andamento",
          valor_cobrado: os.valor_cobrado || "",
          valor_descontado: os.valor_descontado || "",
          data_os: os.data ? os.data.split("T")[0] : new Date().toISOString().split("T")[0],
          observacoes: os.observacoes || "",
        });
        setSelectedReparos(os.reparo_ids || []);
        const pecasMap = {};
        (os.pecas_usadas || []).forEach((p) => { pecasMap[p.estoque_id] = p.quantidade; });
        setPecas(pecasMap);
      } else {
        toast.error("Ordem não encontrada");
        navigate("/ordens");
      }
      if (constRes?.ok) setConstants(constRes);
      if (rRes?.ok) setReparosList(rRes.reparos || []);
      if (eRes?.ok) setEstoqueList(eRes.items || []);
      setLoading(false);
      initialized.current = true;
    });

    checklistApi.getByOrder(id).then((res) => {
      if (res?.ok) {
        setChecklistMeta(res.checklist || null);
      }
    });
  }, [id, navigate]);

  const setField = (key, value) => setForm((p) => ({ ...p, [key]: value }));

  // Auto-preenche valor_cobrado a partir da tabela de preços (somente após carga inicial)
  useEffect(() => {
    if (!initialized.current || !form?.modelo || selectedReparos.length === 0) {
      setSuggestedPrice(null);
      return;
    }
    const tabela = form.tipo === "Upgrade" ? "ir_phones" : "clientes";
    precosApi.sugerir({
      modelo: form.modelo,
      reparo_ids: selectedReparos.join(","),
      tabela,
    }).then((res) => {
      if (res?.ok && res.encontrado) {
        setSuggestedPrice(res.valor);
        if (!form.valor_cobrado) {
          setForm((p) => ({ ...p, valor_cobrado: String(res.valor) }));
        }
      } else {
        setSuggestedPrice(null);
      }
    });
  }, [form?.modelo, form?.tipo, form?.valor_cobrado, selectedReparos]);

  const toggleReparo = (rid) => {
    setSelectedReparos((prev) => prev.includes(rid) ? prev.filter((x) => x !== rid) : [...prev, rid]);
  };

  const adjustPeca = (pid, delta) => {
    setPecas((prev) => {
      const next = Math.max(0, (prev[pid] || 0) + delta);
      if (next === 0) { const { [pid]: _, ...rest } = prev; return rest; }
      return { ...prev, [pid]: next };
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
        pecas_ids: Object.entries(pecas).flatMap(([k, v]) => Array.from({ length: v }, () => parseInt(k, 10))),
      };
      const res = await ordensApi.update(id, payload);
      if (res?.ok) {
        toast.success("Ordem atualizada!");
        navigate("/ordens");
      } else {
        toast.error(res?.erro || "Erro ao atualizar ordem");
      }
    } catch {
      toast.error("Erro ao atualizar ordem");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelOrder = async () => {
    try {
      const res = await ordensApi.patchStatus(id, "Cancelado");
      if (res?.ok) {
        toast.success("Ordem cancelada");
        navigate("/ordens");
      } else {
        toast.error(res?.erro || "Erro ao cancelar");
      }
    } catch {
      toast.error("Erro ao cancelar ordem");
    } finally {
      setCancelDialog(false);
    }
  };

  const handleFinalize = async () => {
    try {
      const res = await ordensApi.patchStatus(id, "Finalizado");
      if (res?.ok) {
        toast.success("Ordem finalizada!");
        navigate("/ordens");
      } else {
        toast.error(res?.erro || "Erro ao finalizar");
      }
    } catch {
      toast.error("Erro ao finalizar ordem");
    }
  };

  const handleChecklistQr = async () => {
    setChecklistLoading(true);
    try {
      const res = await checklistApi.generateToken(id);
      if (!res?.ok) {
        toast.error(res?.erro || "Nao foi possivel gerar o QR do checklist");
        return;
      }
      setChecklistMeta(res.checklist || null);
      setChecklistDialog(true);
    } catch {
      toast.error("Nao foi possivel gerar o QR do checklist");
    } finally {
      setChecklistLoading(false);
    }
  };

  const checklistLink = checklistMeta?.public_url || "";
  const checklistQr = checklistLink ? checklistApi.qrImageUrl(checklistLink) : "";

  const copyChecklistLink = async () => {
    if (!checklistLink) return;
    try {
      await navigator.clipboard.writeText(checklistLink);
      toast.success("Link do checklist copiado");
    } catch {
      toast.error("Nao foi possivel copiar o link");
    }
  };

  const normalizedModelo = form?.modelo?.toLowerCase().trim();
  const filteredEstoque = estoqueList.filter((item) => {
    const itemModelo = item.modelo?.toLowerCase().trim() || "";
    const matchesSearch = item.descricao?.toLowerCase().includes(stockSearch.toLowerCase()) || itemModelo.includes(stockSearch.toLowerCase());
    const matchesModelo = !normalizedModelo || itemModelo === "universal" || itemModelo === normalizedModelo;
    return matchesSearch && matchesModelo;
  });

  const pecasTotal = useMemo(() => {
    return Object.entries(pecas).reduce((sum, [id, quantity]) => {
      const estoqueItem = estoqueList.find((item) => String(item.id) === String(id));
      return sum + (estoqueItem?.valor || 0) * (quantity || 0);
    }, 0);
  }, [pecas, estoqueList]);

  const reparosDisponiveis = useMemo(() => {
    return [...reparosList]
      .filter((reparo) => {
        const nome = (reparo?.nome || "").trim().toLowerCase();
        return nome && !["nao informado", "não informado", "analise", "análise"].includes(nome);
      })
      .sort((a, b) => (a.nome || "").localeCompare(b.nome || "", "pt-BR"));
  }, [reparosList]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Editar Ordem #{String(id).slice(-5)}</h1>
          <p className="text-muted-foreground text-sm">Atualize os dados da OS</p>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="outline" onClick={handleChecklistQr} disabled={checklistLoading}>
            {checklistLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <QrCode className="mr-2 h-4 w-4" />}
            Checklist QR
          </Button>
          <Button type="button" variant="outline" onClick={handleFinalize}>Finalizar OS</Button>
          <Button type="button" variant="destructive" onClick={() => setCancelDialog(true)}>Cancelar OS</Button>
        </div>
      </div>

      {checklistMeta ? (
        <section className="rounded-xl border border-border bg-card p-4 space-y-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div>
              <h2 className="text-sm font-semibold text-card-foreground">Checklist do aparelho</h2>
              <p className="text-sm text-muted-foreground">
                Touch: {checklistMeta.status_touch} • Audio: {checklistMeta.status_audio} • Microfone: {checklistMeta.status_microfone}
              </p>
            </div>
            <Button type="button" variant="outline" onClick={() => setChecklistDialog(true)} disabled={!checklistMeta.access_token}>
              Ver QR
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            {checklistMeta.atualizado_em
              ? `Ultima atualizacao: ${checklistMeta.atualizado_em}`
              : "Checklist ainda nao preenchido."}
          </p>
        </section>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Cliente / Tipo */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Cliente</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2 space-y-1.5">
              <Label htmlFor="edit-order-cliente">Nome do Cliente *</Label>
              <Input id="edit-order-cliente" value={form.cliente} onChange={(e) => setField("cliente", e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label>Tipo de OS</Label>
              <Select value={form.tipo} onValueChange={(v) => setField("tipo", v)}>
                <SelectTrigger aria-label="Tipo de OS"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(constants?.os_tipos || ["Assistencia", "Garantia", "Upgrade"]).map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-order-data-os">Data da OS</Label>
              <Input id="edit-order-data-os" type="date" value={form.data_os} onChange={(e) => setField("data_os", e.target.value)} />
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
                <SelectTrigger aria-label="Modelo"><SelectValue placeholder="Selecione o modelo" /></SelectTrigger>
                <SelectContent>
                  {/* Garante que o modelo atual apareça mesmo se não estiver na lista */}
                  {(!constants?.iphone_models?.includes(form.modelo) && form.modelo) && (
                    <SelectItem key={form.modelo} value={form.modelo}>{form.modelo}</SelectItem>
                  )}
                  {(constants?.iphone_models || []).map((m) => (
                    <SelectItem key={m} value={m}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Cor</Label>
              <Select value={form.cor} onValueChange={(v) => setField("cor", v)}>
                <SelectTrigger aria-label="Cor"><SelectValue placeholder="Cor do aparelho" /></SelectTrigger>
                <SelectContent>
                  {/* Garante que a cor atual apareça mesmo se não estiver na lista */}
                  {(!constants?.iphone_colors?.[form.modelo]?.includes(form.cor) && form.cor) && (
                    <SelectItem key={form.cor} value={form.cor}>{form.cor}</SelectItem>
                  )}
                  {(constants?.iphone_colors?.[form.modelo] || []).map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="col-span-2 space-y-1.5">
              <Label htmlFor="edit-order-imei">IMEI</Label>
              <Input id="edit-order-imei" value={form.imei} onChange={(e) => setField("imei", e.target.value)} maxLength={16} />
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
                <SelectTrigger aria-label="Técnico"><SelectValue placeholder="Selecione" /></SelectTrigger>
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
                <SelectTrigger aria-label="Vendedor"><SelectValue placeholder="Selecione" /></SelectTrigger>
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
                <SelectTrigger aria-label="Status"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(constants?.status_opcoes || ["Em andamento", "Aguardando peca", "Finalizado", "Cancelado"]).map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {reparosDisponiveis.length > 0 && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <Label>Tipos de Reparo</Label>
                <span className="text-xs text-muted-foreground">{selectedReparos.length} selecionado(s)</span>
              </div>
              <div className="rounded-xl border border-border/70 bg-secondary/30 p-3">
                <div className="grid max-h-56 grid-cols-1 gap-2 overflow-y-auto pr-1 sm:grid-cols-2 xl:grid-cols-3">
                  {reparosDisponiveis.map((r) => {
                    const selecionado = selectedReparos.includes(r.id);
                    return (
                      <label
                        key={r.id}
                        className={[
                          "group flex cursor-pointer items-center gap-2 rounded-lg border px-2.5 py-2 text-sm transition-colors",
                          selecionado
                            ? "border-rose-500/60 bg-rose-500/10"
                            : "border-border/70 bg-background/50 hover:border-rose-500/40 hover:bg-background",
                        ].join(" ")}
                      >
                        <Checkbox
                          checked={selecionado}
                          onCheckedChange={() => toggleReparo(r.id)}
                          className="border-rose-500/80 data-[state=checked]:border-rose-500 data-[state=checked]:bg-rose-500"
                        />
                        <span className="font-medium uppercase tracking-wide text-card-foreground">{r.nome}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Financeiro */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Financeiro</h2>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <div className="bg-secondary rounded-xl p-4">
              <p className="text-xs uppercase font-semibold tracking-[0.2em] text-muted-foreground">Custo total de peças</p>
              <p className="mt-3 text-2xl font-bold text-foreground">{formatCurrency(pecasTotal)}</p>
            </div>
            <div className="bg-secondary rounded-xl p-4">
              <p className="text-xs uppercase font-semibold tracking-[0.2em] text-muted-foreground">Sugestão de serviço</p>
              <p className="mt-3 text-2xl font-bold text-rose-500">{suggestedPrice !== null ? formatCurrency(suggestedPrice) : "—"}</p>
              <p className="mt-1 text-xs text-muted-foreground">Baseado na tabela de preços.</p>
            </div>
            <div className="flex items-end justify-end">
              <Button type="button" disabled={!suggestedPrice} onClick={() => suggestedPrice !== null && setField("valor_cobrado", String(suggestedPrice))}>
                Usar sugestão
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="edit-order-valor-cobrado">Valor Cobrado (R$)</Label>
              <Input id="edit-order-valor-cobrado" type="number" step="0.01" min="0" value={form.valor_cobrado} onChange={(e) => setField("valor_cobrado", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-order-valor-descontado">Valor com Desconto (R$)</Label>
              <Input id="edit-order-valor-descontado" type="number" step="0.01" min="0" value={form.valor_descontado} onChange={(e) => setField("valor_descontado", e.target.value)} />
            </div>
          </div>
        </section>

        {/* Peças */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Peças do Estoque</h2>
          <div className="relative">
            <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Buscar peça..." value={stockSearch} onChange={(e) => setStockSearch(e.target.value)} className="pl-8" />
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {filteredEstoque.map((item) => (
              <div key={item.id} className="flex items-center justify-between bg-secondary rounded-lg px-3 py-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-card-foreground truncate">{item.descricao}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.modelo} • Estoque: {item.quantidade} • {formatCurrency(item.valor || 0)}
                  </p>
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
            ))}
          </div>
        </section>

        {/* Observações */}
        <section className="bg-card rounded-xl border border-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-card-foreground">Observações</h2>
          <Textarea value={form.observacoes} onChange={(e) => setField("observacoes", e.target.value)} />
        </section>

        <div className="flex gap-3">
          <Button type="submit" disabled={submitting} data-testid="order-save-button">
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Salvar Alterações
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate("/ordens")}>Voltar</Button>
        </div>
      </form>

      <AlertDialog open={cancelDialog} onOpenChange={setCancelDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancelar Ordem?</AlertDialogTitle>
            <AlertDialogDescription>A ordem será marcada como Cancelada. Deseja continuar?</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction onClick={handleCancelOrder} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Confirmar Cancelamento
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={checklistDialog} onOpenChange={setChecklistDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Checklist por QR Code</DialogTitle>
            <DialogDescription>
              Abra no celular do cliente ou tecnico para testar touch, audio, microfone, camera e botoes.
            </DialogDescription>
          </DialogHeader>

          {checklistMeta?.access_token ? (
            <div className="space-y-4">
              <div className="rounded-2xl border border-border bg-background p-4 flex justify-center">
                <img src={checklistQr} alt="QR code do checklist" className="h-60 w-60 rounded-lg" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="checklist-link">Link publico</Label>
                <Input id="checklist-link" value={checklistLink} readOnly />
              </div>
              <div className="rounded-xl border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
                Ultima atualizacao: {checklistMeta.atualizado_em || "ainda nao preenchido"}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Gere o token para exibir o checklist.</p>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={copyChecklistLink} disabled={!checklistMeta?.access_token}>
              <Copy className="mr-2 h-4 w-4" />
              Copiar link
            </Button>
            <Button type="button" asChild disabled={!checklistMeta?.access_token}>
                <a href={checklistLink} target="_blank" rel="noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                Abrir checklist
              </a>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
