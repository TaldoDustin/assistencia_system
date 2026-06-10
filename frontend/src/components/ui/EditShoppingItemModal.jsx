import React, { useState, useEffect } from "react";

export default function EditShoppingItemModal({ open, onClose, item, onSaved }) {
  const [osId, setOsId] = useState(item?.os_id || "");
  const [quantidade, setQuantidade] = useState(item?.quantidade || 1);
  const [status, setStatus] = useState(item?.status || "");

  useEffect(() => {
    if (item) {
      setOsId(item.os_id || "");
      setQuantidade(item.quantidade || 1);
      setStatus(item.status || "");
    }
  }, [item]);

  if (!open) return null;

  async function handleSave(e) {
    e.preventDefault();
    const body = { os_id: Number(osId) || null, quantidade: Number(quantidade) || 1, status: status || item.status };
    try {
      const res = await fetch(`/api/shopping-list/${item.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.erro || "Erro ao salvar");
      if (onSaved) onSaved(data);
      onClose();
    } catch (err) {
      console.error("Erro ao atualizar item de compras:", err);
      alert("Erro ao salvar: " + err.message);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded bg-card p-6">
        <h3 className="mb-4 text-lg font-semibold">Editar item da Lista de Compras</h3>
        <form onSubmit={handleSave} className="space-y-4">
          <label className="block">
            <div className="text-sm text-muted-foreground">Equipamento (OS) - ID interno</div>
            <input type="number" value={osId} onChange={(e)=>setOsId(e.target.value)} className="mt-1 w-full rounded border px-2 py-1" />
          </label>
          <label className="block">
            <div className="text-sm text-muted-foreground">Quantidade</div>
            <input type="number" min="1" value={quantidade} onChange={(e)=>setQuantidade(e.target.value)} className="mt-1 w-full rounded border px-2 py-1" />
          </label>
          <label className="block">
            <div className="text-sm text-muted-foreground">Status</div>
            <input type="text" value={status} onChange={(e)=>setStatus(e.target.value)} className="mt-1 w-full rounded border px-2 py-1" />
          </label>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded border px-3 py-1">Cancelar</button>
            <button type="submit" className="rounded bg-primary px-3 py-1 text-white">Salvar</button>
          </div>
        </form>
      </div>
    </div>
  );
}
