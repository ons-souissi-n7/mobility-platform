"use client";

import { useState } from "react";
import { Check, Eye, Lock, ToggleLeft, ToggleRight } from "lucide-react";

import { AgreementDetailModal } from "@/components/mobility/agreement-detail-modal";
import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import { createIdMap } from "@/lib/utils";
import type {
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
  onEdit,
  onDelete,
}: Readonly<{
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
  onEdit?: (agreement: Agreement) => void;
  onDelete?: (agreement: Agreement) => void;
}>) {
  const [editingN7ForId, setEditingN7ForId] = useState<number | null>(null);
  const [n7EditValue, setN7EditValue] = useState("");
  const [n7Errors, setN7Errors] = useState<Record<number, string>>({});
  const [editingInpForId, setEditingInpForId] = useState<number | null>(null);
  const [inpEditValue, setInpEditValue] = useState("");
  const [inpErrors, setInpErrors] = useState<Record<number, string>>({});
  const [editingDeptId, setEditingDeptId] = useState<number | null>(null);
  const [deptEditValue, setDeptEditValue] = useState("");
  const [deptErrors, setDeptErrors] = useState<Record<number, string>>({});
  const [editingDurationForId, setEditingDurationForId] = useState<number | null>(null);
  const [durationEditValue, setDurationEditValue] = useState("");
  const [durationErrors, setDurationErrors] = useState<Record<number, string>>({});
  const [viewingRow, setViewingRow] = useState<AgreementRow | null>(null);
  const [rowErrors, setRowErrors] = useState<Record<number, string>>({});

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

  function startEditInp(yi: AgreementYear) {
    setEditingInpForId(yi.id);
    setInpEditValue(String(yi.inp_total_places));
    setInpErrors((prev) => ({ ...prev, [yi.id]: "" }));
  }

  async function saveInp(yi: AgreementYear) {
    const val = Number.parseInt(inpEditValue, 10);
    if (!Number.isNaN(val) && val !== yi.inp_total_places) {
      setInpErrors((prev) => ({ ...prev, [yi.id]: "" }));
      try {
        await onEditYearInp(yi, val);
        setEditingInpForId(null);
      } catch (err) {
        setInpErrors((prev) => ({
          ...prev,
          [yi.id]: err instanceof Error ? err.message : "Impossible de modifier.",
        }));
      }
    } else {
      setEditingInpForId(null);
    }
  }

  function startEditN7(yi: AgreementYear) {
    setEditingN7ForId(yi.id);
    setN7EditValue(String(yi.n7_places));
    setN7Errors((prev) => ({ ...prev, [yi.id]: "" }));
  }

  async function saveN7(yi: AgreementYear) {
    const val = Number.parseInt(n7EditValue, 10);
    if (!Number.isNaN(val) && val !== yi.n7_places) {
      setN7Errors((prev) => ({ ...prev, [yi.id]: "" }));
      try {
        await onEditYear(yi, val);
        setEditingN7ForId(null);
      } catch (err) {
        setN7Errors((prev) => ({
          ...prev,
          [yi.id]: err instanceof Error ? err.message : "Impossible de modifier.",
        }));
      }
    } else {
      setEditingN7ForId(null);
    }
  }

  function startEditDuration(yi: AgreementYear) {
    setEditingDurationForId(yi.id);
    setDurationEditValue(yi.duration_weeks !== null ? String(yi.duration_weeks) : "");
    setDurationErrors((prev) => ({ ...prev, [yi.id]: "" }));
  }

  async function saveDuration(yi: AgreementYear) {
    const raw = durationEditValue.trim();
    const val = raw === "" ? null : Number.parseInt(raw, 10);
    if (val !== null && Number.isNaN(val)) { setEditingDurationForId(null); return; }
    if (val !== yi.duration_weeks) {
      setDurationErrors((prev) => ({ ...prev, [yi.id]: "" }));
      try {
        await onEditYearDuration(yi, val);
        setEditingDurationForId(null);
      } catch (err) {
        setDurationErrors((prev) => ({
          ...prev,
          [yi.id]: err instanceof Error ? err.message : "Impossible de modifier.",
        }));
      }
    } else {
      setEditingDurationForId(null);
    }
  }

  function startEditDept(dq: AgreementYearDepartment) {
    setEditingDeptId(dq.id);
    setDeptEditValue(String(dq.estimated_places));
    setDeptErrors((prev) => ({ ...prev, [dq.id]: "" }));
  }

  async function saveDept(dq: AgreementYearDepartment) {
    const val = Number.parseInt(deptEditValue, 10);
    if (!Number.isNaN(val) && val !== dq.estimated_places) {
      setDeptErrors((prev) => ({ ...prev, [dq.id]: "" }));
      try {
        await onSaveDeptQuota(dq, val);
        setEditingDeptId(null);
      } catch (err) {
        setDeptErrors((prev) => ({
          ...prev,
          [dq.id]: err instanceof Error ? err.message : "Impossible de modifier.",
        }));
      }
    } else {
      setEditingDeptId(null);
    }
  }

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

        // ── Inactif : rien à afficher sauf le statut + bouton Activer ────────
        if (!yearInstance.is_active && !yearInstance.is_validated) {
          return (
            <div className="flex flex-wrap items-center gap-2">
              <YearStatusBadge instance={yearInstance} />
              {!isYearClosed && !isYearLocked && (
                <button
                  className="rounded border border-gray-200 bg-white px-2 py-0.5 text-[10px] text-gray-600 hover:bg-gray-50"
                  onClick={() => onToggleYearActive(yearInstance)}
                  type="button"
                >
                  <ToggleLeft className="mr-0.5 inline text-gray-400" size={10} />
                  Activer
                </button>
              )}
            </div>
          );
        }

        // ── Actif ou validé : affichage complet ───────────────────────────────
        const locked = yearInstance.is_validated || isYearClosed || isYearLocked;
        const deptTotal = deptQuotas.reduce((s, dq) => s + dq.effective_places, 0);
        const isInconsistent = deptQuotas.length > 0 && deptTotal !== yearInstance.n7_places;

        return (
          <div className="min-w-52 space-y-2">
            {/* Statut + INP + N7 */}
            <div className="flex flex-wrap items-center gap-2">
              <YearStatusBadge instance={yearInstance} />

              {/* INP inline-editable */}
              {!locked && editingInpForId === yearInstance.id ? (
                <div className="flex flex-col">
                  <div className="flex items-center gap-0.5">
                    <span className="text-[10px] text-gray-500">INP :</span>
                    <input
                      autoFocus
                      className={`w-14 rounded border px-1 py-0.5 text-xs text-center focus:outline-none focus:ring-1 ${inpErrors[yearInstance.id] ? "border-red-400 focus:ring-red-400" : "border-orange-300 focus:ring-orange-400"}`}
                      min="0"
                      onBlur={() => saveInp(yearInstance)}
                      onChange={(e) => setInpEditValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter")  { void saveInp(yearInstance); }
                        if (e.key === "Escape") { setEditingInpForId(null); setInpErrors((p) => ({ ...p, [yearInstance.id]: "" })); }
                      }}
                      type="number"
                      value={inpEditValue}
                    />
                  </div>
                  {inpErrors[yearInstance.id] && (
                    <p className="mt-0.5 max-w-32 text-[10px] text-red-600">{inpErrors[yearInstance.id]}</p>
                  )}
                </div>
              ) : (
                <button
                  className={`rounded px-1.5 py-0.5 text-xs font-semibold ${
                    locked ? "cursor-default text-gray-500" : "text-orange-700 hover:bg-orange-50 cursor-text"
                  }`}
                  disabled={locked}
                  onClick={() => !locked && startEditInp(yearInstance)}
                  title={locked ? "Validé — non modifiable" : "Cliquer pour modifier le quota INP"}
                  type="button"
                >
                  INP : {yearInstance.inp_total_places}
                  {locked && <Lock className="ml-1 inline" size={9} />}
                </button>
              )}
              <span className="text-[10px] text-gray-400">→</span>

              {/* N7 inline-editable */}
              {!locked && editingN7ForId === yearInstance.id ? (
                <div className="flex flex-col">
                  <input
                    autoFocus
                    className={`w-14 rounded border px-1 py-0.5 text-xs text-center focus:outline-none focus:ring-1 ${n7Errors[yearInstance.id] ? "border-red-400 focus:ring-red-400" : "border-blue-300 focus:ring-blue-400"}`}
                    min="0"
                    onBlur={() => saveN7(yearInstance)}
                    onChange={(e) => setN7EditValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter")  { void saveN7(yearInstance); }
                      if (e.key === "Escape") { setEditingN7ForId(null); setN7Errors((p) => ({ ...p, [yearInstance.id]: "" })); }
                    }}
                    type="number"
                    value={n7EditValue}
                  />
                  {n7Errors[yearInstance.id] && (
                    <p className="mt-0.5 max-w-32 text-[10px] text-red-600">{n7Errors[yearInstance.id]}</p>
                  )}
                </div>
              ) : (
                <button
                  className={`rounded px-1.5 py-0.5 text-xs font-semibold ${
                    locked ? "cursor-default text-gray-600" : "text-[#1E3A8A] hover:bg-blue-50 cursor-text"
                  }`}
                  disabled={locked}
                  onClick={() => !locked && startEditN7(yearInstance)}
                  title={locked ? "Validé — non modifiable" : "Cliquer pour modifier le quota N7"}
                  type="button"
                >
                  N7 : {yearInstance.n7_places}
                  {locked && <Lock className="ml-1 inline" size={9} />}
                </button>
              )}
            </div>

            {/* Durée de la mobilité inline-editable */}
            <div className="flex items-center gap-1.5">
              {!locked && editingDurationForId === yearInstance.id ? (
                <div className="flex flex-col">
                  <div className="flex items-center gap-0.5">
                    <span className="text-[10px] text-gray-500">Durée :</span>
                    <input
                      autoFocus
                      className={`w-14 rounded border px-1 py-0.5 text-xs text-center focus:outline-none focus:ring-1 ${durationErrors[yearInstance.id] ? "border-red-400 focus:ring-red-400" : "border-green-300 focus:ring-green-400"}`}
                      min="1"
                      placeholder="sem."
                      onBlur={() => saveDuration(yearInstance)}
                      onChange={(e) => setDurationEditValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter")  { void saveDuration(yearInstance); }
                        if (e.key === "Escape") { setEditingDurationForId(null); setDurationErrors((p) => ({ ...p, [yearInstance.id]: "" })); }
                      }}
                      type="number"
                      value={durationEditValue}
                    />
                    <span className="text-[10px] text-gray-400">sem.</span>
                  </div>
                  {durationErrors[yearInstance.id] && (
                    <p className="mt-0.5 max-w-32 text-[10px] text-red-600">{durationErrors[yearInstance.id]}</p>
                  )}
                </div>
              ) : (
                <button
                  className={`rounded px-1.5 py-0.5 text-xs font-semibold ${
                    locked ? "cursor-default text-gray-500" : "text-green-700 hover:bg-green-50 cursor-text"
                  }`}
                  disabled={locked}
                  onClick={() => !locked && startEditDuration(yearInstance)}
                  title={locked ? "Validé — non modifiable" : "Cliquer pour modifier la durée de la mobilité (en semaines)"}
                  type="button"
                >
                  Durée : {yearInstance.duration_weeks !== null ? `${yearInstance.duration_weeks} sem.` : "—"}
                  {locked && yearInstance.duration_weeks !== null && <Lock className="ml-1 inline" size={9} />}
                </button>
              )}
            </div>

            {/* Répartition par département — visible et éditable inline */}
            {deptQuotas.length > 0 ? (
              <div className="flex flex-wrap items-center gap-1.5">
                {deptQuotas.map((dq) => {
                  const dept = departmentById.get(dq.department_id);
                  const code = dept?.code ?? String(dq.department_id);
                  const isEditingThis = !locked && editingDeptId === dq.id;
                  return (
                    <span key={dq.id} className="inline-flex items-center gap-0.5">
                      <span className="text-[10px] font-medium text-gray-500">{code} :</span>
                      {isEditingThis ? (
                        <span className="inline-flex flex-col">
                          <input
                            autoFocus
                            className={`w-10 rounded border px-0.5 py-0.5 text-[10px] text-center focus:outline-none focus:ring-1 ${deptErrors[dq.id] ? "border-red-400 focus:ring-red-400" : "border-blue-300 focus:ring-blue-400"}`}
                            min="0"
                            onBlur={() => saveDept(dq)}
                            onChange={(e) => setDeptEditValue(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter")  { void saveDept(dq); }
                              if (e.key === "Escape") { setEditingDeptId(null); setDeptErrors((p) => ({ ...p, [dq.id]: "" })); }
                            }}
                            type="number"
                            value={deptEditValue}
                          />
                          {deptErrors[dq.id] && (
                            <span className="text-[9px] text-red-600">{deptErrors[dq.id]}</span>
                          )}
                        </span>
                      ) : (
                        <button
                          className={`rounded px-1 py-0.5 text-[10px] font-semibold ${
                            locked ? "cursor-default text-gray-700" : "text-[#1E3A8A] hover:bg-blue-50 cursor-text"
                          } ${dq.adjusted_places !== null ? "underline decoration-dotted" : ""}`}
                          disabled={locked}
                          onClick={() => !locked && startEditDept(dq)}
                          title={
                            locked
                              ? "Validé"
                              : dq.adjusted_places !== null
                                ? `Ajusté manuellement (estimé : ${dq.estimated_places})`
                                : "Cliquer pour modifier"
                          }
                          type="button"
                        >
                          {dq.effective_places}
                        </button>
                      )}
                    </span>
                  );
                })}
                {isInconsistent && (
                  <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] text-red-600">
                    {deptTotal} ≠ N7 {yearInstance.n7_places}
                  </span>
                )}
              </div>
            ) : null}

            {/* Actions (uniquement si actif et non validé) */}
            {!locked && (
              <div className="space-y-1">
                <div className="flex flex-wrap gap-1">
                  <button
                    className="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-600 hover:bg-gray-50"
                    onClick={() => onToggleYearActive(yearInstance)}
                    type="button"
                  >
                    <ToggleRight className="mr-0.5 inline text-green-500" size={10} />
                    Désactiver
                  </button>
                  <button
                    className="rounded border border-green-300 bg-green-50 px-1.5 py-0.5 text-[10px] text-green-700 hover:bg-green-100"
                    onClick={async () => {
                      setRowErrors((prev) => ({ ...prev, [yearInstance.id]: "" }));
                      try {
                        await onValidateYear(yearInstance);
                      } catch (err) {
                        setRowErrors((prev) => ({
                          ...prev,
                          [yearInstance.id]: err instanceof Error ? err.message : "Impossible de valider.",
                        }));
                      }
                    }}
                    type="button"
                  >
                    <Check className="mr-0.5 inline" size={9} /> Valider
                  </button>
                </div>
                {rowErrors[yearInstance.id] && (
                  <p className="max-w-52 text-[10px] text-red-600">
                    {rowErrors[yearInstance.id]}
                  </p>
                )}
              </div>
            )}
          </div>
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
          agreement={viewingRow.agreement}
          allAgreementYears={agreementYears}
          allDeptQuotas={agreementYearDepartments}
          university={universityById.get(viewingRow.agreement.partner_university_id)}
          category={categoryById.get(viewingRow.agreement.category_id ?? -1)}
          departments={departmentById}
          levels={levelById}
          onClose={() => setViewingRow(null)}
        />
      )}
    </>
  );
}

function DirectionBadge({ direction }: { direction: string }) {
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

function YearStatusBadge({ instance }: { instance: AgreementYear }) {
  if (instance.is_validated) {
    return (
      <span className="inline-flex items-center gap-0.5 rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700">
        <Lock size={8} /> Validé
      </span>
    );
  }
  return instance.is_active ? (
    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
      Actif
    </span>
  ) : (
    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-500">
      Inactif
    </span>
  );
}
