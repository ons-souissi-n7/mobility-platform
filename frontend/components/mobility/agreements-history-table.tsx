"use client";

import { useState } from "react";
import { Eye, RotateCcw, Trash2 } from "lucide-react";

import { AgreementDetailModal } from "@/components/mobility/agreement-detail-modal";
import { DirectionBadge } from "@/components/mobility/agreements-table";
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

/**
 * Vue "historique complet" : un tableau listant TOUS les accords (y compris
 * ceux supprimés), un accord par ligne. Cliquer sur "Voir l'historique" ouvre
 * la fiche détaillée de l'accord avec une carte par année universitaire —
 * actif/inactif, répartition, édition — exactement comme le tableau des
 * instances de l'année en cours, mais pour toutes les années à la fois.
 */
export function AgreementsHistoryTable({
  academicYears,
  agreements,
  agreementYears,
  agreementYearDepartments,
  categories,
  departments,
  levels,
  universities,
  onEditYear,
  onEditYearDuration,
  onEditYearInp,
  onRestore,
  onSaveDeptQuota,
  onToggleYearActive,
  onValidateYear,
}: Readonly<{
  academicYears: AcademicYear[];
  agreements: Agreement[];
  agreementYears: AgreementYear[];
  agreementYearDepartments: AgreementYearDepartment[];
  categories: MobilityCategory[];
  departments: Department[];
  levels: Level[];
  universities: PartnerUniversity[];
  onEditYear: (yi: AgreementYear, n7Places: number) => Promise<void>;
  onEditYearDuration: (yi: AgreementYear, durationWeeks: number | null) => Promise<void>;
  onEditYearInp: (yi: AgreementYear, inpPlaces: number) => Promise<void>;
  onRestore: (agreement: Agreement) => Promise<void>;
  onSaveDeptQuota: (dq: AgreementYearDepartment, places: number) => Promise<void>;
  onToggleYearActive: (yi: AgreementYear) => Promise<void>;
  onValidateYear: (yi: AgreementYear) => Promise<void>;
}>) {
  const [viewingAgreement, setViewingAgreement] = useState<Agreement | null>(null);

  const universityById = createIdMap(universities);
  const categoryById = createIdMap(categories);
  const departmentById = createIdMap(departments);
  const levelById = createIdMap(levels);

  const yearCountByAgreement = new Map<number, number>();
  for (const yi of agreementYears) {
    yearCountByAgreement.set(yi.agreement_id, (yearCountByAgreement.get(yi.agreement_id) ?? 0) + 1);
  }

  const columns: DataTableColumn<Agreement>[] = [
    {
      key: "accord",
      header: "Accord",
      render: (agreement) => (
        <div className="min-w-48">
          <p className="font-medium text-gray-900">{agreement.name}</p>
          {agreement.reference ? (
            <p className="text-xs text-gray-400">{agreement.reference}</p>
          ) : null}
        </div>
      ),
    },
    {
      key: "partenaire",
      header: "Partenaire",
      render: (agreement) => {
        const u = universityById.get(agreement.partner_university_id);
        if (!u) return <span className="text-xs text-gray-400">—</span>;
        return (
          <div>
            <p className="text-sm font-medium text-gray-900">
              {u.name} - {u.country_name_fr}
            </p>
            {u.short_name ? <p className="text-xs text-gray-500">({u.short_name})</p> : null}
          </div>
        );
      },
    },
    {
      key: "cadre",
      header: "Cadre / Direction",
      render: (agreement) => {
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
      render: (agreement) => (
        <div className="text-xs">
          <p className="text-gray-500">
            {agreement.valid_from ? agreement.valid_from.slice(0, 7) : "—"}
            {" → "}
            {agreement.valid_until ? agreement.valid_until.slice(0, 7) : "—"}
          </p>
          <p className="mt-0.5 font-semibold text-gray-700">
            {agreement.inp_total_places} place{agreement.inp_total_places !== 1 ? "s" : ""} INP
          </p>
        </div>
      ),
    },
    {
      key: "statut",
      header: "Statut",
      render: (agreement) => (
        <div className="space-y-1">
          {agreement.deleted_at ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-medium text-red-700">
              <Trash2 size={9} />
              Supprimé le {new Date(agreement.deleted_at).toLocaleDateString("fr-FR")}
            </span>
          ) : (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
              Actif
            </span>
          )}
          <p className="text-[10px] text-gray-400">
            {yearCountByAgreement.get(agreement.id) ?? 0} année
            {(yearCountByAgreement.get(agreement.id) ?? 0) > 1 ? "s" : ""} d&apos;historique
          </p>
        </div>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (agreement) => (
        <div className="flex items-center justify-end gap-1">
          <button
            className="flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-[11px] text-gray-600 hover:bg-gray-50"
            onClick={() => setViewingAgreement(agreement)}
            title="Voir l'historique complet"
            type="button"
          >
            <Eye size={13} />
            Historique
          </button>
          {agreement.deleted_at && (
            <button
              className="flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-[11px] text-gray-600 hover:bg-gray-50"
              onClick={() => void onRestore(agreement)}
              title="Restaurer l'accord"
              type="button"
            >
              <RotateCcw size={13} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <>
      <DataTable
        columns={columns}
        data={agreements}
        emptyLabel="Aucun accord trouvé."
        getRowKey={(agreement) => agreement.id}
      />

      {viewingAgreement && (
        <AgreementDetailModal
          academicYears={academicYears}
          agreement={viewingAgreement}
          allAgreementYears={agreementYears}
          allDeptQuotas={agreementYearDepartments}
          university={universityById.get(viewingAgreement.partner_university_id)}
          category={categoryById.get(viewingAgreement.category_id ?? -1)}
          departments={departmentById}
          levels={levelById}
          onClose={() => setViewingAgreement(null)}
          onEditYear={onEditYear}
          onEditYearDuration={onEditYearDuration}
          onEditYearInp={onEditYearInp}
          onRestore={async (a) => {
            await onRestore(a);
            setViewingAgreement(null);
          }}
          onSaveDeptQuota={onSaveDeptQuota}
          onToggleYearActive={onToggleYearActive}
          onValidateYear={onValidateYear}
        />
      )}
    </>
  );
}
