import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Search, ScanBarcode, Smartphone, MapPin, BatteryMedium, History, ChevronLeft, ChevronRight, Pencil } from "lucide-react";
import { unidadesSerializadas as unidadesApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";

// Mesma máquina de estados de TRANSICOES_VALIDAS em
// fluxoly_unidades_serializadas_service.py — usada só para popular o select
// de status no modo de edição (o backend valida de novo, esta cópia é só UX).
const TRANSICOES_VALIDAS = {
  disponivel: ["em_reparo"],
  em_reparo: ["disponivel", "devolvido"],
  devolvido: ["disponivel"],
};

// Estados alcançáveis nesta sprint — mesmo domínio de `TRANSICOES_VALIDAS`
// em fluxoly_unidades_serializadas_service.py. 'reservado'/'vendido' existem
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

// Faixas de saúde da bateria e ordenação (C1.3.3) — espelham
// FAIXAS_SAUDE_BATERIA/_ORDENACOES do backend, só os rótulos são daqui.
const SAUDE_BATERIA_OPTIONS = [
  { value: "100-95", label: "100% – 95%" },
  { value: "94-90", label: "94% – 90%" },
  { value: "89-85", label: "89% – 85%" },
  { value: "<85", label: "Abaixo de 85%" },
  { value: "nao_informado", label: "Não informado" },
];

const SORT_OPTIONS = [
  { value: "recente", label: "Mais recente" },
  { value: "antigo", label: "Mais antigo" },
  { value: "imei", label: "IMEI" },
  { value: "modelo", label: "Modelo" },
  { value: "status", label: "Status" },
];

const PER_PAGE = 20;

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
  update: "Localização/bateria atualizada",
};

function eventoDescricao(evento) {
  if (evento.acao === "status_change") {
    const de = STATUS_BADGE[evento.valor_anterior]?.label || evento.valor_anterior || "—";
    const para = STATUS_BADGE[evento.valor_novo]?.label || evento.valor_novo || "—";
    return `${de} → ${para}`;
  }
  if (evento.acao === "update") {
    try {
      const depois = JSON.parse(evento.valor_novo);
      const partes = [];
      if (depois.localizacao) partes.push(`localização: ${depois.localizacao}`);
      if (depois.saude_bateria) partes.push(`bateria: ${depois.saude_bateria}%`);
      return partes.join(", ") || null;
    } catch {
      return null;
    }
  }
  return null;
}

const EMPTY_EDIT_FORM = { localizacao: "", saude_bateria: "", status: "" };

// Modal único para visualizar e editar uma unidade — evita duplicar a
// estrutura (IMEI/origem/status/bateria/localização/histórico) entre uma
// tela de "detalhe" e uma de "edição" separadas. `editing` alterna entre
// texto somente-leitura e campos de formulário para os mesmos dados.
function DetalheUnidade({ unidadeId, onClose, canEdit }) {
  const [loading, setLoading] = useState(true);
  const [unidade, setUnidade] = useState(null);
  const [historico, setHistorico] = useState([]);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(EMPTY_EDIT_FORM);
  const [submitting, setSubmitting] = useState(false);

  const carregar = () => {
    setLoading(true);
    return Promise.all([unidadesApi.get(unidadeId), unidadesApi.historico(unidadeId)]).then(([uRes, hRes]) => {
      if (uRes?.ok) setUnidade(uRes.unidade);
      else toast.error(uRes?.erro || "Erro ao carregar unidade");
      setHistorico(hRes?.ok ? (hRes.historico || []) : []);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadeId]);

  const origem = origemBadge(unidade?.origem_tipo);
  const status = statusBadge(unidade?.status);
  const transicoesDisponiveis = unidade ? (TRANSICOES_VALIDAS[unidade.status] || []) : [];

  const abrirEdicao = () => {
    setForm({
      localizacao: unidade.localizacao || "",
      saude_bateria: unidade.saude_bateria || "",
      status: unidade.status || "",
    });
    setEditing(true);
  };

  const salvar = async () => {
    setSubmitting(true);
    try {
      if (form.status && form.status !== unidade.status) {
        const resStatus = await unidadesApi.updateStatus(unidadeId, form.status);
        if (!resStatus?.ok) {
          toast.error(resStatus?.erro || "Erro ao atualizar status");
          setSubmitting(false);
          return;
        }
      }
      const resCampos = await unidadesApi.update(unidadeId, {
        localizacao: form.localizacao,
        saude_bateria: form.saude_bateria,
      });
      if (!resCampos?.ok) {
        toast.error(resCampos?.erro || "Erro ao salvar alterações");
        return;
      }
      toast.success("Unidade atualizada!");
      setEditing(false);
      await carregar();
    } catch {
      toast.error("Erro ao salvar alterações");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Smartphone className="h-5 w-5 text-primary" />
            {loading ? "Carregando..." : (unidade?.origem_label || "Unidade")}
          </DialogTitle>
          <DialogDescription>
            {editing ? "Editando localização, saúde da bateria e status" : "Detalhes da unidade serializada — IMEI, status e histórico"}
          </DialogDescription>
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
                {editing && <p className="text-xs text-muted-foreground mt-0.5">Imutável após o cadastro</p>}
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Origem</p>
                <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium mt-0.5", origem.className].join(" ")}>
                  {origem.label}
                </span>
              </div>

              {editing ? (
                <div className="space-y-1.5">
                  <Label htmlFor="unidade-status">Status</Label>
                  <Select value={form.status} onValueChange={(v) => setForm((p) => ({ ...p, status: v }))}>
                    <SelectTrigger id="unidade-status" className="w-full" aria-label="Status"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value={unidade.status}>{statusBadge(unidade.status).label} (atual)</SelectItem>
                      {transicoesDisponiveis.map((s) => (
                        <SelectItem key={s} value={s}>{statusBadge(s).label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">Status</p>
                  <span className={["inline-flex rounded-full border px-2 py-0.5 text-xs font-medium mt-0.5", status.className].join(" ")}>
                    {status.label}
                  </span>
                </div>
              )}

              {editing ? (
                <div className="space-y-1.5">
                  <Label htmlFor="unidade-bateria">Saúde da bateria (%)</Label>
                  <Input
                    id="unidade-bateria" type="number" min="0" max="100"
                    value={form.saude_bateria}
                    onChange={(e) => setForm((p) => ({ ...p, saude_bateria: e.target.value }))}
                  />
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <BatteryMedium className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="text-card-foreground text-sm">
                    {unidade.saude_bateria != null && unidade.saude_bateria !== "" ? `${unidade.saude_bateria}% de saúde` : "Saúde da bateria não registrada"}
                  </span>
                </div>
              )}

              {editing ? (
                <div className="space-y-1.5">
                  <Label htmlFor="unidade-localizacao">Localização</Label>
                  <Input
                    id="unidade-localizacao"
                    placeholder="Ex.: Loja, Bancada, Gaveta 3..."
                    value={form.localizacao}
                    onChange={(e) => setForm((p) => ({ ...p, localizacao: e.target.value }))}
                  />
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="text-card-foreground text-sm">{unidade.localizacao || "Localização não registrada"}</span>
                </div>
              )}

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
          {editing ? (
            <>
              <Button type="button" variant="outline" onClick={() => setEditing(false)} disabled={submitting}>Cancelar</Button>
              <Button type="button" onClick={salvar} disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {submitting ? "Salvando..." : "Salvar"}
              </Button>
            </>
          ) : (
            <>
              <Button type="button" variant="outline" onClick={onClose}>Fechar</Button>
              {canEdit && unidade && (
                <Button type="button" onClick={abrirEdicao}>
                  <Pencil className="h-4 w-4 mr-2" /> Editar
                </Button>
              )}
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function UnidadesSerializadas() {
  const { user } = useAuth();
  const canEdit = user?.perfil === "admin" || user?.perfil === "tecnico";
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [detalheId, setDetalheId] = useState(null);

  // Campo de busca com debounce: o valor digitado (searchInput) só vira o
  // termo de busca de fato (search) 350ms depois de parar de digitar —
  // evita 1 requisição por tecla contra a API (C1.3.3: "busca rápida mesmo
  // com milhares de unidades").
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [origemFilter, setOrigemFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [saudeBateriaFaixa, setSaudeBateriaFaixa] = useState("");
  const [localizacaoInput, setLocalizacaoInput] = useState("");
  const [localizacao, setLocalizacao] = useState("");
  const [sort, setSort] = useState("recente");
  const [page, setPage] = useState(1);

  // Debounce da busca/localização: volta para a página 1 junto (dentro do
  // callback assíncrono do setTimeout, não sincronamente no corpo do efeito).
  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput); setPage(1); }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    const t = setTimeout(() => { setLocalizacao(localizacaoInput); setPage(1); }, 350);
    return () => clearTimeout(t);
  }, [localizacaoInput]);

  // Filtros de seleção (origem/status/faixa de bateria/ordenação) resetam a
  // página diretamente no handler, não via efeito reativo — mesma correção
  // já aplicada em Clientes.jsx (evita setState síncrono no corpo do efeito).
  const handleOrigemChange = (v) => { setOrigemFilter(v === "all" ? "" : v); setPage(1); };
  const handleStatusChange = (v) => { setStatusFilter(v === "all" ? "" : v); setPage(1); };
  const handleSaudeBateriaChange = (v) => { setSaudeBateriaFaixa(v === "all" ? "" : v); setPage(1); };
  const handleSortChange = (v) => { setSort(v); setPage(1); };

  useEffect(() => {
    let ativo = true;

    async function buscar() {
      setLoading(true);
      const params = { page, per_page: PER_PAGE, sort };
      if (search) params.q = search;
      if (origemFilter) params.origem = origemFilter;
      if (statusFilter) params.status = statusFilter;
      if (saudeBateriaFaixa) params.saude_bateria_faixa = saudeBateriaFaixa;
      if (localizacao) params.localizacao = localizacao;

      try {
        const res = await unidadesApi.list(params);
        if (!ativo) return;
        if (res?.ok) {
          setItems(res.items || []);
          setTotal(res.total || 0);
        } else {
          toast.error(res?.erro || "Erro ao carregar unidades");
        }
      } catch {
        if (ativo) toast.error("Erro ao carregar unidades");
      } finally {
        if (ativo) setLoading(false);
      }
    }

    buscar();
    return () => { ativo = false; };
  }, [page, search, origemFilter, statusFilter, saudeBateriaFaixa, localizacao, sort]);

  const totalPaginas = Math.max(1, Math.ceil(total / PER_PAGE));
  const filtrosAtivos = Boolean(search || origemFilter || statusFilter || saudeBateriaFaixa || localizacao);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Unidades Serializadas</h1>
          <p className="text-muted-foreground text-sm">
            Localize qualquer aparelho da loja por IMEI, serial, modelo, marca ou localização
          </p>
        </div>
      </div>

      {/* Card de resumo — reflete o resultado filtrado atual, não o total global
          (calcular Disponíveis/Em Reparo globais exigiria consultas extras a
          cada filtro, contra o critério de manter a busca rápida). */}
      <div className="bg-card border border-border rounded-xl p-4 w-fit min-w-[160px]">
        <p className="text-2xl font-bold text-foreground">{total}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {filtrosAtivos ? "unidades encontradas" : "unidades no total"}
        </p>
      </div>

      {/* Busca */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="relative">
          <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por IMEI, serial, modelo, marca ou localização..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap gap-3">
        <Select value={origemFilter || "all"} onValueChange={handleOrigemChange}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Origem" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as origens</SelectItem>
            <SelectItem value="estoque">Estoque</SelectItem>
            <SelectItem value="produto">Produto</SelectItem>
          </SelectContent>
        </Select>

        <Select value={statusFilter || "all"} onValueChange={handleStatusChange}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os status</SelectItem>
            {Object.entries(STATUS_BADGE).map(([value, { label }]) => (
              <SelectItem key={value} value={value}>{label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={saudeBateriaFaixa || "all"} onValueChange={handleSaudeBateriaChange}>
          <SelectTrigger className="w-48"><SelectValue placeholder="Saúde da bateria" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Qualquer saúde de bateria</SelectItem>
            {SAUDE_BATERIA_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="relative w-48">
          <MapPin className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Localização..."
            value={localizacaoInput}
            onChange={(e) => setLocalizacaoInput(e.target.value)}
            className="pl-8"
          />
        </div>

        <Select value={sort} onValueChange={handleSortChange}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Ordenar por" /></SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : items.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          {filtrosAtivos ? (
            "Nenhuma unidade corresponde à busca/filtros atuais."
          ) : (
            <div className="flex flex-col items-center gap-2">
              <ScanBarcode className="h-8 w-8 text-muted-foreground/50" />
              Nenhuma unidade serializada cadastrada ainda.
            </div>
          )}
        </div>
      ) : (
        <>
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
                  {items.map((item) => {
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

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Página {page} de {totalPaginas} — {total} {total === 1 ? "unidade" : "unidades"}</span>
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

      {detalheId && <DetalheUnidade unidadeId={detalheId} onClose={() => setDetalheId(null)} canEdit={canEdit} />}
    </div>
  );
}
