import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Search, ScanBarcode, Smartphone, MapPin, BatteryMedium, History } from "lucide-react";
import { unidadesSerializadas as unidadesApi } from "@/api/client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";

// Estados alcançáveis nesta sprint — mesmo domínio de `TRANSICOES_VALIDAS`
// em irflow_unidades_serializadas_service.py. 'reservado'/'vendido' existem
// no schema mas não são produzidos por nenhum fluxo ainda (aguardam Vendas).
const STATUS_BADGE = {
  disponivel: { label: "Disponível", className: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
  em_reparo: { label: "Em Reparo", className: "bg-amber-500/10 text-amber-300 border-amber-500/30" },
  devolvido: { label: "Devolvido", className: "bg-sky-500/10 text-sky-300 border-sky-500/30" },
  reservado: { label: "Reservado", className: "bg-fuchsia-500/10 text-fuchsia-300 border-fuchsia-500/30" },
  vendido: { label: "Vendido", className: "bg-zinc-500/10 text-zinc-300 border-zinc-500/30" },
};

const ORIGEM_BADGE = {
  estoque: { label: "Estoque", className: "bg-blue-500/10 text-blue-300 border-blue-500/30" },
  produto: { label: "Produto", className: "bg-purple-500/10 text-purple-300 border-purple-500/30" },
};

function statusBadge(status) {
  return STATUS_BADGE[status] || { label: status || "—", className: "bg-secondary/70 text-muted-foreground border-border" };
}

function origemBadge(tipo) {
  return ORIGEM_BADGE[tipo] || { label: "—", className: "bg-secondary/70 text-muted-foreground border-border" };
}

function formatDate(value) {
  if (!value) return "—";
  // criado_em vem como "YYYY-MM-DD HH:MM:SS" (datetime('now') do SQLite)
  const [data] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : value;
}

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  const horaCurta = (hora || "").slice(0, 5);
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${horaCurta}`.trim() : value;
}

const ACAO_LABEL = {
  create: "Unidade cadastrada",
  status_change: "Mudança de status",
};

function eventoDescricao(evento) {
  if (evento.acao === "status_change") {
    const de = STATUS_BADGE[evento.valor_anterior]?.label || evento.valor_anterior || "—";
    const para = STATUS_BADGE[evento.valor_novo]?.label || evento.valor_novo || "—";
    return `${de} → ${para}`;
  }
  return null;
}

function DetalheUnidade({ unidadeId, onClose }) {
  const [loading, setLoading] = useState(true);
  const [unidade, setUnidade] = useState(null);
  const [historico, setHistorico] = useState([]);

  useEffect(() => {
    let ativo = true;
    Promise.all([unidadesApi.get(unidadeId), unidadesApi.historico(unidadeId)]).then(([uRes, hRes]) => {
      if (!ativo) return;
      if (uRes?.ok) setUnidade(uRes.unidade);
      else toast.error(uRes?.erro || "Erro ao carregar unidade");
      setHistorico(hRes?.ok ? (hRes.historico || []) : []);
    }).finally(() => { if (ativo) setLoading(false); });
    return () => { ativo = false; };
  }, [unidadeId]);

  const origem = origemBadge(unidade?.origem_tipo);
  const status = statusBadge(unidade?.status);

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Smartphone className="h-5 w-5 text-primary" />
            {loading ? "Carregando..." : (unidade?.origem_label || "Unidade")}
          </DialogTitle>
          <DialogDescription>Detalhes da unidade serializada — IMEI, status e histórico</DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center h-24">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          </div>
        ) : !unidade ? (
          <p className="text-sm text-muted-foreground">Unidade não encontrada.</p>
        ) : (
          <div className="space-y-5 mt-2">
            <div className="grid grid-cols-2 gap-3 bg-secondary/40 rounded-lg p-4">
              <div className="col-span-2">
                <p className="text-xs text-muted-foreground uppercase tracking-wider">IMEI / Serial</p>
                <p className="font-mono text-card-foreground">{unidade.imei || "—"}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Origem</p>
                <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium mt-0.5", origem.className].join(" ")}>
                  {origem.label}
                </span>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Status</p>
                <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium mt-0.5", status.className].join(" ")}>
                  {status.label}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <BatteryMedium className="h-4 w-4 text-muted-foreground shrink-0" />
                <span className="text-card-foreground text-sm">
                  {unidade.saude_bateria != null ? `${unidade.saude_bateria}% de saúde` : "Saúde da bateria não registrada"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground shrink-0" />
                <span className="text-card-foreground text-sm">{unidade.localizacao || "Localização não registrada"}</span>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Cadastrado em</p>
                <p className="text-card-foreground text-sm">{formatDate(unidade.criado_em)}</p>
              </div>
            </div>

            {/* Campos que dependem do módulo de Vendas — ainda não existe */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Cliente atual</p>
                <p className="text-sm text-muted-foreground bg-secondary/40 rounded-lg p-3">Sem venda registrada — módulo de Vendas em construção.</p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Garantia</p>
                <p className="text-sm text-muted-foreground bg-secondary/40 rounded-lg p-3">Não aplicável ainda — depende da venda.</p>
              </div>
            </div>

            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <History className="h-3.5 w-3.5" /> Histórico {historico.length > 0 && `(${historico.length})`}
              </p>
              {historico.length === 0 ? (
                <p className="text-sm text-muted-foreground bg-secondary/40 rounded-lg p-3">Nenhum evento registrado.</p>
              ) : (
                <div className="space-y-1.5">
                  {historico.map((evento) => (
                    <div key={evento.id} className="flex items-center justify-between text-sm bg-secondary/40 rounded-lg px-3 py-2">
                      <div>
                        <span className="text-card-foreground font-medium">{ACAO_LABEL[evento.acao] || evento.acao}</span>
                        {eventoDescricao(evento) && (
                          <span className="text-muted-foreground ml-2">{eventoDescricao(evento)}</span>
                        )}
                      </div>
                      <div className="text-muted-foreground text-xs text-right">
                        {evento.usuario_nome && <div>{evento.usuario_nome}</div>}
                        <div>{formatDateTime(evento.criado_em)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <DialogFooter className="mt-4">
          <Button type="button" variant="outline" onClick={onClose}>Fechar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function UnidadesSerializadas() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [detalheId, setDetalheId] = useState(null);

  const fetchItems = async () => {
    setLoading(true);
    try {
      // per_page alto: mesmo padrão de Produtos.jsx — busca combinada
      // (IMEI + origem/modelo) é feita client-side sobre a página carregada.
      const res = await unidadesApi.list({ per_page: 500 });
      if (res?.ok) setItems(res.items || []);
      else toast.error(res?.erro || "Erro ao carregar unidades");
    } catch {
      toast.error("Erro ao carregar unidades");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const filtered = items.filter((item) => {
    const termo = search.trim().toLowerCase();
    if (!termo) return true;
    const haystack = [item.imei, item.origem_label, item.produto_categoria, item.produto_marca, item.status]
      .filter(Boolean).join(" ").toLowerCase();
    const tokens = termo.split(/\s+/);
    return tokens.every((t) => haystack.includes(t));
  });

  const totalUnidades = items.length;
  const totalDisponiveis = items.filter((i) => i.status === "disponivel").length;
  const totalEmReparo = items.filter((i) => i.status === "em_reparo").length;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Unidades Serializadas</h1>
          <p className="text-muted-foreground text-sm">
            Localize qualquer aparelho da loja por IMEI, modelo ou produto
          </p>
        </div>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {[
          { label: "Unidades", value: totalUnidades, color: "text-foreground" },
          { label: "Disponíveis", value: totalDisponiveis, color: "text-emerald-400" },
          { label: "Em Reparo", value: totalEmReparo, color: "text-amber-400" },
        ].map((s) => (
          <div key={s.label} className="bg-card border border-border rounded-xl p-4">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Busca */}
      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por IMEI, modelo ou produto..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="ml-auto flex items-center text-xs text-muted-foreground">
          {filtered.length} {filtered.length === 1 ? "unidade" : "unidades"} exibidas
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          {search ? (
            "Nenhuma unidade corresponde à busca atual."
          ) : (
            <div className="flex flex-col items-center gap-2">
              <ScanBarcode className="h-8 w-8 text-muted-foreground/50" />
              Nenhuma unidade serializada cadastrada ainda.
            </div>
          )}
        </div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["IMEI", "Origem", "Status", "Localização", "Cadastrado em"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((item) => {
                  const origem = origemBadge(item.origem_tipo);
                  const status = statusBadge(item.status);
                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-accent/30 transition-colors cursor-pointer"
                      data-testid={`unidade-row-${item.id}`}
                      onClick={() => setDetalheId(item.id)}
                    >
                      <td className="px-4 py-3">
                        <span className="font-medium text-card-foreground font-mono">{item.imei || "—"}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", origem.className].join(" ")}>
                            {origem.label}
                          </span>
                          <span className="text-muted-foreground text-xs">{item.origem_label || "—"}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", status.className].join(" ")}>
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{item.localizacao || "—"}</td>
                      <td className="px-4 py-3 text-muted-foreground">{formatDate(item.criado_em)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {detalheId && <DetalheUnidade unidadeId={detalheId} onClose={() => setDetalheId(null)} />}
    </div>
  );
}
