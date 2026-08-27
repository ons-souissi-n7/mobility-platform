"use client";

import { useState } from "react";
import { Eye } from "lucide-react";

import { AgreementDetailModal } from "@/components/mobility/agreement-detail-modal";
import { AgreementYearCell } from "@/components/mobility/agreement-year-cell";
import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import { createIdMap } from "@/lib/utils";
import type {
  AcademicYear,
  Agreement,
  AgreementYear,
  AgreementYearDepartment,
  Department,
  Level,
  MobilityCategory,
  PartnerUniversity,
} from "@/lib/api/types";

type AgreementRow = {
  agreement: Agreement;
  yearInstance: AgreementYear | undefined;
  deptQuotas: AgreementYearDepartment[];
};

export function AgreementsTable({
  academicYears,
  agreements,
  agreementYears,
  agreementYearDepartments,
  categories,
  departments,
  levels,
  universities,
  yearFilter,
  isYearClosed = false,
  isYearLocked = false,
  onToggleYearActive,
  onEditYear,
  onEditYearInp,
  onValidateYear,
  onSaveDeptQuota,
  onEditYearDuration,
  onRestore,
  onEdit,
  onDelete,
}: Readonly<{
  academicYears: AcademicYear[];
  agreements: Agreement[];
  agreementYears: AgreementYear[];
  agreementYearDepartments: AgreementYearDepartment[];
  categories: MobilityCategory[];
  departments: Department[];
  levels: Level[];
  universities: PartnerUniversity[];
  yearFilter?: string;
  isYearClosed?: boolean;
  isYearLocked?: boolean;
  onToggleYearActive: (yi: AgreementYear) => Promise<void>;
  onEditYear: (yi: AgreementYear, n7Places: number) => Promise<void>;
  onEditYearInp: (yi: AgreementYear, inpPlaces: number) => Promise<void>;
  onValidateYear: (yi: AgreementYear) => Promise<void>;
  onSaveDeptQuota: (dq: AgreementYearDepartment, places: number) => Promise<void>;
  onEditYearDuration: (yi: AgreementYear, durationMonths: number | null) => Promise<void>;
  onRestore: (agreement: Agreement) => Promise<void>;
  onEdit?: (agreement: Agreement) => void;
  onDelete?: (agreement: Agreement) => void;
}>) {
  const [viewingRow, setViewingRow] = useState<AgreementRow | null>(null);

  const universityById  = createIdMap(universities);
  const categoryById    = createIdMap(categories);
  const departmentById  = createIdMap(departments);
  const levelById       = createIdMap(levels);

  const yearInstanceMap = new Map<number, AgreementYear>();
  for (const yi of agreementYears) {
    if (!yearFilter || yi.academic_year_label === yearFilter) {
      yearInstanceMap.set(yi.agreement_id, yi);
    }
  }

  const deptQuotasByYearId = new Map<number, AgreementYearDepartment[]>();
  for (const dq of agreementYearDepartments) {
    const list = deptQuotasByYearId.get(dq.agreement_year_id) ?? [];
    list.push(dq);
    deptQuotasByYearId.set(dq.agreement_year_id, list);
  }

  const rows: AgreementRow[] = agreements.map((a) => {
    const yi = yearInstanceMap.get(a.id);
    return {
      agreement: a,
      yearInstance: yi,
      deptQuotas: yi ? (deptQuotasByYearId.get(yi.id) ?? []) : [],
    };
  });

  const columns: DataTableColumn<AgreementRow>[] = [
    {
      key: "accord",
      header: "Accord",
      render: ({ agreement }) => {
        // Vide = tous inclus
        const displayLevels = agreement.level_ids.length > 0
          ? agreement.level_ids.map((id) => levelById.get(id)).filter(Boolean)
          : [...levelById.values()];
        const displayDepts = agreement.department_ids.length > 0
          ? agreement.department_ids.map((id) => departmentById.get(id)).filter(Boolean)
          : [...departmentById.values()];

        return (
          <div className="min-w-48">
            <p className="font-medium text-gray-900">{agreement.name}</p>
            {agreement.reference ? (
              <p className="text-xs text-gray-400">{agreement.reference}</p>
            ) : null}
            <div className="mt-1 flex flex-wrap gap-1">
              {displayLevels.map((l) => l && (
                <span key={l.id} className="rounded-full bg-purple-100 px-1.5 py-0.5 text-[10px] font-medium text-purple-700">
                  {l.code}
                </span>
              ))}
              {displayDepts.map((d) => d && (
                <span key={d.id} className="rounded-full bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-700">
                  {d.code}
                </span>
              ))}
            </div>
          </div>
        );
      },
    },
    {
      key: "partenaire",
      header: "Partenaire",
      render: ({ agreement }) => {
        const u = universityById.get(agreement.partner_university_id);
        if (!u) return <span className="text-xs text-gray-400">—</span>;
        return (
          <div>
            <p className="text-sm font-medium text-gray-900">
              {u.name} - {u.country_name_fr}
            </p>
            {u.short_name ? (
              <p className="text-xs text-gray-500">({u.short_name})</p>
            ) : null}
          </div>
        );
      },
    },
    {
      key: "cadre",
      header: "Cadre / Direction",
      render: ({ agreement }) => {
        const cat = categoryById.get(agreement.category_id ?? -1);
        return (
          <div className="space-y-1">
            {cat ? <p className="text-xs font-medium text-gray-600">{cat.name}</p> : null}
            <DirectionBadge direction={agreement.direction} />
          </div>
        );
      },
    },
    {
      key: "validite",
      header: "Validité · INP",
      render: ({ agreement }) => (
        <div className="text-xs">
          <p className="text-gray-500">
            {agreement.valid_from  ? agreement.valid_from.slice(0, 7)  : "—"}
            {" → "}
            {agreement.valid_until ? agreement.valid_until.slice(0, 7) : "—"}
          </p>
          <p className="mt-0.5 font-semibold text-gray-700">
            {agreement.inp_total_places} place{agreement.inp_total_places !== 1 ? "s" : ""} INP
          </p>
          {agreement.inp_institutions ? (
            <p className="max-w-32 truncate text-[10px] text-gray-400" title={agreement.inp_institutions}>
              {agreement.inp_institutions}
            </p>
          ) : null}
        </div>
      ),
    },
    {
      key: "annee",
      header: yearFilter ? `Année ${yearFilter}` : "Instance annuelle",
      render: ({ yearInstance, deptQuotas }) => {
        if (!yearInstance) {
          return <span className="text-xs italic text-gray-400">Pas d&apos;instance</span>;
        }
        return (
          <AgreementYearCell
            actionsDisabled={isYearClosed || isYearLocked}
            deptQuotas={deptQuotas}
            departmentById={departmentById}
            onEditYear={onEditYear}
            onEditYearDuration={onEditYearDuration}
            onEditYearInp={onEditYearInp}
            onSaveDeptQuota={onSaveDeptQuota}
            onToggleActive={onToggleYearActive}
            onValidateYear={onValidateYear}
            yearInstance={yearInstance}
          />
        );
      },
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (row) => (
        <div className="flex items-center justify-end gap-1">
          <button
            className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
            onClick={() => setViewingRow(row)}
            title="Voir les détails"
            type="button"
          >
            <Eye size={15} />
          </button>
          <ActionButtons
            onEdit={onEdit ? () => onEdit(row.agreement) : undefined}
            editDisabled={isYearClosed || isYearLocked}
            editDisabledTitle={isYearClosed ? "Année clôturée" : "Campagne en cours — modifications verrouillées"}
            onDelete={() => onDelete?.(row.agreement)}
            deleteDisabled={isYearClosed || isYearLocked}
            deleteDisabledTitle={isYearClosed ? "Année clôturée" : "Campagne en cours — modifications verrouillées"}
          />
        </div>
      ),
    },
  ];

  return (
    <>
      <DataTable
        columns={columns}
        data={rows}
        emptyLabel="Aucun accord trouvé."
        getRowKey={(row) => row.agreement.id}
      />

      {viewingRow && (
        <AgreementDetailModal
          academicYears={academicYears}
          agreement={viewingRow.agreement}
          allAgreementYears={agreementYears}
          allDeptQuotas={agreementYearDepartments}
          university={universityById.get(viewingRow.agreement.partner_university_id)}
          category={categoryById.get(viewingRow.agreement.category_id ?? -1)}
          departments={departmentById}
          levels={levelById}
          onClose={() => setViewingRow(null)}
          onEditYear={onEditYear}
          onEditYearDuration={onEditYearDuration}
          onEditYearInp={onEditYearInp}
          onRestore={onRestore}
          onSaveDeptQuota={onSaveDeptQuota}
          onToggleYearActive={onToggleYearActive}
          onValidateYear={onValidateYear}
        />
      )}
    </>
  );
}

export function DirectionBadge({ direction }: { direction: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    outgoing: { label: "Sortant",  cls: "bg-blue-100 text-blue-700"   },
    incoming: { label: "Entrant",  cls: "bg-orange-100 text-orange-700" },
    both:     { label: "Les deux", cls: "bg-purple-100 text-purple-700" },
  };
  const c = map[direction] ?? { label: direction, cls: "bg-gray-100 text-gray-500" };
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${c.cls}`}>
      {c.label}
    </span>
  );
}
