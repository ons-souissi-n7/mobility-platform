"use client";

import { useState } from "react";
import { Check, Lock, ToggleLeft, ToggleRight } from "lucide-react";

import type { AgreementYear, AgreementYearDepartment, Department } from "@/lib/api/types";

/**
 * Affichage + édition inline d'une instance annuelle (AgreementYear) : statut,
 * INP/N7, durée, répartition par département, activation et validation.
 *
 * Composant autonome (état local par instance, pas d'état indexé par id côté
 * parent) afin d'être réutilisable à la fois dans la colonne "Année en cours"
 * du tableau des accords et dans la fiche historique complète d'un accord,
 * qui affiche une carte de ce type par année universitaire.
 */
export function AgreementYearCell({
  actionsDisabled = false,
  deptQuotas,
  departmentById,
  onEditYear,
  onEditYearDuration,
  onEditYearInp,
  onSaveDeptQuota,
  onToggleActive,
  onValidateYear,
  yearInstance,
}: Readonly<{
  actionsDisabled?: boolean;
  deptQuotas: AgreementYearDepartment[];
  departmentById: Map<number, Department>;
  onEditYear: (yi: AgreementYear, n7Places: number) => Promise<void>;
  onEditYearDuration: (yi: AgreementYear, durationWeeks: number | null) => Promise<void>;
  onEditYearInp: (yi: AgreementYear, inpPlaces: number) => Promise<void>;
  onSaveDeptQuota: (dq: AgreementYearDepartment, places: number) => Promise<void>;
  onToggleActive: (yi: AgreementYear) => Promise<void>;
  onValidateYear: (yi: AgreementYear) => Promise<void>;
  yearInstance: AgreementYear;
}>) {
  const [editingInp, setEditingInp] = useState(false);
  const [inpValue, setInpValue] = useState(String(yearInstance.inp_total_places));
  const [inpError, setInpError] = useState("");

  const [editingN7, setEditingN7] = useState(false);
  const [n7Value, setN7Value] = useState(String(yearInstance.n7_places));
  const [n7Error, setN7Error] = useState("");

  const [editingDuration, setEditingDuration] = useState(false);
  const [durationValue, setDurationValue] = useState(
    yearInstance.duration_weeks !== null ? String(yearInstance.duration_weeks) : "",
  );
  const [durationError, setDurationError] = useState("");

  const [editingDeptId, setEditingDeptId] = useState<number | null>(null);
  const [deptValue, setDeptValue] = useState("");
  const [deptErrors, setDeptErrors] = useState<Record<number, string>>({});

  const [rowError, setRowError] = useState("");

  function startEditInp() {
    setInpValue(String(yearInstance.inp_total_places));
    setInpError("");
    setEditingInp(true);
  }

  async function saveInp() {
    const val = Number.parseInt(inpValue, 10);
    if (!Number.isNaN(val) && val !== yearInstance.inp_total_places) {
      try {
        await onEditYearInp(yearInstance, val);
        setEditingInp(false);
      } catch (err) {
        setInpError(err instanceof Error ? err.message : "Impossible de modifier.");
      }
    } else {
      setEditingInp(false);
    }
  }

  function startEditN7() {
    setN7Value(String(yearInstance.n7_places));
    setN7Error("");
    setEditingN7(true);
  }

  async function saveN7() {
    const val = Number.parseInt(n7Value, 10);
    if (!Number.isNaN(val) && val !== yearInstance.n7_places) {
      try {
        await onEditYear(yearInstance, val);
        setEditingN7(false);
      } catch (err) {
        setN7Error(err instanceof Error ? err.message : "Impossible de modifier.");
      }
    } else {
      setEditingN7(false);
    }
  }

  function startEditDuration() {
    setDurationValue(yearInstance.duration_weeks !== null ? String(yearInstance.duration_weeks) : "");
    setDurationError("");
    setEditingDuration(true);
  }

  async function saveDuration() {
    const raw = durationValue.trim();
    const val = raw === "" ? null : Number.parseInt(raw, 10);
    if (val !== null && Number.isNaN(val)) { setEditingDuration(false); return; }
    if (val !== yearInstance.duration_weeks) {
      try {
        await onEditYearDuration(yearInstance, val);
        setEditingDuration(false);
      } catch (err) {
        setDurationError(err instanceof Error ? err.message : "Impossible de modifier.");
      }
    } else {
      setEditingDuration(false);
    }
  }

  function startEditDept(dq: AgreementYearDepartment) {
    setEditingDeptId(dq.id);
    setDeptValue(String(dq.estimated_places));
    setDeptErrors((prev) => ({ ...prev, [dq.id]: "" }));
  }

  async function saveDept(dq: AgreementYearDepartment) {
    const val = Number.parseInt(deptValue, 10);
    if (!Number.isNaN(val) && val !== dq.estimated_places) {
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

  // ── Inactif, non validé : rien à afficher sauf le statut + bouton Activer ──
  if (!yearInstance.is_active && !yearInstance.is_validated) {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <YearStatusBadge instance={yearInstance} />
        {!actionsDisabled && (
          <button
            className="rounded border border-gray-200 bg-white px-2 py-0.5 text-[10px] text-gray-600 hover:bg-gray-50"
            onClick={() => void onToggleActive(yearInstance)}
            type="button"
          >
            <ToggleLeft className="mr-0.5 inline text-gray-400" size={10} />
            Activer
          </button>
        )}
      </div>
    );
  }

  // ── Actif ou validé : affichage complet ─────────────────────────────────
  const locked = yearInstance.is_validated || actionsDisabled;
  const deptTotal = deptQuotas.reduce((s, dq) => s + dq.effective_places, 0);
  const isInconsistent = deptQuotas.length > 0 && deptTotal !== yearInstance.n7_places;

  return (
    <div className="min-w-52 space-y-2">
      {/* Statut + INP + N7 */}
      <div className="flex flex-wrap items-center gap-2">
        <YearStatusBadge instance={yearInstance} />

        {!locked && editingInp ? (
          <div className="flex flex-col">
            <div className="flex items-center gap-0.5">
              <span className="text-[10px] text-gray-500">INP :</span>
              <input
                autoFocus
                className={`w-14 rounded border px-1 py-0.5 text-xs text-center focus:outline-none focus:ring-1 ${inpError ? "border-red-400 focus:ring-red-400" : "border-orange-300 focus:ring-orange-400"}`}
                min="0"
                onBlur={() => void saveInp()}
                onChange={(e) => setInpValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter")  { void saveInp(); }
                  if (e.key === "Escape") { setEditingInp(false); setInpError(""); }
                }}
                type="number"
                value={inpValue}
              />
            </div>
            {inpError && <p className="mt-0.5 max-w-32 text-[10px] text-red-600">{inpError}</p>}
          </div>
        ) : (
          <button
            className={`rounded px-1.5 py-0.5 text-xs font-semibold ${
              locked ? "cursor-default text-gray-500" : "text-orange-700 hover:bg-orange-50 cursor-text"
            }`}
            disabled={locked}
            onClick={() => !locked && startEditInp()}
            title={locked ? "Validé — non modifiable" : "Cliquer pour modifier le quota INP"}
            type="button"
          >
            INP : {yearInstance.inp_total_places}
            {locked && <Lock className="ml-1 inline" size={9} />}
          </button>
        )}
        <span className="text-[10px] text-gray-400">→</span>

        {!locked && editingN7 ? (
          <div className="flex flex-col">
            <input
              autoFocus
              className={`w-14 rounded border px-1 py-0.5 text-xs text-center focus:outline-none focus:ring-1 ${n7Error ? "border-red-400 focus:ring-red-400" : "border-blue-300 focus:ring-blue-400"}`}
              min="0"
              onBlur={() => void saveN7()}
              onChange={(e) => setN7Value(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter")  { void saveN7(); }
                if (e.key === "Escape") { setEditingN7(false); setN7Error(""); }
              }}
              type="number"
              value={n7Value}
            />
            {n7Error && <p className="mt-0.5 max-w-32 text-[10px] text-red-600">{n7Error}</p>}
          </div>
        ) : (
          <button
            className={`rounded px-1.5 py-0.5 text-xs font-semibold ${
              locked ? "cursor-default text-gray-600" : "text-[#1E3A8A] hover:bg-blue-50 cursor-text"
            }`}
            disabled={locked}
            onClick={() => !locked && startEditN7()}
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
        {!locked && editingDuration ? (
          <div className="flex flex-col">
            <div className="flex items-center gap-0.5">
              <span className="text-[10px] text-gray-500">Durée :</span>
              <input
                autoFocus
                className={`w-14 rounded border px-1 py-0.5 text-xs text-center focus:outline-none focus:ring-1 ${durationError ? "border-red-400 focus:ring-red-400" : "border-green-300 focus:ring-green-400"}`}
                min="1"
                placeholder="sem."
                onBlur={() => void saveDuration()}
                onChange={(e) => setDurationValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter")  { void saveDuration(); }
                  if (e.key === "Escape") { setEditingDuration(false); setDurationError(""); }
                }}
                type="number"
                value={durationValue}
              />
              <span className="text-[10px] text-gray-400">sem.</span>
            </div>
            {durationError && (
              <p className="mt-0.5 max-w-32 text-[10px] text-red-600">{durationError}</p>
            )}
          </div>
        ) : (
          <button
            className={`rounded px-1.5 py-0.5 text-xs font-semibold ${
              locked ? "cursor-default text-gray-500" : "text-green-700 hover:bg-green-50 cursor-text"
            }`}
            disabled={locked}
            onClick={() => !locked && startEditDuration()}
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
                      onBlur={() => void saveDept(dq)}
                      onChange={(e) => setDeptValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter")  { void saveDept(dq); }
                        if (e.key === "Escape") { setEditingDeptId(null); setDeptErrors((p) => ({ ...p, [dq.id]: "" })); }
                      }}
                      type="number"
                      value={deptValue}
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
              onClick={() => void onToggleActive(yearInstance)}
              type="button"
            >
              <ToggleRight className="mr-0.5 inline text-green-500" size={10} />
              Désactiver
            </button>
            <button
              className="rounded border border-green-300 bg-green-50 px-1.5 py-0.5 text-[10px] text-green-700 hover:bg-green-100"
              onClick={async () => {
                setRowError("");
                try {
                  await onValidateYear(yearInstance);
                } catch (err) {
                  setRowError(err instanceof Error ? err.message : "Impossible de valider.");
                }
              }}
              type="button"
            >
              <Check className="mr-0.5 inline" size={9} /> Valider
            </button>
          </div>
          {rowError && <p className="max-w-52 text-[10px] text-red-600">{rowError}</p>}
        </div>
      )}
    </div>
  );
}

export function YearStatusBadge({ instance }: { instance: AgreementYear }) {
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
