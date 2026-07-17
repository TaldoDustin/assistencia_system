import { useState } from "react";
import { toast } from "sonner";
import { ShoppingCart } from "lucide-react";
import { PreviewBadge } from "@/components/ui/preview-badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { formatCurrency } from "@/lib/constants";
import { DEMO_APARELHOS, DEMO_FORMAS_PAGAMENTO, DEMO_CLIENTES_SUGERIDOS } from "@/lib/demoData";

export default function Vendas() {
  const [modeloSelecionado, setModeloSelecionado] = useState(DEMO_APARELHOS[0].modelo);
  const [cliente, setCliente] = useState(DEMO_CLIENTES_SUGERIDOS[0]);
  const [pagamento, setPagamento] = useState(DEMO_FORMAS_PAGAMENTO[0]);

  const aparelho = DEMO_APARELHOS.find((a) => a.modelo === modeloSelecionado) || DEMO_APARELHOS[0];

  const handleFinalizarVenda = () => {
    toast.info("Prévia comercial — módulo de Vendas em finalização. Nenhuma venda foi registrada.");
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Vendas</h1>
          <p className="text-muted-foreground text-sm">Check-out de balcão</p>
        </div>
        <PreviewBadge />
      </div>

      <div className="bg-card rounded-xl border border-border p-5 max-w-xl space-y-4">
        <div className="space-y-1.5">
          <Label>Aparelho</Label>
          <Select value={modeloSelecionado} onValueChange={setModeloSelecionado}>
            <SelectTrigger aria-label="Aparelho"><SelectValue /></SelectTrigger>
            <SelectContent>
              {DEMO_APARELHOS.map((a) => <SelectItem key={a.modelo} value={a.modelo}>{a.modelo}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label>IMEI</Label>
            <p className="font-mono text-sm text-muted-foreground px-3 py-2 rounded-md bg-secondary">{aparelho.imei}</p>
          </div>
          <div className="space-y-1.5">
            <Label>Preço</Label>
            <p className="text-lg font-semibold text-card-foreground px-3 py-2 rounded-md bg-secondary">{formatCurrency(aparelho.preco)}</p>
          </div>
        </div>

        <div className="space-y-1.5">
          <Label>Cliente</Label>
          <Select value={cliente} onValueChange={setCliente}>
            <SelectTrigger aria-label="Cliente"><SelectValue /></SelectTrigger>
            <SelectContent>
              {DEMO_CLIENTES_SUGERIDOS.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label>Forma de Pagamento</Label>
            <Select value={pagamento} onValueChange={setPagamento}>
              <SelectTrigger aria-label="Forma de Pagamento"><SelectValue /></SelectTrigger>
              <SelectContent>
                {DEMO_FORMAS_PAGAMENTO.map((f) => <SelectItem key={f} value={f}>{f}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Garantia</Label>
            <p className="text-sm text-muted-foreground px-3 py-2 rounded-md bg-secondary">{aparelho.garantiaDias} dias</p>
          </div>
        </div>

        <Button onClick={handleFinalizarVenda} className="w-full mt-2">
          <ShoppingCart className="h-4 w-4 mr-2" />
          Finalizar Venda
        </Button>
      </div>
    </div>
  );
}
