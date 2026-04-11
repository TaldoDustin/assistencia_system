import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, Pencil } from "lucide-react";
import { ordens as ordensApi } from "@/api/client";
import OrderStatusBadge from "@/components/orders/OrderStatusBadge";

const COLUMNS = [
  { status: "Em andamento",    label: "Em Andamento",     color: "text-blue-400",    border: "border-blue-500/30",    bg: "bg-blue-500/5",    dragBg: "bg-blue-500/15" },
  { status: "Aguardando peca", label: "Aguardando Peça",  color: "text-amber-400",   border: "border-amber-500/30",   bg: "bg-amber-500/5",   dragBg: "bg-amber-500/15" },
  { status: "Finalizado",      label: "Finalizado",       color: "text-emerald-400", border: "border-emerald-500/30", bg: "bg-emerald-500/5", dragBg: "bg-emerald-500/15" },
  { status: "Cancelado",       label: "Cancelado",        color: "text-red-400",     border: "border-red-500/30",     bg: "bg-red-500/5",     dragBg: "bg-red-500/15" },
];

export default function Kanban() {
  const [ordens, setOrdens]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [dragOver, setDragOver] = useState(null); // column status being dragged over
  const dragging = useRef(null); // { id, fromStatus }

  useEffect(() => {
    ordensApi.list().then((res) => {
      if (res?.ok) setOrdens(res.ordens || []);
      else toast.error("Erro ao carregar ordens");
      setLoading(false);
    });
  }, []);

  const handleDragStart = (e, os) => {
    dragging.current = { id: os.id, fromStatus: os.status };
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e, colStatus) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOver(colStatus);
  };

  const handleDragLeave = () => setDragOver(null);

  const handleDrop = async (e, toStatus) => {
    e.preventDefault();
    setDragOver(null);
    if (!dragging.current) return;
    const { id, fromStatus } = dragging.current;
    dragging.current = null;
    if (fromStatus === toStatus) return;

    // Optimistic update
    setOrdens((prev) => prev.map((o) => o.id === id ? { ...o, status: toStatus } : o));
    try {
      const res = await ordensApi.patchStatus(id, toStatus);
      if (!res?.ok) {
        toast.error(res?.erro || "Erro ao mover OS");
        setOrdens((prev) => prev.map((o) => o.id === id ? { ...o, status: fromStatus } : o));
      }
    } catch {
      toast.error("Erro ao mover OS");
      setOrdens((prev) => prev.map((o) => o.id === id ? { ...o, status: fromStatus } : o));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Kanban</h1>
        <p className="text-muted-foreground text-sm">Arraste os cards para mover entre status</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {COLUMNS.map((col) => {
          const colOrdens = ordens.filter((o) => o.status === col.status);
          const isOver = dragOver === col.status;
          return (
            <div
              key={col.status}
              className={`rounded-xl border ${col.border} ${isOver ? col.dragBg : col.bg} p-3 flex flex-col min-h-[200px] transition-colors`}
              onDragOver={(e) => handleDragOver(e, col.status)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, col.status)}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className={`text-sm font-semibold ${col.color}`}>{col.label}</h3>
                <span className={`text-xs font-bold ${col.color} bg-card rounded-full px-2 py-0.5 border ${col.border}`}>
                  {colOrdens.length}
                </span>
              </div>
              <div className="space-y-2 overflow-y-auto max-h-[600px] flex-1">
                {colOrdens.length === 0 ? (
                  <p className={`text-muted-foreground text-xs text-center py-6 rounded-lg border-2 border-dashed ${col.border} ${isOver ? "opacity-100" : "opacity-50"}`}>
                    {isOver ? "Solte aqui" : "Nenhuma ordem"}
                  </p>
                ) : (
                  colOrdens.map((os) => (
                    <div
                      key={os.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, os)}
                      className="bg-card border border-border rounded-lg p-3 space-y-2 cursor-grab active:cursor-grabbing hover:border-primary/40 hover:shadow-md transition-all select-none"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-muted-foreground font-mono">#{String(os.id).slice(-5)}</p>
                          <p className="text-sm font-semibold text-card-foreground truncate">{os.cliente}</p>
                          <p className="text-xs text-muted-foreground">{os.modelo}</p>
                        </div>
                        <Link to={`/ordens/editar/${os.id}`} className="shrink-0" onClick={(e) => e.stopPropagation()}>
                          <Pencil className="h-3.5 w-3.5 text-muted-foreground hover:text-primary" />
                        </Link>
                      </div>
                      {os.tecnico && (
                        <p className="text-xs text-muted-foreground">👤 {os.tecnico}</p>
                      )}
                      {os.reparos && os.reparos.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {os.reparos.slice(0, 2).map((r, i) => (
                            <span key={i} className="text-xs bg-secondary text-secondary-foreground rounded px-1.5 py-0.5">
                              {r}
                            </span>
                          ))}
                          {os.reparos.length > 2 && (
                            <span className="text-xs text-muted-foreground">+{os.reparos.length - 2}</span>
                          )}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}