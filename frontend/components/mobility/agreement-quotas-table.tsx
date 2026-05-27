import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { Agreement, AgreementQuota } from "@/lib/api/types";

type QuotaRow = AgreementQuota & {
  agreementName: string;
};

function getColumns(
  onDelete: (quota: AgreementQuota) => void,
  onEdit: (quota: AgreementQuota) => void,
): DataTableColumn<QuotaRow>[] {
  return [
    {
      key: "agreement",
      header: "Accord",
      render: (quota) => (
        <div className="min-w-64">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium text-gray-900">{quota.agreementName}</p>
            {quota.is_estimated ? (
              <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">
                {quota.source_scope === "manual_required" ? "A saisir" : "Estime"}
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-xs text-gray-500">{quota.places_id || "Places sans ID MoveON"}</p>
          {quota.source_total_places != null ? (
            <p className="mt-1 text-xs text-gray-500">
              Source {quota.source_scope.toUpperCase()}: {quota.source_remaining_places ?? "-"}
              /{quota.source_total_places}
            </p>
          ) : null}
          {quota.source_scope === "manual_required" ? (
            <p className="mt-1 text-xs font-medium text-red-700">
              Nouveau sans historique: l&apos;admin doit renseigner les places.
            </p>
          ) : quota.estimation_basis ? (
            <p className="mt-1 text-xs text-amber-700">{quota.estimation_basis}</p>
          ) : null}
        </div>
      ),
    },
    {
      key: "year",
      header: "Annee",
      render: (quota) => quota.academic_year_label,
    },
    {
      key: "period",
      header: "Periode",
      render: (quota) => quota.period || "-",
    },
    {
      key: "places",
      header: "Places",
      render: (quota) => (
        <span className="font-medium text-gray-900">
          {quota.remaining_places}/{quota.total_places}
        </span>
      ),
    },
    {
      key: "duration",
      header: "Duree",
      render: (quota) =>
        quota.total_duration
          ? `${quota.total_duration} ${quota.duration_unit || ""}`.trim()
          : "-",
    },
    {
      key: "effective",
      header: "Effectif",
      render: (quota) => (quota.is_effective ? "Oui" : "Non"),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (quota) => (
        <ActionButtons onDelete={() => onDelete(quota)} onEdit={() => onEdit(quota)} />
      ),
    },
  ];
}

export function AgreementQuotasTable({
  agreements,
  onDelete,
  onEdit,
  quotas,
}: {
  agreements: Agreement[];
  onDelete: (quota: AgreementQuota) => void;
  onEdit: (quota: AgreementQuota) => void;
  quotas: AgreementQuota[];
}) {
  const agreementsById = new Map(agreements.map((agreement) => [agreement.id, agreement]));
  const rows = quotas.map((quota) => ({
    ...quota,
    agreementName: agreementsById.get(quota.agreement_id)?.name ?? "Accord inconnu",
  }));

  return (
    <DataTable
      columns={getColumns(onDelete, onEdit)}
      data={rows}
      emptyLabel="Aucun quota d'accord configure"
      getRowKey={(quota) => quota.id}
      maxHeight="32rem"
      pageSize={15}
    />
  );
}
