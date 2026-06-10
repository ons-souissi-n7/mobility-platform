import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";

type Item = { id: number; name: string };

const columns: DataTableColumn<Item>[] = [
  { key: "name", header: "Nom", render: (item) => item.name },
];

const items: Item[] = Array.from({ length: 12 }, (_, i) => ({
  id: i + 1,
  name: `Item ${i + 1}`,
}));

describe("DataTable", () => {
  it("renders column headers", () => {
    render(
      <DataTable
        columns={columns}
        data={[]}
        emptyLabel="Aucun élément"
        getRowKey={(i) => i.id}
        pageSize={5}
      />,
    );
    expect(screen.getByText("Nom")).toBeInTheDocument();
  });

  it("shows emptyLabel when data is empty", () => {
    render(
      <DataTable
        columns={columns}
        data={[]}
        emptyLabel="Aucune donnée"
        getRowKey={(i) => i.id}
        pageSize={5}
      />,
    );
    expect(screen.getByText("Aucune donnée")).toBeInTheDocument();
  });

  it("renders all items when within page size", () => {
    render(
      <DataTable
        columns={columns}
        data={items.slice(0, 3)}
        emptyLabel="Aucun"
        getRowKey={(i) => i.id}
        pageSize={5}
      />,
    );
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 3")).toBeInTheDocument();
  });

  it("paginates: first page shows only pageSize items", () => {
    render(
      <DataTable
        columns={columns}
        data={items}
        emptyLabel="Aucun"
        getRowKey={(i) => i.id}
        pageSize={5}
      />,
    );
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 5")).toBeInTheDocument();
    expect(screen.queryByText("Item 6")).not.toBeInTheDocument();
  });

  it("navigates to the next page", async () => {
    render(
      <DataTable
        columns={columns}
        data={items}
        emptyLabel="Aucun"
        getRowKey={(i) => i.id}
        pageSize={5}
      />,
    );
    const nextBtn = screen.getByRole("button", { name: /suivant/i });
    await userEvent.click(nextBtn);
    expect(screen.getByText("Item 6")).toBeInTheDocument();
    expect(screen.queryByText("Item 1")).not.toBeInTheDocument();
  });
});
