import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DataTable } from "./data-table";

const columns = [
  { key: "nome", header: "Nome" },
  { key: "valor", header: "Valor", render: (row) => `R$ ${row.valor}` },
];
const rows = [
  { id: 1, nome: "Item A", valor: 10 },
  { id: 2, nome: "Item B", valor: 20 },
];

describe("DataTable", () => {
  it("renderiza cabeçalhos e células, usando render() quando informado", () => {
    render(<DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} />);
    expect(screen.getByText("Nome")).toBeInTheDocument();
    expect(screen.getByText("Valor")).toBeInTheDocument();
    expect(screen.getByText("Item A")).toBeInTheDocument();
    expect(screen.getByText("R$ 10")).toBeInTheDocument();
    expect(screen.getByText("R$ 20")).toBeInTheDocument();
  });

  it("renderiza uma linha por item de rows, sem linha extra quando vazio", () => {
    const { container } = render(<DataTable columns={columns} rows={[]} getRowKey={(r) => r.id} />);
    expect(container.querySelectorAll("tbody tr")).toHaveLength(0);
  });

  it("stickyHeader aplica sticky top-0 no <thead>", () => {
    const { container } = render(
      <DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} stickyHeader />
    );
    expect(container.querySelector("thead").className).toContain("sticky");
  });

  it("sem stickyHeader, o <thead> não tem a classe sticky", () => {
    const { container } = render(<DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} />);
    expect(container.querySelector("thead").className).not.toContain("sticky");
  });

  it("onRowClick é chamado ao clicar na linha e ao pressionar Enter com foco nela", async () => {
    const onRowClick = vi.fn();
    render(<DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} onRowClick={onRowClick} />);
    const user = userEvent.setup();

    await user.click(screen.getByText("Item A"));
    expect(onRowClick).toHaveBeenCalledWith(rows[0]);

    screen.getByText("Item B").closest("tr").focus();
    await user.keyboard("{Enter}");
    expect(onRowClick).toHaveBeenCalledWith(rows[1]);
  });

  it("sem onRowClick, as linhas não são focáveis nem clicáveis", () => {
    render(<DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} />);
    const row = screen.getByText("Item A").closest("tr");
    expect(row).not.toHaveAttribute("tabindex");
  });
});
