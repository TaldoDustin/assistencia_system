import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { STATUS_OPTIONS, OS_TYPES } from "@/lib/constants";

export default function OrderFilters({ filters, setFilters, tecnicos = [], vendedores = [] }) {
  const update = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="bg-card rounded-xl border border-border p-4 flex flex-wrap gap-3">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar cliente, modelo, IMEI..."
          value={filters.search || ""}
          onChange={(e) => update("search", e.target.value)}
          className="pl-8"
        />
      </div>

      <Select value={filters.status || ""} onValueChange={(v) => update("status", v === "all" ? "" : v)}>
        <SelectTrigger className="w-44">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos os status</SelectItem>
          {STATUS_OPTIONS.map((s) => (
            <SelectItem key={s} value={s}>{s}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={filters.tipo || ""} onValueChange={(v) => update("tipo", v === "all" ? "" : v)}>
        <SelectTrigger className="w-36">
          <SelectValue placeholder="Tipo" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos os tipos</SelectItem>
          {OS_TYPES.map((t) => (
            <SelectItem key={t} value={t}>{t}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {tecnicos.length > 0 && (
        <Select value={filters.tecnico || ""} onValueChange={(v) => update("tecnico", v === "all" ? "" : v)}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Técnico" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos técnicos</SelectItem>
            {tecnicos.map((t) => (
              <SelectItem key={t} value={t}>{t}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {vendedores.length > 0 && (
        <Select value={filters.vendedor || ""} onValueChange={(v) => update("vendedor", v === "all" ? "" : v)}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Vendedor" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos vendedores</SelectItem>
            {vendedores.map((v) => (
              <SelectItem key={v} value={v}>{v}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
}
