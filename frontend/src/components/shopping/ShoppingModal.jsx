import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { shoppingList as shoppingApi, estoque as estoqueApi } from "@/api/client";
import { toast } from "sonner";

export default function ShoppingModal({ open, onOpenChange, osId, onCreated }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [produtoId, setProdutoId] = useState("");
  const [produtoNome, setProdutoNome] = useState("");
  const [quantidade, setQuantidade] = useState(1);
  const [prioridade, setPrioridade] = useState("NORMAL");
  const [observacao, setObservacao] = useState("");

  useEffect(() => {
    if (!open) return;
    estoqueApi.list().then((res) => {
      if (res?.ok) setProducts(res.items || []);
    }).catch(() => {});
  }, [open]);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      const payload = {
        os_id: osId,
        produto_id: produtoId || undefined,
        produto_nome: produtoNome || (produtoId ? undefined : ""),
        quantidade_solicitada: Number(quantidade) || 1,
        prioridade,
        observacao,
      };
      const res = await shoppingApi.create(payload);
      if (res?.ok) {
        toast.success("Peça adicionada à lista de compras");
        onCreated && onCreated(res.id);
        onOpenChange(false);
      } else {
        toast.error(res?.erro || "Erro ao adicionar peça");
      }
    } catch (err) {
      toast.error("Erro ao adicionar peça");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Adicionar à Lista de Compras</DialogTitle>
          <DialogDescription>Informe a peça, quantidade e prioridade.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div>
            <label className="block text-sm font-medium mb-1">Peça</label>
            <Select value={produtoId || ""} onValueChange={(v) => { setProdutoId(v); const p = products.find(x => String(x.id) === String(v)); if (p) setProdutoNome(p.descricao); }}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione uma peça" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Nenhuma (informar nome)</SelectItem>
                {products.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>{p.descricao}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input placeholder="Ou informe o nome da peça" value={produtoNome} onChange={(e) => setProdutoNome(e.target.value)} className="mt-2" />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Quantidade</label>
            <Input type="number" min={1} value={quantidade} onChange={(e) => setQuantidade(e.target.value)} />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Prioridade</label>
            <Select value={prioridade} onValueChange={(v) => setPrioridade(v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="URGENTE">URGENTE</SelectItem>
                <SelectItem value="ALTA">ALTA</SelectItem>
                <SelectItem value="NORMAL">NORMAL</SelectItem>
                <SelectItem value="BAIXA">BAIXA</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Observação</label>
            <Input value={observacao} onChange={(e) => setObservacao(e.target.value)} />
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>Fechar</Button>
            <Button type="submit" disabled={loading}>{loading ? 'Salvando...' : 'Adicionar'}</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
