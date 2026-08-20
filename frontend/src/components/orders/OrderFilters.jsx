import { MagnifyingGlass } from "@phosphor-icons/react";
import { FilterBar, FilterSelect, FilterInput } from "@/components/ui/filter-bar";
import { STATUS_OPTIONS_FALLBACK, OS_TYPES_FALLBACK } from "@/lib/constants";

export default function OrderFilters({ filters, setFilters, tecnicos = [], vendedores = [], constants = null }) {
  const update = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));
  const statusOptions = constants?.status_opcoes?.length ? constants.status_opcoes : STATUS_OPTIONS_FALLBACK;
  const osTypes = constants?.os_tipos?.length ? constants.os_tipos : OS_TYPES_FALLBACK;

  return (
    <FilterBar className="bg-card rounded-xl border border-border p-4">
      <div className="relative flex-1 min-w-[200px]">
        <MagnifyingGlass className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
        <FilterInput
          placeholder="Buscar cliente, modelo, IMEI..."
          value={filters.search || ""}
          onChange={(e) => update("search", e.target.value)}
          className="w-full pl-8"
        />
      </div>

      <FilterSelect
        value={filters.status || ""}
        onValueChange={(v) => update("status", v === "all" ? "" : v)}
        placeholder="Status"
        className="w-44"
        options={[{ value: "all", label: "Todos os status" }, ...statusOptions.map((s) => ({ value: s, label: s }))]}
      />

      <FilterSelect
        value={filters.tipo || ""}
        onValueChange={(v) => update("tipo", v === "all" ? "" : v)}
        placeholder="Tipo"
        className="w-36"
        options={[{ value: "all", label: "Todos os tipos" }, ...osTypes.map((t) => ({ value: t, label: t }))]}
      />

      {tecnicos.length > 0 && (
        <FilterSelect
          value={filters.tecnico || ""}
          onValueChange={(v) => update("tecnico", v === "all" ? "" : v)}
          placeholder="Técnico"
          options={[{ value: "all", label: "Todos técnicos" }, ...tecnicos.map((t) => ({ value: t, label: t }))]}
        />
      )}

      {vendedores.length > 0 && (
        <FilterSelect
          value={filters.vendedor || ""}
          onValueChange={(v) => update("vendedor", v === "all" ? "" : v)}
          placeholder="Vendedor"
          options={[{ value: "all", label: "Todos vendedores" }, ...vendedores.map((v) => ({ value: v, label: v }))]}
        />
      )}
    </FilterBar>
  );
}
