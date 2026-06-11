import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { MobilityCategory } from "@/lib/api/types";

type MobilityCategoryRow = MobilityCategory;

function getColumns(
  onEdit: (framework: MobilityCategory) => void,
  onDelete: (framework: MobilityCategory) => void,
  isYearClosed: boolean,
): DataTableColumn<MobilityCategoryRow>[] {
  return [
    {
      key: "name",
      header: "Cadre",
      render: (framework) => (
        <p className="font-medium text-gray-900">{framework.name}</p>
      ),
    },
    {
      key: "moveon_id",
      header: "MoveON ID",
      render: (framework) => framework.moveon_id || "-",
    },
    {
      key: "last_sync_moveon",
      header: "Derniere synchro",
      render: (framework) => framework.last_sync_moveon || "-",
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (framework) => (
        <ActionButtons
          onEdit={() => onEdit(framework)}
          editDisabled={isYearClosed}
          editDisabledTitle="Année clôturée — modification non autorisée"
          onDelete={() => onDelete(framework)}
          deleteDisabled={isYearClosed}
          deleteDisabledTitle="Année clôturée — suppression non autorisée"
        />
      ),
    },
  ];
}

type MobilityCategorysTableProps = {
  agreementFrameworks: MobilityCategory[];
  isYearClosed?: boolean;
  onDelete: (framework: MobilityCategory) => void;
  onEdit: (framework: MobilityCategory) => void;
};

export function MobilityCategorysTable({
  agreementFrameworks,
  isYearClosed = false,
  onDelete,
  onEdit,
}: MobilityCategorysTableProps) {
  return (
    <DataTable
      columns={getColumns(onEdit, onDelete, isYearClosed)}
      data={agreementFrameworks}
      emptyLabel="Aucun cadre d'accord configure"
      getRowKey={(framework) => framework.id}
      maxHeight="28rem"
      pageSize={5}
    />
  );
}
