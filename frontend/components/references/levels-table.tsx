import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { Level } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";

const LOCKED_TITLE = "Modifications disponibles en phase Initialisation uniquement";

function getColumns(
  onEdit: (level: Level) => void,
  onDelete: (level: Level) => void,
  readOnly: boolean,
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
      key: "is_terminal",
      header: "est_niveau_terminal",
      render: (level) =>
        level.is_terminal ? (
          <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
            Diplômant
          </span>
        ) : (
          <span className="text-gray-400">—</span>
        ),
    },
    {
      key: "last_sync_pegase",
      header: "Derniere sync",
      render: (level) => formatDate(level.last_sync_pegase),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (level) => (
        <ActionButtons
          onEdit={() => onEdit(level)}
          editDisabled={readOnly}
          editDisabledTitle={LOCKED_TITLE}
          onDelete={() => onDelete(level)}
          deleteDisabled={readOnly}
          deleteDisabledTitle={LOCKED_TITLE}
        />
      ),
    },
  ];
}

export function LevelsTable({
  levels,
  readOnly = false,
  onDelete,
  onEdit,
}: {
  levels: Level[];
  readOnly?: boolean;
  onDelete: (level: Level) => void;
  onEdit: (level: Level) => void;
}) {
  return (
    <DataTable
      columns={getColumns(onEdit, onDelete, readOnly)}
      data={levels}
      emptyLabel="Aucun niveau configure"
      getRowKey={(level) => level.id}
    />
  );
}
