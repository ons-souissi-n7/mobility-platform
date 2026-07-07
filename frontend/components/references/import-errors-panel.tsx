"use client";

import { AlertTriangle, Check, ChevronDown, ChevronRight, RefreshCw, RotateCw } from "lucide-react";
import { useState } from "react";

import { Pagination } from "@/components/ui/pagination";
import type { Country, RawImport } from "@/lib/api/types";
import type { DepartmentImportCorrection, UniversityImportCorrection } from "@/lib/api/reference-mutations";

export type LevelImportCorrection = { code?: string; name?: string; pegase_id?: string };

const UNIVERSITY_LABELS: Record<string, string> = {
  moveon_id: "ID MoveON",
  name: "Nom",
  short_name: "Nom court",
  translated_name: "Nom traduit",
  erasmus_code: "Code Erasmus",
  city: "Ville",
  url: "Site web",
  email: "Email",
};

const DEPARTMENT_LABELS: Record<string, string> = {
  pegase_id: "ID Pégase",
  code: "Code",
  name: "Nom",
};

function getLabels(entity: string | undefined): Record<string, string> {
  if (entity === "partner_university") return UNIVERSITY_LABELS;
  if (entity === "department") return DEPARTMENT_LABELS;
  if (entity === "level") return DEPARTMENT_LABELS;
  return {};
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    return obj.name ? String(obj.name) : JSON.stringify(value);
  }
  return String(value);
}

function PayloadGrid({ entity, payload }: { entity: string | undefined; payload: Record<string, unknown> }) {
  const labels = getLabels(entity);
  const entries = Object.entries(payload).filter(([, v]) => v !== null && v !== undefined && v !== "");
  if (entries.length === 0) return <p className="text-xs italic text-gray-400">Aucune donnée disponible</p>;
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">
            {labels[key] ?? key}
          </dt>
          <dd className="mt-0.5 font-mono text-xs text-gray-800 break-all">
            {renderValue(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

// ── University form ────────────────────────────────────────────────────────

type UniversityForm = {
  name: string;
  short_name: string;
  translated_name: string;
  erasmus_code: string;
  city: string;
  url: string;
  email: string;
  country_id: number | "";
};

function buildUniversityForm(payload: Record<string, unknown>): UniversityForm {
  return {
    name: String(payload.name ?? ""),
    short_name: String(payload.short_name ?? ""),
    translated_name: String(payload.translated_name ?? ""),
    erasmus_code: String(payload.erasmus_code ?? ""),
    city: String(payload.city ?? ""),
    url: String(payload.url ?? ""),
    email: String(payload.email ?? ""),
    country_id: "",
  };
}

function buildUniversityCorrection(form: UniversityForm): UniversityImportCorrection {
  const c: UniversityImportCorrection = {};
  if (form.country_id !== "") c.country_id = form.country_id;
  if (form.name) c.name = form.name;
  if (form.short_name) c.short_name = form.short_name;
  if (form.translated_name) c.translated_name = form.translated_name;
  if (form.erasmus_code) c.erasmus_code = form.erasmus_code;
  if (form.city) c.city = form.city;
  if (form.url) c.url = form.url;
  if (form.email) c.email = form.email;
  return c;
}

// ── Department / Level form ────────────────────────────────────────────────

type DeptLevelForm = { code: string; name: string; pegase_id: string };

function buildDeptLevelForm(payload: Record<string, unknown>): DeptLevelForm {
  return {
    code: String(payload.code ?? ""),
    name: String(payload.name ?? ""),
    pegase_id: String(payload.pegase_id ?? ""),
  };
}

function buildDeptCorrection(form: DeptLevelForm): DepartmentImportCorrection {
  const c: DepartmentImportCorrection = {};
  if (form.code) c.code = form.code;
  if (form.name) c.name = form.name;
  if (form.pegase_id) c.pegase_id = form.pegase_id;
  return c;
}

// ── Component ──────────────────────────────────────────────────────────────

type ImportErrorsPanelProps = {
  countries: Country[];
  errors: RawImport[];
  isBusy: boolean;
  onIgnore: (error: RawImport) => Promise<void>;
  onRetry?: (error: RawImport, correction: UniversityImportCorrection | DepartmentImportCorrection | LevelImportCorrection) => Promise<void>;
  onForce?: (error: RawImport) => Promise<void>;
  title?: string;
  totalCount?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
};

export function ImportErrorsPanel({
  countries,
  errors,
  isBusy,
  onIgnore,
  onRetry,
  onForce,
  title,
  totalCount,
  page = 1,
  pageSize = 25,
  onPageChange,
}: ImportErrorsPanelProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [univForms, setUnivForms] = useState<Record<number, UniversityForm>>({});
  const [deptForms, setDeptForms] = useState<Record<number, DeptLevelForm>>({});

  if (errors.length === 0) return null;

  const sortedCountries = [...countries].sort((a, b) => a.name_fr.localeCompare(b.name_fr));

  async function runAction(fn: () => Promise<void>, id: number) {
    setActiveId(id);
    setActionError(null);
    try {
      await fn();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Erreur inconnue lors de l'opération.");
    } finally {
      setActiveId(null);
    }
  }

  function toggleExpand(id: number) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  function getUnivForm(error: RawImport): UniversityForm {
    if (!univForms[error.id]) {
      const f = buildUniversityForm(error.payload);
      setUnivForms((prev) => ({ ...prev, [error.id]: f }));
      return f;
    }
    return univForms[error.id];
  }

  function getDeptForm(error: RawImport): DeptLevelForm {
    if (!deptForms[error.id]) {
      const f = buildDeptLevelForm(error.payload);
      setDeptForms((prev) => ({ ...prev, [error.id]: f }));
      return f;
    }
    return deptForms[error.id];
  }

  function updateUnivForm(id: number, patch: Partial<UniversityForm>) {
    setUnivForms((prev) => ({ ...prev, [id]: { ...(prev[id] ?? buildUniversityForm({})), ...patch } }));
  }

  function updateDeptForm(id: number, patch: Partial<DeptLevelForm>) {
    setDeptForms((prev) => ({ ...prev, [id]: { ...(prev[id] ?? buildDeptLevelForm({})), ...patch } }));
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          {title ?? "Erreurs d'import"} ({totalCount ?? errors.length})
        </h3>
      </div>

      {actionError && (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </div>
      )}

      <div className="mt-4 space-y-2">
        {errors.map((error) => {
          const isConflict = error.status === "conflict";
          const busy = isBusy || activeId === error.id;
          const isExpanded = expandedId === error.id;
          const entityName = String(error.payload?.name ?? error.external_id ?? "—");
          const isUniversity = error.entity === "partner_university";
          const isDeptOrLevel = error.entity === "department" || error.entity === "level";

          let univForm: UniversityForm | null = null;
          let deptForm: DeptLevelForm | null = null;
          if (isExpanded) {
            if (isUniversity) univForm = getUnivForm(error);
            else if (isDeptOrLevel) deptForm = getDeptForm(error);
          }

          return (
            <div
              key={error.id}
              className={`rounded-md overflow-hidden ${isConflict ? "border border-amber-300 bg-amber-50/30" : "border border-amber-200 bg-white"}`}
            >
              <button
                type="button"
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-amber-50 transition-colors"
                onClick={() => toggleExpand(error.id)}
              >
                <span className="shrink-0 text-amber-500">
                  {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </span>
                <span className="font-mono text-xs text-gray-600 shrink-0 w-28 truncate">
                  {error.external_id || "—"}
                </span>
                <span className="shrink-0 text-xs font-medium text-gray-700 w-40 truncate">
                  {entityName}
                </span>
                <span className="flex-1 text-xs text-red-700 truncate">
                  {error.error_message || "Erreur inconnue"}
                </span>
                <span className={`shrink-0 ml-2 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  isConflict ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-700"
                }`}>
                  {isConflict ? "conflit" : "corrigeable"}
                </span>
              </button>

              {isExpanded && (
                <div className="border-t border-amber-100 px-4 py-4 grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div>
                    <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Enregistrement complet
                    </h4>
                    <div className="rounded-md border border-gray-100 bg-gray-50 p-3">
                      <PayloadGrid entity={error.entity} payload={error.payload} />
                    </div>
                    <div className="mt-3 rounded-md border border-red-100 bg-red-50 px-3 py-2">
                      <p className="text-xs font-semibold text-red-700">Motif d&apos;échec</p>
                      <p className="mt-0.5 text-xs text-red-600">
                        {error.error_message || "Erreur inconnue"}
                      </p>
                    </div>
                  </div>

                  <div>
                    <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                      {isConflict ? "Action requise" : "Corriger et relancer"}
                    </h4>

                    {isConflict ? (
                      <p className="text-xs text-amber-700">
                        Cet enregistrement a été modifié localement depuis la dernière synchronisation.
                        Cliquez sur <strong>Forcer</strong> pour écraser avec les données source.
                      </p>
                    ) : isUniversity && univForm ? (
                      <div className="grid grid-cols-1 gap-2">
                        <TextField label="Nom" value={univForm.name} onChange={(v) => updateUnivForm(error.id, { name: v })} />
                        <TextField label="Nom court" value={univForm.short_name} onChange={(v) => updateUnivForm(error.id, { short_name: v })} />
                        <TextField label="Nom traduit" value={univForm.translated_name} onChange={(v) => updateUnivForm(error.id, { translated_name: v })} />
                        <TextField label="Code Erasmus" value={univForm.erasmus_code} onChange={(v) => updateUnivForm(error.id, { erasmus_code: v })} />
                        <TextField label="Ville" value={univForm.city} onChange={(v) => updateUnivForm(error.id, { city: v })} />
                        <TextField label="Site web" value={univForm.url} onChange={(v) => updateUnivForm(error.id, { url: v })} />
                        <TextField label="Email" value={univForm.email} onChange={(v) => updateUnivForm(error.id, { email: v })} />
                        <label className="block">
                          <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Pays</span>
                          <select
                            className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900"
                            value={univForm.country_id}
                            onChange={(e) => updateUnivForm(error.id, { country_id: e.target.value ? Number(e.target.value) : "" })}
                          >
                            <option value="">— Sélectionner un pays —</option>
                            {sortedCountries.map((c) => (
                              <option key={c.id} value={c.id}>{c.name_fr} ({c.iso2})</option>
                            ))}
                          </select>
                        </label>
                      </div>
                    ) : isDeptOrLevel && deptForm ? (
                      <div className="grid grid-cols-1 gap-2">
                        <TextField label="Code" value={deptForm.code} onChange={(v) => updateDeptForm(error.id, { code: v })} />
                        <TextField label="Nom" value={deptForm.name} onChange={(v) => updateDeptForm(error.id, { name: v })} />
                        <TextField label="ID Pégase" value={deptForm.pegase_id} onChange={(v) => updateDeptForm(error.id, { pegase_id: v })} />
                      </div>
                    ) : (
                      <p className="text-xs italic text-gray-400">
                        Ce type d&apos;erreur nécessite une correction manuelle dans la source de données.
                      </p>
                    )}

                    <div className="mt-4 flex gap-2">
                      {isConflict && onForce && (
                        <button
                          className="inline-flex h-8 items-center gap-1.5 rounded-md bg-amber-600 px-3 text-xs font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={busy}
                          onClick={() => runAction(() => onForce(error), error.id)}
                          type="button"
                        >
                          <RefreshCw className="h-3 w-3" />
                          Forcer la mise à jour
                        </button>
                      )}
                      {!isConflict && onRetry && (isUniversity || isDeptOrLevel) && (
                        <button
                          className="inline-flex h-8 items-center gap-1.5 rounded-md bg-[#1E3A8A] px-3 text-xs font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={busy}
                          onClick={() => {
                            const correction = isUniversity && univForm
                              ? buildUniversityCorrection(univForm)
                              : deptForm
                                ? buildDeptCorrection(deptForm)
                                : {};
                            return runAction(() => onRetry(error, correction), error.id);
                          }}
                          type="button"
                        >
                          <RotateCw className="h-3 w-3" />
                          Relancer
                        </button>
                      )}
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

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">{label}</span>
      <input
        className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1.5 text-xs text-gray-900 font-mono focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A]"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
