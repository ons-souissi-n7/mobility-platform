"use client";

import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, ChevronUp, Lock, Plus } from "lucide-react";

import { ActionButtons } from "@/components/ui/action-buttons";
import type {
  AcademicYear,
  Agreement,
  AgreementDepartmentConstraint,
  AgreementLevelConstraint,
  AgreementQuota,
  AgreementYearAvailability,
  Department,
  DepartmentQuota,
  Level,
  PartnerUniversity,
} from "@/lib/api/types";

const PAGE_SIZE_OPTIONS = [5, 10, 15, 20];

export function AgreementsTable({
  agreements,
  agreementDepartmentConstraints,
  agreementLevelConstraints,
  agreementQuotas,
  academicYears,
  departmentQuotas,
  departments,
  levels,
  currentYear,
  onDelete,
  onAddDepartmentConstraint,
  onAddDepartmentQuota,
  onAddLevelConstraint,
  onDeleteDepartmentConstraint,
  onDeleteDepartmentQuota,
  onDeleteLevelConstraint,
  onEdit,
  onEditDepartmentQuota,
  onSaveQuota,
  onSaveSourceInfo,
  onToggleAvailability,
  onValidateAgreementQuota,
  onValidateDepartmentQuota,
  universities,
  yearFilter,
  yearAvailabilities,
}: {
  agreements: Agreement[];
  agreementDepartmentConstraints: AgreementDepartmentConstraint[];
  agreementLevelConstraints: AgreementLevelConstraint[];
  agreementQuotas: AgreementQuota[];
  academicYears: AcademicYear[];
  departmentQuotas: DepartmentQuota[];
  departments: Department[];
  levels: Level[];
  currentYear?: AcademicYear | null;
  onAddDepartmentConstraint?: (agreement: Agreement) => void;
  onAddDepartmentQuota: (quota: AgreementQuota) => void;
  onAddLevelConstraint?: (agreement: Agreement) => void;
  onDelete: (agreement: Agreement) => void;
  onDeleteDepartmentConstraint?: (constraint: AgreementDepartmentConstraint) => void;
  onDeleteDepartmentQuota: (quota: DepartmentQuota) => void;
  onDeleteLevelConstraint?: (constraint: AgreementLevelConstraint) => void;
  onEdit: (agreement: Agreement) => void;
  onEditDepartmentQuota: (quota: DepartmentQuota) => void;
  onSaveQuota: (agreement: Agreement, places: number, existingQuota: AgreementQuota | null) => Promise<void>;
  onSaveSourceInfo?: (quota: AgreementQuota, sourceTotalPlaces: number | null, sourceInstitutions: string) => Promise<void>;
  onToggleAvailability: (agreement: Agreement) => void;
  onValidateAgreementQuota: (quota: AgreementQuota) => Promise<void>;
  onValidateDepartmentQuota: (quota: DepartmentQuota) => void;
  universities: PartnerUniversity[];
  yearFilter?: string;
  yearAvailabilities: AgreementYearAvailability[];
}) {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    setPage(0);
    setExpandedIds(new Set());
  }, [agreements]);

  useEffect(() => { setPage(0); }, [pageSize]);

  const universitiesById = useMemo(
    () => new Map(universities.map((u) => [u.id, u])),
    [universities],
  );

  const agreementQuotasByAgreementId = useMemo(() => {
    const map = new Map<number, AgreementQuota[]>();
    for (const q of agreementQuotas) {
      const items = map.get(q.agreement_id) ?? [];
      items.push(q);
      map.set(q.agreement_id, items);
    }
    return map;
  }, [agreementQuotas]);

  const quotasById = useMemo(
    () => new Map(agreementQuotas.map((q) => [q.id, q])),
    [agreementQuotas],
  );

  const departmentQuotasByAgreementId = useMemo(() => {
    const map = new Map<number, DepartmentQuota[]>();
    for (const dq of departmentQuotas) {
      const quota = quotasById.get(dq.agreement_quota_id);
      if (!quota) continue;
      const items = map.get(quota.agreement_id) ?? [];
      items.push(dq);
      map.set(quota.agreement_id, items);
    }
    return map;
  }, [departmentQuotas, quotasById]);

  const levelsById = useMemo(
    () => new Map(levels.map((l) => [l.id, l])),
    [levels],
  );

  const departmentsById = useMemo(
    () => new Map(departments.map((d) => [d.id, d])),
    [departments],
  );

  const levelConstraintsByAgreementId = useMemo(() => {
    const map = new Map<number, AgreementLevelConstraint[]>();
    for (const c of agreementLevelConstraints) {
      if (!c.is_active) continue;
      const items = map.get(c.agreement_id) ?? [];
      items.push(c);
      map.set(c.agreement_id, items);
    }
    return map;
  }, [agreementLevelConstraints]);

  const deptConstraintsByAgreementId = useMemo(() => {
    const map = new Map<number, AgreementDepartmentConstraint[]>();
    for (const c of agreementDepartmentConstraints) {
      if (!c.is_active) continue;
      const items = map.get(c.agreement_id) ?? [];
      items.push(c);
      map.set(c.agreement_id, items);
    }
    return map;
  }, [agreementDepartmentConstraints]);

  const isHistoricalView = useMemo(() => {
    if (!yearFilter) return false;
    const yr = academicYears.find((y) => y.label === yearFilter);
    return yr?.status === "closed";
  }, [yearFilter, academicYears]);

  const totalPages = Math.max(1, Math.ceil(agreements.length / pageSize));
  const pageAgreements = agreements.slice(page * pageSize, (page + 1) * pageSize);

  function toggleExpand(id: number) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (agreements.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-gray-300 px-4 py-8 text-center text-sm text-gray-500">
        Aucun accord de mobilite reference
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="divide-y divide-gray-100 rounded-md border border-gray-200 bg-white">
        {pageAgreements.map((agreement) => {
          const quotaEntries = filterQuotasForYear(
            agreementQuotasByAgreementId.get(agreement.id!) ?? [],
            yearFilter,
          );
          const activeQuota = quotaEntries[0] ?? null;
          const isValidated = activeQuota?.is_validated ?? false;
          const canEditConstraints = !isHistoricalView && !isValidated;
          const visibleQuotaIds = new Set(quotaEntries.map((q) => q.id));
          const deptQuotas = (departmentQuotasByAgreementId.get(agreement.id!) ?? []).filter(
            (dq) => visibleQuotaIds.has(dq.agreement_quota_id),
          );
          const isAvailable = getAgreementAvailabilityForYear(
            agreement, yearFilter, academicYears, yearAvailabilities, currentYear,
          );
          const university = universitiesById.get(agreement.partner_university_id) ?? null;
          const isExpanded = expandedIds.has(agreement.id!);
          const levelConstraints = levelConstraintsByAgreementId.get(agreement.id!) ?? [];
          const deptConstraints = deptConstraintsByAgreementId.get(agreement.id!) ?? [];

          return (
            <Fragment key={agreement.id}>
              <div className={isExpanded ? "bg-blue-50/20" : undefined}>
                {/* ── Card body ─────────────────────────────────────── */}
                <div className="flex flex-wrap items-start gap-x-6 gap-y-3 px-4 py-3">

                  {/* Column 1 — Identite */}
                  <div className="min-w-0 flex-[3] space-y-0.5">
                    <p className="font-semibold text-gray-900 text-sm leading-snug">
                      {agreement.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {university?.name ?? "—"}
                      {university?.city ? ` · ${university.city}` : ""}
                    </p>
                    <p className="text-xs text-gray-400">
                      {agreement.reference || agreement.moveon_relation_id || "—"}
                    </p>
                    <div className="flex flex-wrap items-center gap-1 pt-1">
                      {agreement.framework ? (
                        <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
                          {agreement.framework}
                        </span>
                      ) : null}
                    </div>
                    {agreement.remarks ? (
                      <p className="truncate text-xs italic text-gray-400 pt-0.5">
                        {agreement.remarks}
                      </p>
                    ) : null}
                  </div>

                  {/* Column 2 — Niveaux + Departements */}
                  <div className="flex-[2] space-y-1.5">
                    {/* Levels */}
                    <div className="flex flex-wrap items-center gap-1">
                      <span className="text-xs text-gray-400">Niveaux :</span>
                      {levelConstraints.length === 0 ? (
                        <span className="text-xs italic text-gray-400">Tous</span>
                      ) : (
                        levelConstraints.map((c) => {
                          const lvl = levelsById.get(c.level_id);
                          return (
                            <span
                              key={c.id}
                              className="inline-flex items-center gap-0.5 rounded-full bg-purple-50 px-2 py-0.5 text-xs font-medium text-purple-700"
                            >
                              {lvl?.code ?? c.level_id}
                              {onDeleteLevelConstraint && canEditConstraints ? (
                                <button
                                  className="ml-0.5 flex h-3 w-3 items-center justify-center rounded-full text-purple-300 hover:bg-purple-200 hover:text-purple-700"
                                  onClick={() => onDeleteLevelConstraint(c)}
                                  title="Retirer ce niveau"
                                  type="button"
                                >
                                  ×
                                </button>
                              ) : null}
                            </span>
                          );
                        })
                      )}
                      {onAddLevelConstraint && canEditConstraints ? (
                        <button
                          className="flex h-5 w-5 flex-none items-center justify-center rounded-full border border-dashed border-gray-300 text-gray-400 hover:border-purple-400 hover:text-purple-600"
                          onClick={() => onAddLevelConstraint(agreement)}
                          title="Ajouter un niveau"
                          type="button"
                        >
                          <Plus className="h-3 w-3" aria-hidden="true" />
                        </button>
                      ) : null}
                    </div>

                    {/* Departments — constraints */}
                    <div className="flex flex-wrap items-center gap-1">
                      <span className="text-xs text-gray-400">Depts :</span>
                      {deptConstraints.length === 0 ? (
                        <span className="text-xs italic text-gray-400">Tous</span>
                      ) : (
                        deptConstraints.map((c) => {
                          const dept = departmentsById.get(c.department_id);
                          return (
                            <span
                              key={c.id}
                              className="inline-flex items-center gap-0.5 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-[#1E3A8A]"
                            >
                              {dept?.code ?? c.department_id}
                              {onDeleteDepartmentConstraint && canEditConstraints ? (
                                <button
                                  className="ml-0.5 flex h-3 w-3 items-center justify-center rounded-full text-blue-300 hover:bg-blue-200 hover:text-[#1E3A8A]"
                                  onClick={() => onDeleteDepartmentConstraint(c)}
                                  title="Retirer ce departement"
                                  type="button"
                                >
                                  ×
                                </button>
                              ) : null}
                            </span>
                          );
                        })
                      )}
                      {onAddDepartmentConstraint && canEditConstraints ? (
                        <button
                          className="flex h-5 w-5 flex-none items-center justify-center rounded-full border border-dashed border-gray-300 text-gray-400 hover:border-[#1E3A8A] hover:text-[#1E3A8A]"
                          onClick={() => onAddDepartmentConstraint(agreement)}
                          title="Ajouter un departement"
                          type="button"
                        >
                          <Plus className="h-3 w-3" aria-hidden="true" />
                        </button>
                      ) : null}
                    </div>
                  </div>

                  {/* Column 3 — Quotas INP */}
                  <div className="flex-[2] space-y-1.5">
                    {activeQuota ? (
                      <>
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-xs text-gray-400 shrink-0">INP total :</span>
                          <InlineEditNumber
                            value={activeQuota.source_total_places}
                            readOnly={isHistoricalView || isValidated}
                            onSave={(v) =>
                              onSaveSourceInfo?.(activeQuota, v, activeQuota.source_institutions)
                            }
                          />
                        </div>
                        <div className="flex items-start gap-1.5">
                          <span className="text-xs text-gray-400 shrink-0">Etablissements :</span>
                          <InlineEditText
                            value={activeQuota.source_institutions}
                            readOnly={isHistoricalView || isValidated}
                            placeholder="ex: INP-ENSEEIHT;INP-ENSAT"
                            onSave={(v) =>
                              onSaveSourceInfo?.(activeQuota, activeQuota.source_total_places, v)
                            }
                          />
                        </div>
                        {deptQuotas.length > 0 ? (
                          <div className="flex flex-wrap items-start gap-1">
                            <span className="text-xs text-gray-400 shrink-0">Repartition :</span>
                            <div className="flex flex-wrap gap-1">
                              {deptQuotas.map((dq) => {
                                const dept = departmentsById.get(dq.department_id);
                                return (
                                  <span
                                    key={dq.id}
                                    className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
                                  >
                                    {dept?.code ?? "?"} : {dq.places}
                                  </span>
                                );
                              })}
                            </div>
                          </div>
                        ) : null}
                      </>
                    ) : (
                      <span className="text-xs italic text-gray-400">Pas de quota</span>
                    )}
                  </div>

                  {/* Column 4 — Places N7 + Statut + Actions */}
                  <div className="flex flex-none flex-col items-end gap-2 min-w-40">
                    {/* Status row */}
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          isAvailable
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-gray-100 text-gray-500"
                        }`}
                      >
                        {isAvailable ? "disponible" : "indisponible"}
                      </span>
                      {isValidated ? (
                        <span className="flex items-center gap-1 text-xs text-gray-400">
                          <Lock className="h-3 w-3" aria-hidden="true" />
                          Valide
                        </span>
                      ) : null}
                    </div>

                    {/* N7 Places */}
                    <InlineQuotaInput
                      quota={activeQuota}
                      onSave={(places) => onSaveQuota(agreement, places, activeQuota)}
                      onValidate={
                        activeQuota && !isValidated
                          ? () => onValidateAgreementQuota(activeQuota)
                          : undefined
                      }
                      readOnly={isHistoricalView || isValidated}
                      yearLabel={yearFilter}
                    />

                    {/* Actions */}
                    <div className="flex items-center gap-1">
                      {isHistoricalView ? (
                        activeQuota ? (
                          <ExpandButton
                            expanded={isExpanded}
                            onClick={() => toggleExpand(agreement.id!)}
                          />
                        ) : null
                      ) : (
                        <>
                          {activeQuota ? (
                            <ExpandButton
                              expanded={isExpanded}
                              onClick={() => toggleExpand(agreement.id!)}
                            />
                          ) : null}
                          {!isValidated ? (
                            <>
                              <button
                                className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
                                onClick={() => onToggleAvailability(agreement)}
                                type="button"
                              >
                                {isAvailable ? "Desactiver" : "Activer"}
                              </button>
                              <ActionButtons
                                onDelete={() => onDelete(agreement)}
                                onEdit={() => onEdit(agreement)}
                              />
                            </>
                          ) : null}
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* ── Dept quota breakdown ───────────────────────────── */}
                {isExpanded && activeQuota ? (
                  <div className="border-t border-gray-100 bg-white px-4 pb-3 pt-2">
                    <DeptQuotaBreakdown
                      deptQuotas={deptQuotas}
                      departments={departments}
                      isHistoricalView={isHistoricalView}
                      isValidated={isValidated}
                      onDelete={onDeleteDepartmentQuota}
                      onEdit={onEditDepartmentQuota}
                      onValidate={onValidateDepartmentQuota}
                    />
                  </div>
                ) : null}
              </div>
            </Fragment>
          );
        })}
      </div>

      {/* ── Pagination ──────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-1 text-sm text-gray-600">
        <span>
          {agreements.length} accord{agreements.length > 1 ? "s" : ""}
          {` — page ${page + 1} / ${totalPages}`}
        </span>
        <div className="flex items-center gap-3">
          <select
            className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#1E3A8A]"
            onChange={(e) => setPageSize(Number(e.target.value))}
            value={pageSize}
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>{size} / page</option>
            ))}
          </select>
          <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ExpandButton({ expanded, onClick }: { expanded: boolean; onClick: () => void }) {
  return (
    <button
      className="flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
      onClick={onClick}
      type="button"
    >
      Repartition
      {expanded ? (
        <ChevronUp className="h-3 w-3" aria-hidden="true" />
      ) : (
        <ChevronDown className="h-3 w-3" aria-hidden="true" />
      )}
    </button>
  );
}

function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (p: number) => void;
}) {
  const pageNumbers = buildPageNumbers(page, totalPages);

  return (
    <div className="flex items-center gap-1">
      <NavBtn onClick={() => onPageChange(0)} disabled={page === 0} label="«" title="Premiere page" />
      <NavBtn onClick={() => onPageChange(page - 1)} disabled={page === 0} label="‹" title="Page precedente" />

      {pageNumbers.map((p, i) =>
        p === "..." ? (
          <span key={`ellipsis-${i}`} className="px-1 text-xs text-gray-400">…</span>
        ) : (
          <button
            key={p}
            className={`min-w-[2rem] rounded-md border px-2 py-1 text-xs font-medium ${
              p === page
                ? "border-[#1E3A8A] bg-[#1E3A8A] text-white"
                : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
            }`}
            onClick={() => onPageChange(p as number)}
            type="button"
          >
            {(p as number) + 1}
          </button>
        ),
      )}

      <NavBtn onClick={() => onPageChange(page + 1)} disabled={page >= totalPages - 1} label="›" title="Page suivante" />
      <NavBtn onClick={() => onPageChange(totalPages - 1)} disabled={page >= totalPages - 1} label="»" title="Derniere page" />
    </div>
  );
}

function NavBtn({
  onClick,
  disabled,
  label,
  title,
}: {
  onClick: () => void;
  disabled: boolean;
  label: string;
  title: string;
}) {
  return (
    <button
      className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
      disabled={disabled}
      onClick={onClick}
      title={title}
      type="button"
    >
      {label}
    </button>
  );
}

function buildPageNumbers(current: number, total: number): (number | "...")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i);
  const pages: (number | "...")[] = [];
  const addPage = (p: number) => { if (!pages.includes(p)) pages.push(p); };
  addPage(0);
  if (current > 3) pages.push("...");
  for (let p = Math.max(1, current - 2); p <= Math.min(total - 2, current + 2); p++) addPage(p);
  if (current < total - 4) pages.push("...");
  addPage(total - 1);
  return pages;
}

function DeptQuotaBreakdown({
  deptQuotas,
  departments,
  isHistoricalView,
  isValidated,
  onDelete,
  onEdit,
  onValidate,
}: {
  deptQuotas: DepartmentQuota[];
  departments: Department[];
  isHistoricalView: boolean;
  isValidated: boolean;
  onDelete: (q: DepartmentQuota) => void;
  onEdit: (q: DepartmentQuota) => void;
  onValidate: (q: DepartmentQuota) => void;
}) {
  const showActions = !isHistoricalView && !isValidated;

  if (deptQuotas.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        Aucune repartition departement pour cet accord.
      </p>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-normal text-gray-500">
          <tr>
            <th className="px-3 py-2">Departement</th>
            <th className="px-3 py-2">Places</th>
            <th className="px-3 py-2">Statut</th>
            {showActions ? <th className="px-3 py-2 text-right">Actions</th> : null}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {deptQuotas.map((dq) => {
            const dept = departments.find((d) => d.id === dq.department_id);
            return (
              <tr key={dq.id}>
                <td className="px-3 py-2.5 text-gray-700">
                  {dept ? `${dept.code} — ${dept.name}` : "Departement inconnu"}
                </td>
                <td className="px-3 py-2.5">
                  <span className="font-medium text-gray-900">{dq.places}</span>
                  {dq.estimated_places !== null && dq.estimated_places !== dq.places ? (
                    <span className="ml-1.5 text-xs text-gray-400">
                      (estime : {dq.estimated_places})
                    </span>
                  ) : null}
                </td>
                <td className="px-3 py-2.5">
                  {dq.is_validated ? (
                    <div>
                      <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                        Valide
                      </span>
                      {dq.validated_by ? (
                        <p className="mt-0.5 text-xs text-gray-400">
                          {dq.validated_by}
                          {dq.validated_at
                            ? ` · ${new Date(dq.validated_at).toLocaleDateString("fr-FR")}`
                            : ""}
                        </p>
                      ) : null}
                    </div>
                  ) : dq.is_estimated ? (
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">
                        Estime
                      </span>
                      {showActions ? (
                        <button
                          className="rounded border border-amber-300 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800 hover:bg-amber-100"
                          onClick={() => onValidate(dq)}
                          type="button"
                        >
                          Valider
                        </button>
                      ) : null}
                    </div>
                  ) : (
                    <span className="text-xs text-gray-500">Manuel</span>
                  )}
                </td>
                {showActions ? (
                  <td className="px-3 py-2.5 text-right">
                    <ActionButtons onDelete={() => onDelete(dq)} onEdit={() => onEdit(dq)} />
                  </td>
                ) : null}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Inline quota input ────────────────────────────────────────────────────────

function InlineQuotaInput({
  quota,
  onSave,
  onValidate,
  readOnly = false,
  yearLabel,
}: {
  quota: AgreementQuota | null;
  onSave: (places: number) => Promise<void>;
  onValidate?: () => Promise<void>;
  readOnly?: boolean;
  yearLabel?: string;
}) {
  const [value, setValue] = useState<string>(quota ? String(quota.total_places) : "");
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const label = yearLabel ? `Places N7 — ${yearLabel}` : "Places N7 (annee courante)";

  if (readOnly) {
    return (
      <div className="text-right">
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-lg font-semibold text-gray-900">
          {quota ? quota.total_places : "—"}
        </p>
        {quota ? (
          <p className="text-xs text-gray-400">{quota.remaining_places} restantes</p>
        ) : null}
      </div>
    );
  }

  async function handleValidate() {
    if (!onValidate) return;
    setValidating(true);
    try {
      await onValidate();
    } finally {
      setValidating(false);
    }
  }

  async function commit() {
    const trimmed = value.trim();
    if (trimmed === "" && !quota) return;
    const places = Number(trimmed);
    if (isNaN(places) || places < 0) {
      setError(true);
      return;
    }
    if (quota?.source_total_places != null && places > quota.source_total_places) {
      setError(true);
      return;
    }
    if (quota && places === quota.total_places) return;
    setError(false);
    setSaving(true);
    try {
      await onSave(places);
    } catch {
      setError(true);
    } finally {
      setSaving(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      inputRef.current?.blur();
    }
    if (e.key === "Escape") {
      setValue(quota ? String(quota.total_places) : "");
      setError(false);
      inputRef.current?.blur();
    }
  }

  return (
    <div className="text-right">
      <p className="text-xs text-gray-400">{label}</p>
      <div className="mt-0.5 flex items-center justify-end gap-1.5">
        <input
          ref={inputRef}
          className={`w-20 rounded-md border px-2 py-1 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A] ${
            error ? "border-red-400 bg-red-50" : "border-gray-300 bg-white"
          } ${saving ? "opacity-60" : ""}`}
          disabled={saving}
          min="0"
          onBlur={commit}
          onChange={(e) => {
            setValue(e.target.value);
            setError(false);
          }}
          onKeyDown={handleKeyDown}
          placeholder="places"
          type="number"
          value={value}
        />
        {saving ? <span className="text-xs text-gray-400">...</span> : null}
        {quota?.is_estimated && !quota.is_validated ? (
          <div className="flex items-center gap-1">
            <span className="rounded-full bg-amber-50 px-1.5 py-0.5 text-xs font-medium text-amber-700">
              Estime
            </span>
            {onValidate ? (
              <button
                className="rounded border border-amber-300 bg-amber-50 px-1.5 py-0.5 text-xs font-medium text-amber-800 hover:bg-amber-100 disabled:opacity-60"
                disabled={validating}
                onClick={handleValidate}
                type="button"
              >
                {validating ? "..." : "Valider"}
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
      {quota ? (
        <p className="text-xs text-gray-400">{quota.remaining_places} restantes</p>
      ) : (
        <p className="text-xs text-gray-400">Saisir pour creer</p>
      )}
    </div>
  );
}

// ── Inline source info inputs ─────────────────────────────────────────────────

function InlineEditNumber({
  value,
  onSave,
  readOnly,
}: {
  value: number | null;
  onSave: ((v: number | null) => Promise<void> | void) | undefined;
  readOnly: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);

  function startEdit() {
    if (readOnly || !onSave) return;
    setDraft(value != null ? String(value) : "");
    setEditing(true);
  }

  async function commit() {
    setEditing(false);
    if (!onSave) return;
    const trimmed = draft.trim();
    const newVal = trimmed === "" ? null : Number(trimmed);
    if (newVal === value || (newVal == null && value == null)) return;
    if (trimmed !== "" && isNaN(newVal!)) return;
    setSaving(true);
    try { await onSave(newVal); } finally { setSaving(false); }
  }

  if (!editing) {
    return (
      <button
        className="text-xs text-left disabled:cursor-default"
        disabled={readOnly || saving || !onSave}
        onClick={startEdit}
        title={readOnly ? undefined : "Cliquer pour modifier"}
        type="button"
      >
        {saving ? (
          <span className="text-gray-400">...</span>
        ) : value != null ? (
          <span className={`font-medium ${readOnly ? "text-gray-700" : "text-gray-700 hover:underline"}`}>
            {value} places
          </span>
        ) : (
          <span className={readOnly ? "italic text-gray-400" : "italic text-blue-500 hover:underline"}>
            {readOnly ? "non renseigne" : "ajouter..."}
          </span>
        )}
      </button>
    );
  }

  return (
    <input
      autoFocus
      className="w-20 rounded border border-gray-300 px-1.5 py-0.5 text-xs text-gray-900 focus:outline-none focus:ring-1 focus:ring-[#1E3A8A]"
      min="0"
      onBlur={commit}
      onChange={(e) => setDraft(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter") e.currentTarget.blur();
        if (e.key === "Escape") { setEditing(false); setDraft(""); }
      }}
      type="number"
      value={draft}
    />
  );
}

function InlineEditText({
  value,
  onSave,
  placeholder,
  readOnly,
}: {
  value: string;
  onSave: ((v: string) => Promise<void> | void) | undefined;
  placeholder?: string;
  readOnly: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);

  function startEdit() {
    if (readOnly || !onSave) return;
    setDraft(value ?? "");
    setEditing(true);
  }

  async function commit() {
    setEditing(false);
    if (!onSave) return;
    const trimmed = draft.trim();
    if (trimmed === (value ?? "")) return;
    setSaving(true);
    try { await onSave(trimmed); } finally { setSaving(false); }
  }

  if (!editing) {
    return (
      <button
        className="max-w-[13rem] truncate text-xs text-left disabled:cursor-default"
        disabled={readOnly || saving || !onSave}
        onClick={startEdit}
        title={value || (readOnly ? undefined : "Cliquer pour modifier")}
        type="button"
      >
        {saving ? (
          <span className="text-gray-400">...</span>
        ) : value ? (
          <span className={readOnly ? "text-gray-600" : "text-gray-600 hover:underline"}>{value}</span>
        ) : (
          <span className={readOnly ? "italic text-gray-400" : "italic text-blue-500 hover:underline"}>
            {readOnly ? "—" : "ajouter..."}
          </span>
        )}
      </button>
    );
  }

  return (
    <input
      autoFocus
      className="w-44 rounded border border-gray-300 px-1.5 py-0.5 text-xs text-gray-900 focus:outline-none focus:ring-1 focus:ring-[#1E3A8A]"
      onBlur={commit}
      onChange={(e) => setDraft(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter") e.currentTarget.blur();
        if (e.key === "Escape") { setEditing(false); setDraft(""); }
      }}
      placeholder={placeholder}
      value={draft}
    />
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function getAgreementAvailabilityForYear(
  agreement: Agreement,
  yearFilter: string | undefined,
  academicYears: AcademicYear[],
  availabilities: AgreementYearAvailability[],
  currentYear?: AcademicYear | null,
) {
  const selectedLabel = yearFilter || currentYear?.label;
  const selectedYear =
    academicYears.find((y) => y.label === selectedLabel) ?? currentYear;
  const availability = selectedLabel
    ? availabilities.find(
        (item) =>
          item.agreement_id === agreement.id! &&
          item.academic_year_label === selectedLabel,
      )
    : undefined;

  if (availability) return availability.is_available;
  return selectedYear
    ? isAgreementValidForYear(agreement, selectedYear)
    : agreement.is_active;
}

function filterQuotasForYear(quotas: AgreementQuota[], yearFilter?: string) {
  if (!yearFilter) return quotas;
  return quotas.filter((q) => q.academic_year_label === yearFilter);
}

function isAgreementValidForYear(agreement: Agreement, academicYear: AcademicYear) {
  if (!agreement.is_active) return false;
  if (
    ["closed", "archived", "inactive", "termine", "terminé"].includes(
      (agreement.status ?? "").toLowerCase(),
    )
  ) {
    return false;
  }
  if (agreement.start_date && agreement.start_date > academicYear.end_date)
    return false;
  if (agreement.end_date && agreement.end_date < academicYear.start_date)
    return false;
  return true;
}
