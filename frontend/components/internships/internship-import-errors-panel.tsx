"use client";

import { AlertTriangle, Check, ChevronDown, ChevronRight, FilePlus, RefreshCw, Search } from "lucide-react";
import { useState } from "react";

import { ExistingComparisonView } from "@/components/ui/existing-comparison";
import { Pagination } from "@/components/ui/pagination";
import type { InternshipForcePayload, ReconciliationCandidate } from "@/lib/api/internship-mutations";
import { getInternshipReconciliationCandidates } from "@/lib/api/internship-mutations";
import { getStudentSelectOptions } from "@/lib/api/student-mutations";
import type { Country, InternshipImportError } from "@/lib/api/types";
import { splitTrailingParenthetical } from "@/lib/utils";

const INTERNSHIP_LABELS: Record<string, string> = {
  ine: "N°INE",
  company_name: "Raison sociale",
  country_name: "Pays",
  city: "Ville",
  start_date: "Date de début",
  end_date: "Date de fin",
  internship_type: "Type",
  title: "Titre",
  status: "Statut",
  status_code: "Code statut",
  weeks: "Nb semaines",
  libelle: "Libellé Eudonet",
  school_tutor: "Tuteur pédagogique",
  company_tutor: "Tuteur entreprise",
};

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    return obj.name ? String(obj.name) : JSON.stringify(value);
  }
  return String(value);
}

function PayloadGrid({ payload }: { payload: Record<string, unknown> }) {
  const entries = Object.entries(payload).filter(([, v]) => {
    if (v === null || v === undefined || v === "") return false;
    if (Array.isArray(v) && v.length === 0) return false;
    return true;
  });

  if (entries.length === 0)
    return <p className="text-xs italic text-gray-400">Aucune donnée disponible</p>;

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">
            {INTERNSHIP_LABELS[key] ?? key}
          </dt>
          <dd className="mt-0.5 font-mono text-xs text-gray-800 break-all">
            {renderValue(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function ConfidenceBadge({ confidence, score }: { confidence: string; score: number }) {
  const styles: Record<string, string> = {
    high: "bg-green-100 text-green-800",
    medium: "bg-amber-100 text-amber-800",
    low: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${styles[confidence] ?? styles.low}`}>
      {Math.round(score * 100)}%
    </span>
  );
}

function InternshipCandidatesPanel({
  candidates,
  loading,
  onSearch,
  onSelect,
}: Readonly<{
  candidates: ReconciliationCandidate[] | undefined;
  loading: boolean;
  onSearch: () => void;
  onSelect: (ine: string) => void;
}>) {
  return (
    <div className="rounded-md border border-blue-200 bg-blue-50 p-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-blue-800">Réconciliation — étudiant similaire</p>
        <button
          type="button"
          className="inline-flex h-7 items-center gap-1 rounded-md border border-blue-300 bg-white px-2 text-xs font-medium text-blue-700 hover:bg-blue-50 disabled:opacity-60"
          disabled={loading}
          onClick={onSearch}
        >
          <Search className="h-3 w-3" />
          {candidates !== undefined ? "Actualiser" : "Chercher"}
        </button>
      </div>

      {loading && <p className="mt-2 text-xs text-blue-500">Recherche en cours…</p>}

      {!loading && candidates !== undefined && (
        candidates.length === 0 ? (
          <p className="mt-2 text-xs italic text-blue-500">Aucun étudiant similaire trouvé.</p>
        ) : (
          <ul className="mt-2 space-y-1.5">
            {candidates.map((c) => (
              <li key={c.ine} className="flex items-center gap-2">
                <div className="min-w-0 flex-1">
                  <span className="font-mono text-xs font-medium text-gray-800">
                    {c.last_name} {c.first_name}
                  </span>
                  <span className="ml-1.5 text-[10px] text-gray-500">
                    ({c.ine}){c.department_code ? ` · ${c.department_code}` : ""}
                  </span>
                </div>
                <div className="flex shrink-0 items-center gap-1.5">
                  <ConfidenceBadge confidence={c.confidence} score={c.score} />
                  <button
                    type="button"
                    className="h-6 rounded px-2 text-[10px] font-medium bg-blue-600 text-white hover:bg-blue-700"
                    onClick={() => onSelect(c.ine)}
                  >
                    Utiliser
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )
      )}
    </div>
  );
}

type StudentOption = { ine: string; label: string };

type CorrectionState = {
  ine: string;
  company_name: string;
  country_name: string;
  start_date: string;
  end_date: string;
};

function buildInitialCorrection(error: InternshipImportError): CorrectionState {
  const p = error.payload;
  const msg = error.error_message ?? "";
  const isCountryError = /[Pp]ays\s+introuvable/i.test(msg);

  // Excel format: "Étudiant (INE – Nom Prénom)" = "INE – NOM Prénom"
  const studentField = String(p["Étudiant (INE – Nom Prénom)"] ?? "").trim();
  let defaultIne = "";
  for (const sep of [" – ", " - "]) {
    if (studentField.includes(sep)) {
      defaultIne = studentField.split(sep, 1)[0].trim();
      break;
    }
  }
  // Eudonet sync stores INE as "ine" key (snake_case)
  if (!defaultIne) defaultIne = String(p["ine"] ?? "");

  return {
    ine: defaultIne,
    company_name: String(p.company_name ?? ""),
    country_name: isCountryError ? "" : String(p.country_name ?? ""),
    start_date: String(p.start_date ?? ""),
    end_date: String(p.end_date ?? ""),
  };
}

export function InternshipImportErrorsPanel({
  errors,
  isBusy,
  onIgnore,
  onForce,
  onAdd,
  countries,
  selectedYearId,
  totalCount,
  page = 1,
  pageSize = 25,
  onPageChange,
}: Readonly<{
  errors: InternshipImportError[];
  isBusy: boolean;
  onIgnore: (error: InternshipImportError) => Promise<void>;
  onForce: (error: InternshipImportError, payload: InternshipForcePayload) => Promise<void>;
  onAdd: (error: InternshipImportError) => Promise<void>;
  countries: Country[];
  selectedYearId?: number;
  totalCount?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
}>) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [corrections, setCorrections] = useState<Record<number, CorrectionState>>({});
  const [studentOptions, setStudentOptions] = useState<StudentOption[]>([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [candidatesByError, setCandidatesByError] = useState<Record<number, ReconciliationCandidate[]>>({});
  const [loadingCandidates, setLoadingCandidates] = useState<number | null>(null);


  if (errors.length === 0) return null;

  async function runAction(fn: () => Promise<void>, id: number) {
    setActiveId(id);
    setActionError(null);
    try {
      await fn();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Impossible de traiter l'erreur.");
    } finally {
      setActiveId(null);
    }
  }

  function getCorrection(error: InternshipImportError): CorrectionState {
    if (!corrections[error.id]) {
      const initial = buildInitialCorrection(error);
      setCorrections((prev) => ({ ...prev, [error.id]: initial }));
      return initial;
    }
    return corrections[error.id];
  }

  function updateCorrection(id: number, field: keyof CorrectionState, value: string) {
    setCorrections((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] ?? { ine: "", company_name: "", country_name: "", start_date: "", end_date: "" }),
        [field]: value,
      },
    }));
  }

  async function loadCandidates(id: number) {
    setLoadingCandidates(id);
    try {
      const result = await getInternshipReconciliationCandidates(id);
      setCandidatesByError((prev) => ({ ...prev, [id]: result }));
    } catch {
      setCandidatesByError((prev) => ({ ...prev, [id]: [] }));
    } finally {
      setLoadingCandidates(null);
    }
  }

  async function ensureStudents() {
    if (studentOptions.length === 0 && !loadingStudents) {
      setLoadingStudents(true);
      try {
        const opts = await getStudentSelectOptions(selectedYearId);
        setStudentOptions(
          opts.map((o) => {
            // Format attendu : "NOM Prénom (INE)"
            const { base: name, inner: ine } = splitTrailingParenthetical(o.label);
            return { ine, label: `${ine} – ${name}` };
          }),
        );
      } catch {
        // silently ignore — user can still type manually
      } finally {
        setLoadingStudents(false);
      }
    }
  }

  function handleForce(error: InternshipImportError) {
    const c = corrections[error.id];
    if (!c) return;
    const payload: InternshipForcePayload = {
      payload: {
        ine: c.ine,
        company_name: c.company_name,
        country_name: c.country_name,
        start_date: c.start_date,
        end_date: c.end_date,
      },
    };
    void runAction(() => onForce(error, payload), error.id);
  }

  const sortedCountries = [...countries].sort((a, b) => a.name_fr.localeCompare(b.name_fr));

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          Erreurs d&apos;import ({totalCount ?? errors.length})
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
          const existing = isExpanded
            ? (error.payload?._existing as Record<string, unknown> | undefined)
            : undefined;
          const sourceData = existing
            ? (Object.fromEntries(Object.entries(error.payload).filter(([k]) => k !== "_existing")) as Record<string, unknown>)
            : null;
          const correction = isExpanded && !existing ? getCorrection(error) : null;
          // Excel: "Étudiant (INE – Nom Prénom)" field; Eudonet: "libelle" field (unique to Eudonet format)
          const hasStudentField =
            !!String(error.payload?.["Étudiant (INE – Nom Prénom)"] ?? "").trim() ||
            !!String(error.payload?.["libelle"] ?? "").trim();

          const entityName = String(
            error.payload?.ine ?? error.payload?.company_name ?? error.external_id ?? "—",
          );

          return (
            <div
              key={error.id}
              className="rounded-md overflow-hidden border border-amber-200 bg-white"
            >
              {/* Summary row */}
              <button
                type="button"
                className="w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-amber-50"
                onClick={() => {
                  setExpandedId((prev) => (prev === error.id ? null : error.id));
                  if (expandedId !== error.id) void ensureStudents();
                }}
              >
                <span className="shrink-0 text-amber-500">
                  {isExpanded
                    ? <ChevronDown className="h-4 w-4" />
                    : <ChevronRight className="h-4 w-4" />}
                </span>
                <span className="font-mono text-xs text-gray-500 shrink-0 w-24 truncate">
                  {error.external_id || "—"}
                </span>
                <span className="shrink-0 text-xs font-medium text-gray-700 w-48 truncate">
                  {entityName}
                </span>
                <span className="flex-1 text-xs truncate text-red-700">
                  {error.error_message || "Erreur inconnue"}
                </span>
                <span className="shrink-0 ml-2 rounded-full px-2 py-0.5 text-[10px] font-medium bg-red-100 text-red-700">
                  {error.status}
                </span>
              </button>

              {/* Expanded panel */}
              {isExpanded && (
                <div className="border-t border-amber-100 px-4 py-4">
                  {existing && sourceData ? (
                    <div>
                      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                        Comparaison — données source vs. base actuelle
                      </h4>
                      <ExistingComparisonView
                        newData={sourceData}
                        existingData={existing}
                        labels={INTERNSHIP_LABELS}
                      />
                      <div className="mt-3 rounded-md border border-red-100 bg-red-50 px-3 py-2">
                        <p className="text-xs font-semibold text-red-700">Motif d&apos;échec</p>
                        <p className="mt-0.5 text-xs text-red-600">
                          {error.error_message || "Erreur inconnue"}
                        </p>
                      </div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        <button
                          className="inline-flex h-8 items-center gap-1.5 rounded-md bg-amber-600 px-3 text-xs font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={busy}
                          onClick={() => void runAction(() => onForce(error, { payload: {} }), error.id)}
                          type="button"
                        >
                          <RefreshCw className="h-3 w-3" />
                          Remplacer l&apos;existant
                        </button>
                        <button
                          className="inline-flex h-8 items-center gap-1.5 rounded-md bg-blue-700 px-3 text-xs font-medium text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={busy}
                          onClick={() => void runAction(() => onAdd(error), error.id)}
                          type="button"
                        >
                          <FilePlus className="h-3 w-3" />
                          Ajouter comme nouvel enregistrement
                        </button>
                        <button
                          className="inline-flex h-8 items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={busy}
                          onClick={() => void runAction(() => onIgnore(error), error.id)}
                          type="button"
                        >
                          <Check className="h-3 w-3" />
                          Ignorer
                        </button>
                      </div>
                    </div>
                  ) : correction ? (
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                      {/* Left: full record */}
                      <div>
                        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                          Enregistrement complet
                        </h4>
                        <div className="rounded-md border border-gray-100 bg-gray-50 p-3">
                          <PayloadGrid payload={error.payload} />
                        </div>
                        <div className="mt-3 rounded-md border border-red-100 bg-red-50 px-3 py-2">
                          <p className="text-xs font-semibold text-red-700">Motif d&apos;échec</p>
                          <p className="mt-0.5 text-xs text-red-600">
                            {error.error_message || "Erreur inconnue"}
                          </p>
                        </div>
                      </div>

                      {/* Right: correction form */}
                      <div>
                        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                          Corriger et relancer
                        </h4>

                        <div className="grid grid-cols-1 gap-2">
                          {hasStudentField && (
                            <InternshipCandidatesPanel
                              candidates={candidatesByError[error.id]}
                              loading={loadingCandidates === error.id}
                              onSearch={() => void loadCandidates(error.id)}
                              onSelect={(ine) => updateCorrection(error.id, "ine", ine)}
                            />
                          )}

                          {/* Student select */}
                          <label className="block">
                            <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                              Étudiant (INE – Nom Prénom)
                            </span>
                            <select
                              className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900 focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A] disabled:bg-gray-50 disabled:text-gray-400"
                              value={correction.ine}
                              disabled={loadingStudents}
                              onChange={(e) => updateCorrection(error.id, "ine", e.target.value)}
                            >
                              <option value="">
                                {loadingStudents ? "Chargement…" : "— Sélectionner un étudiant —"}
                              </option>
                              {studentOptions.map((s) => (
                                <option key={s.ine} value={s.ine}>
                                  {s.label}
                                </option>
                              ))}
                            </select>
                          </label>

                          <CorrectionField
                            label="Raison sociale"
                            value={correction.company_name}
                            onChange={(v) => updateCorrection(error.id, "company_name", v)}
                          />

                          {/* Country select */}
                          <label className="block">
                            <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                              Pays
                            </span>
                            <select
                              className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900 focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A]"
                              value={correction.country_name}
                              onChange={(e) => updateCorrection(error.id, "country_name", e.target.value)}
                            >
                              <option value="">— Sélectionner un pays —</option>
                              {sortedCountries.map((c) => (
                                <option key={c.id} value={c.name_fr}>
                                  {c.name_fr}
                                </option>
                              ))}
                            </select>
                          </label>

                          <CorrectionField
                            label="Date de début"
                            value={correction.start_date}
                            type="date"
                            onChange={(v) => updateCorrection(error.id, "start_date", v)}
                          />
                          <CorrectionField
                            label="Date de fin"
                            value={correction.end_date}
                            type="date"
                            onChange={(v) => updateCorrection(error.id, "end_date", v)}
                          />
                        </div>

                        <div className="flex flex-wrap gap-2 mt-4">
                          <button
                            className="inline-flex h-8 items-center gap-1.5 rounded-md bg-[#1E3A8A] px-3 text-xs font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={busy}
                            onClick={() => handleForce(error)}
                            type="button"
                          >
                            <RefreshCw className="h-3 w-3" />
                            Relancer
                          </button>
                          <button
                            className="inline-flex h-8 items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={busy}
                            onClick={() => void runAction(() => onIgnore(error), error.id)}
                            type="button"
                          >
                            <Check className="h-3 w-3" />
                            Ignorer
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : null}
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

function CorrectionField({
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
        className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1.5 text-xs text-gray-900 focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A]"
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
