import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type {
  Agreement,
  AgreementYear,
  AgreementYearDepartment,
  Department,
} from "@/lib/api/types";
import { createIdMap } from "@/lib/utils";

type DepartmentQuotaRow = AgreementYearDepartment & {
  agreementName: string;
  departmentLabel: string;
  quotaLabel: string;
};

function getColumns(
  onDelete: (quota: AgreementYearDepartment) => void,
  onEdit: (quota: AgreementYearDepartment) => void,
): DataTableColumn<DepartmentQuotaRow>[] {
  return [
    {
      key: "department",
      header: "Département",
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
      header: "Places estimées",
      render: (quota) => (
        <span className="font-medium text-gray-900">{quota.estimated_places}</span>
      ),
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
  yearInstances,
}: {
  agreements: Agreement[];
  departmentQuotas: AgreementYearDepartment[];
  departments: Department[];
  onDelete: (quota: AgreementYearDepartment) => void;
  onEdit: (quota: AgreementYearDepartment) => void;
  yearInstances: AgreementYear[];
}) {
  const agreementsById = createIdMap(agreements);
  const departmentsById = createIdMap(departments);
  const yearInstancesById = createIdMap(yearInstances);

  const rows = departmentQuotas.map((dq) => {
    const yearInstance = yearInstancesById.get(dq.agreement_year_id);
    const agreement = yearInstance ? agreementsById.get(yearInstance.agreement_id) : undefined;
    const department = departmentsById.get(dq.department_id);

    return {
      ...dq,
      agreementName: agreement?.name ?? "Accord inconnu",
      departmentLabel: department ? `${department.code} - ${department.name}` : "Département inconnu",
      quotaLabel: yearInstance?.academic_year_label ?? "Année inconnue",
    };
  });

  return (
    <DataTable
      columns={getColumns(onDelete, onEdit)}
      data={rows}
      emptyLabel="Aucun quota departement configure"
      getRowKey={(quota) => quota.id}
      maxHeight="30rem"
    />
  );
}
