import { XCircle } from "@phosphor-icons/react";
import { Input } from "./input";
import { Button } from "./button";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "./select";
import { cn } from "@/lib/utils";

/**
 * Contêiner de layout para uma linha de filtros — mesma composição já usada em `Dashboard.jsx`
 * (`flex items-center gap-2 flex-wrap`), agora reutilizável em qualquer página. Não altera lógica de
 * filtragem — só padroniza a apresentação.
 * @param {{ className?: string, children: import("react").ReactNode }} props
 */
export function FilterBar({ className, children }) {
  return <div className={cn("flex items-center gap-2 flex-wrap", className)}>{children}</div>;
}

/**
 * Select de filtro com largura padrão — wrapper visual sobre `ui/select.jsx`. O chamador continua
 * responsável pelo mapeamento de valor (ex.: opção "Todos" -> filtro vazio), esse componente não
 * assume regra de negócio nenhuma.
 * @param {{
 *   value: string,
 *   onValueChange: (value: string) => void,
 *   placeholder: string,
 *   options: Array<{ value: string, label: string }>,
 *   className?: string,
 * }} props
 */
export function FilterSelect({ value, onValueChange, placeholder, options, className }) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className={cn("w-40", className)}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/**
 * Input de filtro com largura padrão — wrapper visual sobre `ui/input.jsx`.
 * @param {import("react").ComponentProps<typeof Input>} props
 */
export function FilterInput({ className, ...props }) {
  return <Input className={cn("w-36", className)} {...props} />;
}

/**
 * Par de inputs de data (início/fim) — mesma composição já usada em `Dashboard.jsx`.
 * @param {{
 *   startValue: string,
 *   endValue: string,
 *   onStartChange: (value: string) => void,
 *   onEndChange: (value: string) => void,
 *   className?: string,
 * }} props
 */
export function DateRangeFilter({ startValue, endValue, onStartChange, onEndChange, className }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <FilterInput type="date" value={startValue} onChange={(e) => onStartChange(e.target.value)} />
      <FilterInput type="date" value={endValue} onChange={(e) => onEndChange(e.target.value)} />
    </div>
  );
}

/**
 * Botão de limpar filtros — visível só quando faz sentido (o chamador decide via `show`/renderização
 * condicional), sem impor quando os filtros estão "sujos".
 * @param {{ onClear: () => void, label?: string, className?: string }} props
 */
export function ClearFiltersButton({ onClear, label = "Limpar filtros", className }) {
  return (
    <Button variant="ghost" size="sm" onClick={onClear} className={className}>
      <XCircle className="h-4 w-4" />
      {label}
    </Button>
  );
}
