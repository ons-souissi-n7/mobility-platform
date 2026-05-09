import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { Department } from "@/lib/api/types";

function getColumns(
  onEdit: (department: Department) => void,
  onDelete: (department: Department) => void,
): DataTableColumn<Department>[] {
  return [
    {
      key: "code",
      header: "Code",
      render: (department) => (
        <span className="font-medium text-gray-900">{department.code}</span>
      ),
    },
    {
      key: "name",
      header: "Intitule",
      render: (department) => department.name,
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (department) => (
        <ActionButtons
          onDelete={() => onDelete(department)}
          onEdit={() => onEdit(department)}
        />
      ),
    },
  ];
}

type DepartmentsTableProps = {
  departments: Department[];
  onDelete: (department: Department) => void;
  onEdit: (department: Department) => void;
};

export function DepartmentsTable({
  departments,
  onDelete,
  onEdit,
}: DepartmentsTableProps) {
  return (
    <DataTable
      columns={getColumns(onEdit, onDelete)}
      data={departments}
      emptyLabel="Aucun departement reference"
      getRowKey={(department) => department.id}
      maxHeight="24rem"
    />
  );
}
