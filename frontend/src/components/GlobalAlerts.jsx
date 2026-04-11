import { useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { alertas as alertasApi } from "@/api/client";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";

const levelColor = {
  critico: "bg-red-500",
  atencao: "bg-amber-400",
  info: "bg-blue-400",
};

export default function GlobalAlerts() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    alertasApi.list().then((data) => {
      if (data?.ok && Array.isArray(data.alertas)) setAlerts(data.alertas);
    }).catch(() => {});
  }, []);

  if (alerts.length === 0) return null;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="relative flex items-center justify-center h-8 w-8 rounded-lg hover:bg-sidebar-accent transition-colors">
          <Bell className="h-4 w-4 text-sidebar-foreground/70" />
          <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center">
            {alerts.length > 9 ? "9+" : alerts.length}
          </span>
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-2">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2 py-1 mb-1">
          Alertas do sistema
        </p>
        <div className="space-y-1">
          {alerts.map((alert, i) => (
            <div key={i} className="flex items-start gap-2 px-2 py-1.5 rounded-lg hover:bg-accent">
              <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${levelColor[alert.nivel] || "bg-muted"}`} />
              <p className="text-sm text-popover-foreground">{alert.mensagem}</p>
            </div>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
