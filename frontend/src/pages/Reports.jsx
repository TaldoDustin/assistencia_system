import { useState } from "react";
import { toast } from "sonner";
import { Loader2, Search, FileDown, Lock } from "lucide-react";
import { relatorios as relatoriosApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/constants";

const TABS = [
  { key: "irphones", label: "IR Phones" },
  { key: "tecnicos", label: "Técnicos" },
];

export default function Reports() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("irphones");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const isAdmin = user?.perfil === "admin";

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Lock className="h-10 w-10" />
        <p>Somente administradores podem acessar relatórios.</p>
      </div>
    );
  }

  const handleSearch = async () => {
    setLoading(true);
    setResults(null);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      const fn = activeTab === "irphones" ? relatoriosApi.irphones : relatoriosApi.tecnicos;
      const res = await fn(params);
      if (res?.ok) setResults(res);
      else toast.error(res?.erro || "Erro ao gerar relatório");
    } catch {
      toast.error("Erro ao gerar relatório");
    } finally {
      setLoading(false);
    }
  };

  const handleExportPdf = () => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const url = relatoriosApi.pdfUrl(activeTab, params);
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Relatórios</h1>
        <p className="text-muted-foreground text-sm">Geração de relatórios e análises</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-secondary p-1 rounded-lg w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); setResults(null); }}
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

      {/* Filters */}
      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap items-end gap-3">
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground">Data Inicial</label>
          <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-36" />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground">Data Final</label>
          <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-36" />
        </div>
        <Button onClick={handleSearch} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}
          Gerar Relatório
        </Button>
        {results && (
          <Button variant="outline" onClick={handleExportPdf}>
            <FileDown className="h-4 w-4 mr-2" />Exportar PDF
          </Button>
        )}
      </div>

      {/* Results */}
      {loading && (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      )}

      {results && activeTab === "irphones" && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: "Total OS", value: results.total_os ?? "—", isCurrency: false },
              { label: "Faturamento", value: formatCurrency(results.faturamento), isCurrency: true },
              { label: "Lucro", value: formatCurrency(results.lucro), isCurrency: true },
              { label: "Ticket Médio", value: formatCurrency(results.ticket_medio), isCurrency: true },
            ].map((s) => (
              <div key={s.label} className="bg-card border border-border rounded-xl p-4">
                <p className="text-xl font-bold text-card-foreground">{s.value}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>

          {/* Table */}
          {results.ordens && results.ordens.length > 0 && (
            <div className="bg-card rounded-xl border border-border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      {["#OS", "Cliente", "Modelo", "Técnico", "Status", "Data", "Valor"].map((h) => (
                        <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {results.ordens.map((os) => (
                      <tr key={os.id} className="hover:bg-accent/30">
                        <td className="px-4 py-2 font-mono text-xs text-muted-foreground">#{String(os.id).slice(-5)}</td>
                        <td className="px-4 py-2 text-card-foreground">{os.cliente}</td>
                        <td className="px-4 py-2 text-muted-foreground">{os.modelo}</td>
                        <td className="px-4 py-2 text-muted-foreground">{os.tecnico || "—"}</td>
                        <td className="px-4 py-2 text-muted-foreground">{os.status}</td>
                        <td className="px-4 py-2 text-muted-foreground whitespace-nowrap">{os.data_os ? new Date(os.data_os).toLocaleDateString("pt-BR") : "—"}</td>
                        <td className="px-4 py-2 font-medium text-card-foreground">{formatCurrency(os.valor_cobrado || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {results && activeTab === "tecnicos" && (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Técnico", "OS Finalizadas", "Faturamento", "Custo Peças", "Lucro"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(results.tecnicos || []).map((t) => (
                  <tr key={t.tecnico} className="hover:bg-accent/30">
                    <td className="px-4 py-3 font-medium text-card-foreground">{t.tecnico}</td>
                    <td className="px-4 py-3 text-muted-foreground">{t.os_finalizadas}</td>
                    <td className="px-4 py-3 text-card-foreground font-medium">{formatCurrency(t.faturamento)}</td>
                    <td className="px-4 py-3 text-red-400">{formatCurrency(t.custo_pecas)}</td>
                    <td className="px-4 py-3 text-emerald-400 font-medium">{formatCurrency(t.lucro)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
