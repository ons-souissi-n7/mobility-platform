"use client";

import { AlertTriangle, Check, ChevronDown, ChevronRight, RotateCw } from "lucide-react";
import { useState } from "react";

import { Pagination } from "@/components/ui/pagination";
import type { Country, Department, Level, Parcours, RawImport } from "@/lib/api/types";
import { type StudentImportCorrection } from "@/lib/api/student-mutations";

const STUDENT_FIELD_LABELS: Record<string, string> = {
  ine: "INE",
  first_name: "Prénom",
  last_name: "Nom",
  email: "Email",
  gender: "Genre",
  department_code: "Code département",
  level_code: "Code niveau",
  parcours_code: "Code parcours",
  gpa: "Moyenne (GPA)",
  nationality_iso2: "Nationalité",
};

function PayloadGrid({ payload }: { payload: Record<string, unknown> }) {
  const entries = Object.entries(payload).filter(([, v]) => v !== null && v !== undefined && v !== "");
  if (entries.length === 0) return <p className="text-xs text-gray-400 italic">Aucune donnée disponible</p>;

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">
            {STUDENT_FIELD_LABELS[key] ?? key}
          </dt>
          <dd className="mt-0.5 font-mono text-xs text-gray-800 break-all">
            {String(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

type CorrectionForm = {
  ine: string;
  first_name: string;
  last_name: string;
  email: string;
  gender: string;
  department_id: number | "";
  level_id: number | "";
  parcours_id: number | "";
  gpa: string;
  nationality_iso2: string;
};

function buildInitialForm(
  payload: Record<string, unknown>,
  departments: Department[],
  levels: Level[],
  parcourses: Parcours[],
): CorrectionForm {
  const deptCode = String(payload.department_code ?? "").toUpperCase();
  const levelCode = String(payload.level_code ?? "").toUpperCase();
  const parcoursCode = String(payload.parcours_code ?? "").toUpperCase();
  return {
    ine: String(payload.ine ?? ""),
    first_name: String(payload.first_name ?? ""),
    last_name: String(payload.last_name ?? ""),
    email: String(payload.email ?? ""),
    gender: String(payload.gender ?? ""),
    department_id: departments.find((d) => d.code.toUpperCase() === deptCode)?.id ?? "",
    level_id: levels.find((l) => l.code.toUpperCase() === levelCode)?.id ?? "",
    parcours_id: parcourses.find((p) => p.code.toUpperCase() === parcoursCode)?.id ?? "",
    gpa: payload.gpa !== null && payload.gpa !== undefined ? String(payload.gpa) : "",
    nationality_iso2: String(payload.nationality_iso2 ?? ""),
  };
}

function buildCorrection(form: CorrectionForm): StudentImportCorrection {
  const c: StudentImportCorrection = {};
  if (form.department_id !== "") c.department_id = form.department_id;
  if (form.level_id !== "") c.level_id = form.level_id;
  if (form.parcours_id !== "") c.parcours_id = form.parcours_id;
  if (form.ine) c.ine = form.ine;
  if (form.first_name) c.first_name = form.first_name;
  if (form.last_name) c.last_name = form.last_name;
  if (form.email) c.email = form.email;
  if (form.gender) c.gender = form.gender;
  if (form.gpa !== "") c.gpa = Number(form.gpa);
  if (form.nationality_iso2) c.nationality_iso2 = form.nationality_iso2;
  return c;
}

export function StudentImportErrorsPanel({
  countries,
  departments,
  errors,
  isBusy,
  levels,
  onIgnore,
  onRetry,
  parcourses,
  title = "Erreurs d'import étudiants",
  totalCount,
  page = 1,
  pageSize = 25,
  onPageChange,
}: Readonly<{
  countries: Country[];
  departments: Department[];
  errors: RawImport[];
  isBusy: boolean;
  levels: Level[];
  onIgnore: (error: RawImport) => Promise<void>;
  onRetry: (error: RawImport, correction: StudentImportCorrection) => Promise<void>;
  parcourses: Parcours[];
  title?: string;
  totalCount?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
}>) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [forms, setForms] = useState<Record<number, CorrectionForm>>({});

  if (errors.length === 0) return null;

  async function runAction(fn: () => Promise<void>, id: number) {
    setActiveId(id);
    setActionError(null);
    try {
      await fn();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Erreur lors de l'opération.");
    } finally {
      setActiveId(null);
    }
  }

  function getForm(error: RawImport): CorrectionForm {
    if (!forms[error.id]) {
      const initial = buildInitialForm(error.payload, departments, levels, parcourses);
      setForms((prev) => ({ ...prev, [error.id]: initial }));
      return initial;
    }
    return forms[error.id];
  }

  function updateForm(id: number, patch: Partial<CorrectionForm>) {
    setForms((prev) => ({ ...prev, [id]: { ...(prev[id] ?? buildInitialForm({}, departments, levels, parcourses)), ...patch } }));
  }

  function toggleExpand(id: number) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  const sortedDepts = [...departments].sort((a, b) => a.code.localeCompare(b.code));
  const sortedLevels = [...levels].sort((a, b) => a.code.localeCompare(b.code));
  const sortedParcours = [...parcourses].sort((a, b) => a.code.localeCompare(b.code));
  const sortedCountries = [...countries].sort((a, b) => a.name_fr.localeCompare(b.name_fr));

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          {title} ({totalCount ?? errors.length})
        </h3>
      </div>

      {actionError && (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </div>
      )}

      <div className="mt-4 space-y-2">
        {errors.map((error) => {
          const busy = isBusy || activeId === error.id;
          const isExpanded = expandedId === error.id;
          const form = isExpanded ? getForm(error) : null;

          return (
            <div
              key={error.id}
              className="rounded-md border border-amber-200 bg-white overflow-hidden"
            >
              <button
                type="button"
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-amber-50 transition-colors"
                onClick={() => toggleExpand(error.id)}
              >
                <span className="shrink-0 text-amber-500">
                  {isExpanded
                    ? <ChevronDown className="h-4 w-4" />
                    : <ChevronRight className="h-4 w-4" />}
                </span>
                <span className="font-mono text-xs text-gray-600 shrink-0 w-32 truncate">
                  {error.external_id || "—"}
                </span>
                <span className="shrink-0 text-xs text-gray-400 w-20 truncate">
                  {error.source}
                </span>
                <span className="flex-1 text-xs text-red-700 truncate">
                  {error.error_message || "Erreur inconnue"}
                </span>
                <span className="shrink-0 ml-2 rounded-full px-2 py-0.5 text-[10px] font-medium bg-red-100 text-red-700">
                  {error.status}
                </span>
              </button>

              {isExpanded && form && (
                <div className="border-t border-amber-100 px-4 py-4 grid grid-cols-1 gap-6 sm:grid-cols-2">
                  {/* Left: full record + error */}
                  <div>
                    <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Enregistrement complet
                    </h4>
                    <div className="rounded-md border border-gray-100 bg-gray-50 p-3">
                      <PayloadGrid payload={error.payload} />
                    </div>
                    <div className="mt-3 rounded-md border border-red-100 bg-red-50 px-3 py-2">
                      <p className="text-xs font-semibold text-red-700">Motif d&apos;échec</p>
                      <p className="mt-0.5 text-xs text-red-600">{error.error_message || "Erreur inconnue"}</p>
                    </div>
                  </div>

                  {/* Right: correction form */}
                  <div>
                    <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Corriger et relancer
                    </h4>

                    <div className="grid grid-cols-1 gap-2">
                      <CorrField label="N°INE" value={form.ine} onChange={(v) => updateForm(error.id, { ine: v })} />
                      <CorrField label="Prénom" value={form.first_name} onChange={(v) => updateForm(error.id, { first_name: v })} />
                      <CorrField label="Nom" value={form.last_name} onChange={(v) => updateForm(error.id, { last_name: v })} />
                      <CorrField label="Email" value={form.email} onChange={(v) => updateForm(error.id, { email: v })} />

                      <label className="block">
                        <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Genre</span>
                        <select
                          className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900"
                          value={form.gender}
                          onChange={(e) => updateForm(error.id, { gender: e.target.value })}
                        >
                          <option value="">—</option>
                          <option value="M">M — Masculin</option>
                          <option value="F">F — Féminin</option>
                        </select>
                      </label>

                      <label className="block">
                        <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Département</span>
                        <select
                          className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900"
                          value={form.department_id}
                          onChange={(e) => updateForm(error.id, { department_id: e.target.value ? Number(e.target.value) : "" })}
                        >
                          <option value="">— Sélectionner —</option>
                          {sortedDepts.map((d) => (
                            <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
                          ))}
                        </select>
                      </label>

                      <label className="block">
                        <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Niveau</span>
                        <select
                          className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900"
                          value={form.level_id}
                          onChange={(e) => updateForm(error.id, { level_id: e.target.value ? Number(e.target.value) : "" })}
                        >
                          <option value="">— Sélectionner —</option>
                          {sortedLevels.map((l) => (
                            <option key={l.id} value={l.id}>{l.code} — {l.name}</option>
                          ))}
                        </select>
                      </label>

                      <label className="block">
                        <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Parcours</span>
                        <select
                          className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900"
                          value={form.parcours_id}
                          onChange={(e) => updateForm(error.id, { parcours_id: e.target.value ? Number(e.target.value) : "" })}
                        >
                          <option value="">— Sélectionner —</option>
                          {sortedParcours.map((p) => (
                            <option key={p.id} value={p.id}>{p.code} — {p.label}</option>
                          ))}
                        </select>
                      </label>

                      <label className="block">
                          <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Moyenne (GPA)</span>
                          <input
                            className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1.5 text-xs text-gray-900 font-mono focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A]"
                            type="number"
                            min="0"
                            max="4"
                            step="0.01"
                            value={form.gpa}
                            onChange={(e) => updateForm(error.id, { gpa: e.target.value })}
                          />
                        </label>

                      <label className="block">
                          <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Nationalité (pays)</span>
                          <select
                            className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900"
                            value={form.nationality_iso2}
                            onChange={(e) => updateForm(error.id, { nationality_iso2: e.target.value })}
                          >
                            <option value="">— Sélectionner —</option>
                            {sortedCountries.map((c) => (
                              <option key={c.id} value={c.iso2}>{c.name_fr} ({c.iso2})</option>
                            ))}
                          </select>
                        </label>
                    </div>

                    <div className="mt-4 flex gap-2">
                      <button
                        className="inline-flex h-8 items-center gap-1.5 rounded-md bg-[#1E3A8A] px-3 text-xs font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={busy}
                        onClick={() => runAction(() => onRetry(error, buildCorrection(form)), error.id)}
                        type="button"
                      >
                        <RotateCw className="h-3 w-3" />
                        Relancer
                      </button>
                      <button
                        className="inline-flex h-8 items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={busy}
                        onClick={() => runAction(() => onIgnore(error), error.id)}
                        type="button"
                      >
                        <Check className="h-3 w-3" />
                        Ignorer
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {onPageChange && totalCount !== undefined && totalCount > pageSize && (
        <div className="mt-4 border-t border-amber-100 pt-3">
          <Pagination
            page={page}
            totalPages={Math.ceil(totalCount / pageSize)}
            totalItems={totalCount}
            pageSize={pageSize}
            onPageChange={onPageChange}
          />
        </div>
      )}
    </div>
  );
}

function CorrField({
  label,
  value,
  type = "text",
  onChange,
}: Readonly<{
  label: string;
  value: string;
  type?: string;
  onChange: (v: string) => void;
}>) {
  return (
    <label className="block">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">{label}</span>
      <input
        className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1.5 text-xs text-gray-900 font-mono focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A]"
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
