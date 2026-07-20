"use client";

import { AlertTriangle, Check, ChevronDown, ChevronRight, RefreshCw } from "lucide-react";
import { useState } from "react";

import { ExistingComparisonView } from "@/components/ui/existing-comparison";
import { Pagination } from "@/components/ui/pagination";
import type { Country, Department, IncomingImportError } from "@/lib/api/types";

const INCOMING_LABELS: Record<string, string> = {
  DEPARTEMENT: "Département",
  CIVILITE: "Civilité",
  NOM: "Nom",
  PRENOM: "Prénom",
  PAYS: "Pays",
  "UNIV ORIGINE": "Université d'origine",
  "DATE NAISSANCE": "Date naissance",
  CADRE: "Cadre",
  MAIL: "Email personnel",
  "MAIL ENSEEIHT": "Email ENSEEIHT",
  DUREE: "Durée",
  ANNEE: "Niveau / Année",
  PARCOURS: "Parcours",
  REMARQUES: "Remarques",
  STAGE: "Stage",
  DIPLOME: "Diplôme",
  "POURSUITE DOCTORAT": "Poursuite doctorat",
};

type CorrectionState = Record<string, string>;

const EDITABLE_FIELDS: Array<{ key: string; label: string; type?: string }> = [
  { key: "NOM", label: "Nom" },
  { key: "PRENOM", label: "Prénom" },
  { key: "CIVILITE", label: "Civilité" },
  { key: "DATE NAISSANCE", label: "Date naissance", type: "date" },
  { key: "PAYS", label: "Pays" },
  { key: "UNIV ORIGINE", label: "Université d'origine" },
  { key: "DEPARTEMENT", label: "Département" },
  { key: "CADRE", label: "Cadre" },
  { key: "ANNEE", label: "Niveau / Année" },
  { key: "PARCOURS", label: "Parcours" },
  { key: "MAIL", label: "Email personnel" },
  { key: "MAIL ENSEEIHT", label: "Email ENSEEIHT" },
  { key: "DUREE", label: "Durée" },
];

function PayloadGrid({ payload }: { payload: Record<string, unknown> }) {
  const entries = Object.entries(payload).filter(
    ([k, v]) => k !== "row_number" && v !== null && v !== undefined && v !== "",
  );
  if (entries.length === 0)
    return <p className="text-xs italic text-gray-400">Aucune donnée disponible</p>;
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">
            {INCOMING_LABELS[key] ?? key}
          </dt>
          <dd className="mt-0.5 font-mono text-xs text-gray-800 break-all">
            {String(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function IncomingImportErrorsPanel({
  errors,
  isBusy,
  canManage,
  onIgnore,
  onForce,
  countries,
  departments,
  totalCount,
  page = 1,
  pageSize = 25,
  onPageChange,
}: {
  errors: IncomingImportError[];
  isBusy: boolean;
  canManage: boolean;
  onIgnore: (error: IncomingImportError) => Promise<void>;
  onForce: (error: IncomingImportError, payload: Record<string, string>) => Promise<void>;
  countries: Country[];
  departments: Department[];
  totalCount?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
}) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [corrections, setCorrections] = useState<Record<number, CorrectionState>>({});

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

  function getCorrection(error: IncomingImportError): CorrectionState {
    if (!corrections[error.id]) {
      const p = error.payload as Record<string, string>;
      const init: CorrectionState = {};
      for (const { key } of EDITABLE_FIELDS) {
        init[key] = p[key] ?? "";
      }
      setCorrections((prev) => ({ ...prev, [error.id]: init }));
      return init;
    }
    return corrections[error.id];
  }

  function updateField(id: number, key: string, value: string) {
    setCorrections((prev) => ({
      ...prev,
      [id]: { ...(prev[id] ?? {}), [key]: value },
    }));
  }

  function handleForce(error: IncomingImportError) {
    const c = corrections[error.id];
    if (!c) return;
    const fullPayload = {
      ...(error.payload as Record<string, string>),
      ...c,
    };
    void runAction(() => onForce(error, fullPayload), error.id);
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
          const p = error.payload as Record<string, string>;
          const entityName =
            [p.NOM, p.PRENOM].filter(Boolean).join(" ") || error.external_id || "—";

          return (
            <div key={error.id} className="rounded-md overflow-hidden border border-amber-200 bg-white">
              {/* Summary row */}
              <button
                type="button"
                className="w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-amber-50"
                onClick={() => setExpandedId((prev) => (prev === error.id ? null : error.id))}
              >
                <span className="shrink-0 text-amber-500">
                  {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
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
                        labels={INCOMING_LABELS}
                      />
                      <div className="mt-3 rounded-md border border-red-100 bg-red-50 px-3 py-2">
                        <p className="text-xs font-semibold text-red-700">Motif d&apos;échec</p>
                        <p className="mt-0.5 text-xs text-red-600">
                          {error.error_message || "Erreur inconnue"}
                        </p>
                      </div>
                      <div className="mt-4 flex gap-2">
                        <button
                          className="inline-flex h-8 items-center gap-1.5 rounded-md bg-amber-600 px-3 text-xs font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={busy || !canManage}
                          onClick={() => void runAction(() => onForce(error, {}), error.id)}
                          type="button"
                        >
                          <RefreshCw className="h-3 w-3" />
                          Remplacer par les données sources
                        </button>
                        <button
                          className="inline-flex h-8 items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={busy || !canManage}
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

                        <div className="grid grid-cols-1 gap-2 max-h-72 overflow-y-auto pr-1">
                          {EDITABLE_FIELDS.map(({ key, label, type }) => {
                            if (key === "PAYS") {
                              return (
                                <label key={key} className="block">
                                  <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                                    {label}
                                  </span>
                                  <select
                                    className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900 focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A] disabled:bg-gray-50 disabled:text-gray-400"
                                    value={correction[key] ?? ""}
                                    disabled={!canManage}
                                    onChange={(e) => updateField(error.id, key, e.target.value)}
                                  >
                                    <option value="">— Sélectionner un pays —</option>
                                    {sortedCountries.map((c) => (
                                      <option key={c.id} value={c.name_fr}>{c.name_fr}</option>
                                    ))}
                                  </select>
                                </label>
                              );
                            }
                            if (key === "DEPARTEMENT") {
                              return (
                                <label key={key} className="block">
                                  <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                                    {label}
                                  </span>
                                  <select
                                    className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900 focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A] disabled:bg-gray-50 disabled:text-gray-400"
                                    value={correction[key] ?? ""}
                                    disabled={!canManage}
                                    onChange={(e) => updateField(error.id, key, e.target.value)}
                                  >
                                    <option value="">— Sélectionner un département —</option>
                                    {departments.map((d) => (
                                      <option key={d.id} value={d.code}>{d.code} — {d.name}</option>
                                    ))}
                                  </select>
                                </label>
                              );
                            }
                            return (
                              <label key={key} className="block">
                                <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                                  {label}
                                </span>
                                <input
                                  className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1.5 text-xs text-gray-900 focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A] disabled:bg-gray-50 disabled:text-gray-400"
                                  type={type ?? "text"}
                                  value={correction[key] ?? ""}
                                  disabled={!canManage}
                                  onChange={(e) => updateField(error.id, key, e.target.value)}
                                />
                              </label>
                            );
                          })}
                        </div>

                        <div className="flex flex-wrap gap-2 mt-4">
                          <button
                            className="inline-flex h-8 items-center gap-1.5 rounded-md bg-amber-600 px-3 text-xs font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={busy || !canManage}
                            onClick={() => handleForce(error)}
                            type="button"
                          >
                            <RefreshCw className="h-3 w-3" />
                            Relancer
                          </button>
                          <button
                            className="inline-flex h-8 items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={busy || !canManage}
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
