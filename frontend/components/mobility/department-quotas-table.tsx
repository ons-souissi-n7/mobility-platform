import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type {
  Agreement,
  AgreementQuota,
  Department,
  DepartmentQuota,
} from "@/lib/api/types";

type DepartmentQuotaRow = DepartmentQuota & {
  agreementName: string;
  departmentLabel: string;
  quotaLabel: string;
};

function getColumns(
  onDelete: (quota: DepartmentQuota) => void,
  onEdit: (quota: DepartmentQuota) => void,
): DataTableColumn<DepartmentQuotaRow>[] {
  return [
    {
      key: "department",
      header: "Departement",
      render: (quota) => <span className="font-medium text-gray-900">{quota.departmentLabel}</span>,
    },
    {
      key: "agreement",
      header: "Accord",
      render: (quota) => (
        <div className="min-w-64">
          <p className="font-medium text-gray-900">{quota.agreementName}</p>
          <p className="mt-1 text-xs text-gray-500">{quota.quotaLabel}</p>
        </div>
      ),
    },
    {
      key: "places",
      header: "Places",
      render: (quota) => (
        <div>
          <span className="font-medium text-gray-900">{quota.places}</span>
          {quota.is_estimated ? (
            <span className="ml-2 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">
              Estime
            </span>
          ) : null}
          {quota.estimation_basis ? (
            <p className="mt-1 text-xs text-amber-700">{quota.estimation_basis}</p>
          ) : null}
        </div>
      ),
    },
    {
      key: "remarks",
      header: "Remarques",
      render: (quota) => quota.remarks || "-",
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

export function DepartmentQuotasTable({
  agreements,
  departmentQuotas,
  departments,
  onDelete,
  onEdit,
  quotas,
}: {
  agreements: Agreement[];
  departmentQuotas: DepartmentQuota[];
  departments: Department[];
  onDelete: (quota: DepartmentQuota) => void;
  onEdit: (quota: DepartmentQuota) => void;
  quotas: AgreementQuota[];
}) {
  const agreementsById = new Map(agreements.map((agreement) => [agreement.id, agreement]));
  const departmentsById = new Map(departments.map((department) => [department.id, department]));
  const quotasById = new Map(quotas.map((quota) => [quota.id, quota]));

  const rows = departmentQuotas.map((departmentQuota) => {
    const quota = quotasById.get(departmentQuota.agreement_quota_id);
    const agreement = quota ? agreementsById.get(quota.agreement_id) : undefined;
    const department = departmentsById.get(departmentQuota.department_id);

    return {
      ...departmentQuota,
      agreementName: agreement?.name ?? "Accord inconnu",
      departmentLabel: department ? `${department.code} - ${department.name}` : "Departement inconnu",
      quotaLabel: quota ? `${quota.academic_year_label}${quota.period ? ` / ${quota.period}` : ""}` : "Quota inconnu",
    };
  });

  return (
    <DataTable
      columns={getColumns(onDelete, onEdit)}
      data={rows}
      emptyLabel="Aucun quota departement configure"
      getRowKey={(quota) => quota.id}
      maxHeight="30rem"
      pageSize={15}
    />
  );
}
