import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { Department } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";

const LOCKED_TITLE = "Modifications disponibles en phase Initialisation uniquement";

function getColumns(
  onEdit: (department: Department) => void,
  onDelete: (department: Department) => void,
  readOnly: boolean,
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
      key: "pegase_id",
      header: "Pegase ID",
      render: (department) => department.pegase_id ?? "-",
    },
    {
      key: "last_sync_pegase",
      header: "Dernier sync",
      render: (department) => formatDate(department.last_sync_pegase),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (department) => (
        <ActionButtons
          onEdit={() => onEdit(department)}
          editDisabled={readOnly}
          editDisabledTitle={LOCKED_TITLE}
          onDelete={() => onDelete(department)}
          deleteDisabled={readOnly}
          deleteDisabledTitle={LOCKED_TITLE}
        />
      ),
    },
  ];
}

type DepartmentsTableProps = {
  departments: Department[];
  readOnly?: boolean;
  onDelete: (department: Department) => void;
  onEdit: (department: Department) => void;
};

export function DepartmentsTable({
  departments,
  readOnly = false,
  onDelete,
  onEdit,
}: DepartmentsTableProps) {
  return (
    <DataTable
      columns={getColumns(onEdit, onDelete, readOnly)}
      data={departments}
      emptyLabel="Aucun departement reference"
      getRowKey={(department) => department.id}
    />
  );
}
