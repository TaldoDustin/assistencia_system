import React, { useEffect, useState } from "react";
import EditShoppingItemModal from "@/components/ui/EditShoppingItemModal";
import { shoppingList } from "@/api/client";

export default function Compras() {
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(false);

  async function load() {
    try {
      const data = await shoppingList.list();
      if (data?.ok) setItems(data.compras || []);
    } catch (err) {
      console.error("Erro carregando lista de compras:", err);
    }
  }

  useEffect(() => {
    async function carregarInicial() {
      await load();
    }
    carregarInicial();
  }, []);

  function handleEdit(item) {
    setEditing(item);
    setOpen(true);
  }

  function handleSaved() {
    setOpen(false);
    setEditing(null);
    load();
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Lista de Compras</h2>
      <div className="overflow-x-auto bg-card rounded p-4">
        <table className="w-full text-left">
          <thead className="text-sm text-muted-foreground">
            <tr>
              <th>Produto</th>
              <th>Equipamento (OS)</th>
              <th>Quantidade</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id} className="border-t border-border">
                <td className="py-2">{it.produto}</td>
                <td className="py-2">{it.os_numero || it.os_id || "—"}</td>
                <td className="py-2">{it.quantidade}</td>
                <td className="py-2">{it.status}</td>
                <td className="py-2">
                  <button className="rounded bg-primary px-2 py-1 text-white text-sm" onClick={() => handleEdit(it)}>Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <EditShoppingItemModal open={open} onClose={() => setOpen(false)} item={editing} onSaved={handleSaved} />
    </div>
  );
}
