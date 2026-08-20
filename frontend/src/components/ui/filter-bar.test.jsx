import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  FilterBar,
  FilterSelect,
  FilterInput,
  DateRangeFilter,
  ClearFiltersButton,
} from "./filter-bar";

describe("FilterBar", () => {
  it("renderiza os filhos", () => {
    render(
      <FilterBar>
        <span>filtro 1</span>
        <span>filtro 2</span>
      </FilterBar>
    );
    expect(screen.getByText("filtro 1")).toBeInTheDocument();
    expect(screen.getByText("filtro 2")).toBeInTheDocument();
  });
});

describe("FilterSelect", () => {
  it("mostra o placeholder quando não há valor", () => {
    render(
      <FilterSelect
        value=""
        onValueChange={() => {}}
        placeholder="Técnico"
        options={[{ value: "joao", label: "João" }]}
      />
    );
    expect(screen.getByText("Técnico")).toBeInTheDocument();
  });
});

describe("FilterInput", () => {
  it("dispara onChange com o valor digitado", () => {
    const onChange = vi.fn();
    render(<FilterInput value="" onChange={onChange} placeholder="Buscar" />);
    fireEvent.change(screen.getByPlaceholderText("Buscar"), { target: { value: "abc" } });
    expect(onChange).toHaveBeenCalled();
  });
});

describe("DateRangeFilter", () => {
  it("chama onStartChange/onEndChange separadamente", () => {
    const onStartChange = vi.fn();
    const onEndChange = vi.fn();
    const { container } = render(
      <DateRangeFilter
        startValue=""
        endValue=""
        onStartChange={onStartChange}
        onEndChange={onEndChange}
      />
    );
    const [start, end] = container.querySelectorAll("input[type=date]");
    fireEvent.change(start, { target: { value: "2026-01-01" } });
    fireEvent.change(end, { target: { value: "2026-01-31" } });
    expect(onStartChange).toHaveBeenCalledWith("2026-01-01");
    expect(onEndChange).toHaveBeenCalledWith("2026-01-31");
  });
});

describe("ClearFiltersButton", () => {
  it("chama onClear ao clicar", async () => {
    const onClear = vi.fn();
    render(<ClearFiltersButton onClear={onClear} />);
    await userEvent.click(screen.getByText("Limpar filtros"));
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("aceita um label customizado", () => {
    render(<ClearFiltersButton onClear={() => {}} label="Resetar" />);
    expect(screen.getByText("Resetar")).toBeInTheDocument();
  });
});
