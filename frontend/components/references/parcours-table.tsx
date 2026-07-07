import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { Department, Parcours } from "@/lib/api/types";
import { createIdMap } from "@/lib/utils";

function getColumns(
  departments: Department[],
  onEdit: (p: Parcours) => void,
  onDelete: (p: Parcours) => void,
): DataTableColumn<Parcours>[] {
  const deptMap = createIdMap(departments);
  return [
    {
      key: "department",
      header: "Département",
      render: (p) => {
        const d = deptMap.get(p.department_id);
        return d ? (
          <span className="font-medium text-gray-900">{d.code}</span>
        ) : (
          <span className="text-gray-400">—</span>
        );
      },
    },
    {
      key: "code",
      header: "Code",
      render: (p) => <span className="font-mono text-sm">{p.code}</span>,
    },
    {
      key: "label",
      header: "Intitule",
      render: (p) => p.label,
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (p) => (
        <ActionButtons onDelete={() => onDelete(p)} onEdit={() => onEdit(p)} />
      ),
    },
  ];
}

type ParcoursTableProps = {
  parcours: Parcours[];
  departments: Department[];
  onDelete: (p: Parcours) => void;
  onEdit: (p: Parcours) => void;
};

export function ParcoursTable({ parcours, departments, onDelete, onEdit }: ParcoursTableProps) {
  return (
    <DataTable
      columns={getColumns(departments, onEdit, onDelete)}
      data={parcours}
      emptyLabel="Aucun parcours reference"
      getRowKey={(p) => p.id}
    />
  );
}
