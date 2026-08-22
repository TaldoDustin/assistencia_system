import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { garantias as garantiasApi } from "@/api/client";
import { getOrderDisplayNumber } from "@/lib/constants";

function GarantiaBadge({ status, dias }) {
  const map = {
    vencida:   "bg-destructive/20 text-destructive border-destructive/30",
    vencendo:  "bg-warning/20 text-warning border-warning/30",
    ativa:     "bg-success/20 text-success border-success/30",
  };
  const label = status === "vencida" ? "Vencida" : status === "vencendo" ? `Vencendo (${dias}d)` : `${dias}d restantes`;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${map[status] || "bg-muted text-muted-foreground border-border"}`}>
      {label}
    </span>
  );
}

export default function Garantias() {
  const [garantias, setGarantias] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    garantiasApi.list().then((res) => {
      if (res?.ok) setGarantias(res.garantias || []);
      else toast.error("Erro ao carregar garantias");
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Garantias</h1>
        <p className="text-muted-foreground text-sm">Ordens finalizadas e seus prazos de garantia</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : garantias.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          Nenhuma garantia encontrada.
        </div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["OS", "Cliente", "Modelo", "Reparo", "Data Finalização", "Garantia"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {garantias.map((g, i) => {
                  // BR-062: uma linha por reparo -- mas ainda agrupável
                  // visualmente por OS (linhas consecutivas da mesma OS não
                  // repetem OS/Cliente/Modelo/Data, só o reparo e a garantia).
                  const mesmaOsDaAnterior = i > 0 && garantias[i - 1].id === g.id;
                  return (
                    <tr key={`${g.id}-${g.reparo_id}`} className="hover:bg-accent/30 transition-colors">
                      <td className="px-4 py-3">
                        {mesmaOsDaAnterior ? null : (
                          <Link to={`/ordens/editar/${g.id}`} className="font-mono text-xs text-primary hover:underline">
                            #{getOrderDisplayNumber(g)}
                          </Link>
                        )}
                      </td>
                      <td className="px-4 py-3 font-medium text-card-foreground">{mesmaOsDaAnterior ? "" : g.cliente}</td>
                      <td className="px-4 py-3 text-muted-foreground">{mesmaOsDaAnterior ? "" : g.modelo}</td>
                      <td className="px-4 py-3 text-muted-foreground text-xs max-w-[200px]">{g.reparos_texto || "—"}</td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                        {mesmaOsDaAnterior ? "" : (g.data_finalizado ? new Date(g.data_finalizado).toLocaleDateString("pt-BR") : "—")}
                      </td>
                      <td className="px-4 py-3">
                        <GarantiaBadge status={g.status_garantia} dias={g.dias_restantes} />
                      </td>
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
