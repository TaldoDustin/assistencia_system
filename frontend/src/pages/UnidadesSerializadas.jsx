import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Search, ScanBarcode } from "lucide-react";
import { unidadesSerializadas as unidadesApi } from "@/api/client";
import { Input } from "@/components/ui/input";

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

export default function UnidadesSerializadas() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

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
                    <tr key={item.id} className="hover:bg-accent/30 transition-colors" data-testid={`unidade-row-${item.id}`}>
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
    </div>
  );
}
