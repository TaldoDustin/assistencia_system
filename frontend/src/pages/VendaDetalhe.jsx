import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, ArrowLeft, Printer, UserCircle, CreditCard, Calendar, FileText } from "lucide-react";
import { vendas as vendasApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/constants";

const FORMA_PAGAMENTO_LABEL = {
  pix: "Pix",
  cartao: "Cartão",
  dinheiro: "Dinheiro",
  transferencia: "Transferência",
};

const STATUS_BADGE = {
  concluida: { label: "Concluída", className: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
};

function statusBadge(status) {
  return STATUS_BADGE[status] || { label: status || "—", className: "bg-secondary/70 text-muted-foreground border-border" };
}

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  const horaCurta = (hora || "").slice(0, 5);
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${horaCurta}`.trim() : value;
}

// Estrutura pensada para ser reaproveitada como recibo quando a feature de
// Imprimir (V1.8 do roadmap) existir — por isso as seções (cabeçalho,
// cliente/vendedor/pagamento, itens, total) já ficam isoladas e limpas, sem
// nada específico de tela que atrapalharia virar impresso depois.
export default function VendaDetalhe() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [venda, setVenda] = useState(null);
  const [itens, setItens] = useState([]);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    let ativo = true;

    async function carregar() {
      setLoading(true);
      try {
        const res = await vendasApi.get(id);
        if (!ativo) return;
        if (res?.ok) {
          setVenda(res.venda);
          setItens(res.itens || []);
        } else {
          setErro(res?.erro || "Venda não encontrada");
        }
      } catch {
        if (ativo) setErro("Erro ao carregar venda");
      } finally {
        if (ativo) setLoading(false);
      }
    }

    carregar();
    return () => { ativo = false; };
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (erro || !venda) {
    return (
      <div className="space-y-4 max-w-2xl">
        <Button variant="outline" size="sm" onClick={() => navigate("/vendas")}>
          <ArrowLeft className="h-4 w-4 mr-2" />Voltar
        </Button>
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          {erro || "Venda não encontrada."}
        </div>
      </div>
    );
  }

  const status = statusBadge(venda.status);

  return (
    <div className="space-y-5 max-w-3xl">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <Button variant="outline" size="sm" onClick={() => navigate("/vendas")}>
          <ArrowLeft className="h-4 w-4 mr-2" />Voltar
        </Button>
        <Button variant="outline" size="sm" onClick={() => toast.info("Impressão ainda não disponível — em breve.")}>
          <Printer className="h-4 w-4 mr-2" />Imprimir
        </Button>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 space-y-5">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-xl font-bold text-foreground">Venda #{venda.id}</h1>
            <p className="text-muted-foreground text-sm flex items-center gap-1.5 mt-0.5">
              <Calendar className="h-3.5 w-3.5" />{formatDateTime(venda.criado_em)}
            </p>
          </div>
          <span className={["inline-flex rounded-full border px-2.5 py-1 text-xs font-medium", status.className].join(" ")}>
            {status.label}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-secondary/40 rounded-lg p-4">
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <UserCircle className="h-3.5 w-3.5" />Cliente
            </p>
            <p className="text-sm font-medium text-card-foreground mt-0.5">{venda.cliente_nome || "—"}</p>
            {venda.cliente_telefone && <p className="text-xs text-muted-foreground">{venda.cliente_telefone}</p>}
          </div>
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Vendedor</p>
            <p className="text-sm font-medium text-card-foreground mt-0.5">{venda.vendedor_nome || "—"}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <CreditCard className="h-3.5 w-3.5" />Pagamento
            </p>
            <p className="text-sm font-medium text-card-foreground mt-0.5">
              {FORMA_PAGAMENTO_LABEL[venda.forma_pagamento] || venda.forma_pagamento || "—"}
            </p>
          </div>
        </div>

        {venda.observacoes && (
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5" />Observações
            </p>
            <p className="text-sm text-card-foreground bg-secondary/40 rounded-lg p-3">{venda.observacoes}</p>
          </div>
        )}

        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
            Itens {itens.length > 0 && `(${itens.length})`}
          </p>
          <div className="border border-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-secondary/40">
                    {["Produto", "IMEI", "SKU", "Valor de tabela", "Valor vendido", "Desconto", "Total"].map((h) => (
                      <th key={h} className="text-left px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {itens.map((item) => (
                    <tr key={item.id}>
                      <td className="px-3 py-2 font-medium text-card-foreground">{item.produto_nome}</td>
                      <td className="px-3 py-2 text-muted-foreground font-mono">{item.imei || "—"}</td>
                      <td className="px-3 py-2 text-muted-foreground">{item.produto_sku || "—"}</td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {item.valor_tabela != null ? formatCurrency(item.valor_tabela) : "—"}
                      </td>
                      <td className="px-3 py-2 text-card-foreground">{formatCurrency(item.valor_unitario)}</td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {item.desconto != null ? formatCurrency(item.desconto) : "—"}
                      </td>
                      <td className="px-3 py-2 font-medium text-card-foreground">{formatCurrency(item.subtotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-border">
          <span className="text-sm text-muted-foreground">Total da venda</span>
          <span className="text-lg font-bold text-foreground">{formatCurrency(venda.valor_total)}</span>
        </div>
      </div>
    </div>
  );
}
