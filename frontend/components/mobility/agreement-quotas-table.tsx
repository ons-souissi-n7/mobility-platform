import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { Agreement, AgreementYear } from "@/lib/api/types";
import { createIdMap } from "@/lib/utils";

type QuotaRow = AgreementYear & {
  agreementName: string;
};

function getColumns(
  onDelete: (quota: AgreementYear) => void,
  onEdit: (quota: AgreementYear) => void,
  isYearClosed: boolean,
): DataTableColumn<QuotaRow>[] {
  return [
    {
      key: "agreement",
      header: "Accord",
      render: (quota) => (
        <p className="min-w-48 font-medium text-gray-900">{quota.agreementName}</p>
      ),
    },
    {
      key: "year",
      header: "Annee",
      render: (quota) => quota.academic_year_label,
    },
    {
      key: "n7_places",
      header: "Places N7",
      render: (quota) => (
        <span className="font-medium text-gray-900">{quota.n7_places}</span>
      ),
    },
    {
      key: "active",
      header: "Actif",
      render: (quota) => (quota.is_active ? "Oui" : "Non"),
    },
    {
      key: "validated",
      header: "Valide",
      render: (quota) =>
        quota.is_validated ? (
          <span className="rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">
            Oui
          </span>
        ) : (
          <span className="text-xs text-gray-400">Non</span>
        ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (quota) => (
        <ActionButtons
          onEdit={() => onEdit(quota)}
          editDisabled={isYearClosed}
          editDisabledTitle="Année clôturée — modification non autorisée"
          onDelete={() => onDelete(quota)}
          deleteDisabled={isYearClosed}
          deleteDisabledTitle="Année clôturée — suppression non autorisée"
        />
      ),
    },
  ];
}

export function AgreementQuotasTable({
  agreements,
  isYearClosed = false,
  onDelete,
  onEdit,
  quotas,
}: {
  agreements: Agreement[];
  isYearClosed?: boolean;
  onDelete: (quota: AgreementYear) => void;
  onEdit: (quota: AgreementYear) => void;
  quotas: AgreementYear[];
}) {
  const agreementsById = createIdMap(agreements);
  const rows = quotas.map((quota) => ({
    ...quota,
    agreementName: agreementsById.get(quota.agreement_id)?.name ?? "Accord inconnu",
  }));

  return (
    <DataTable
      columns={getColumns(onDelete, onEdit, isYearClosed)}
      data={rows}
      emptyLabel="Aucun quota d'accord configure"
      getRowKey={(quota) => quota.id}
      maxHeight="32rem"
      pageSize={5}
    />
  );
}
