import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { Level } from "@/lib/api/types";

function getColumns(
  onEdit: (level: Level) => void,
  onDelete: (level: Level) => void,
): DataTableColumn<Level>[] {
  return [
    {
      key: "code",
      header: "Code",
      render: (level) => (
        <span className="font-mono font-medium text-gray-900">{level.code}</span>
      ),
    },
    {
      key: "name",
      header: "Intitule",
      render: (level) => level.name || "-",
    },
    {
      key: "pegase_id",
      header: "ID Pegase",
      render: (level) => (
        <span className="font-mono text-xs text-gray-500">{level.pegase_id ?? "-"}</span>
      ),
    },
    {
      key: "last_sync_pegase",
      header: "Derniere sync",
      render: (level) =>
        level.last_sync_pegase
          ? new Date(level.last_sync_pegase).toLocaleDateString("fr-FR")
          : "-",
    },
    {
      key: "is_active",
      header: "Statut",
      render: (level) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-medium ${
            level.is_active
              ? "bg-emerald-50 text-emerald-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          {level.is_active ? "Actif" : "Inactif"}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (level) => (
        <ActionButtons onDelete={() => onDelete(level)} onEdit={() => onEdit(level)} />
      ),
    },
  ];
}

export function LevelsTable({
  levels,
  onDelete,
  onEdit,
}: {
  levels: Level[];
  onDelete: (level: Level) => void;
  onEdit: (level: Level) => void;
}) {
  return (
    <DataTable
      columns={getColumns(onEdit, onDelete)}
      data={levels}
      emptyLabel="Aucun niveau configure"
      getRowKey={(level) => level.id}
      pageSize={15}
    />
  );
}
