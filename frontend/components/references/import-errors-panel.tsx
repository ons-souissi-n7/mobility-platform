"use client";

import { AlertTriangle, Check, ChevronDown, ChevronRight, RotateCw } from "lucide-react";
import { useMemo, useState } from "react";

import type { Country, RawImport } from "@/lib/api/types";

// Field labels by entity type
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

const LEVEL_LABELS: Record<string, string> = {
  pegase_id: "ID Pégase",
  code: "Code",
  name: "Nom",
};

function getLabels(entity: string | undefined): Record<string, string> {
  if (entity === "partner_university") return UNIVERSITY_LABELS;
  if (entity === "department") return DEPARTMENT_LABELS;
  if (entity === "level") return LEVEL_LABELS;
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

function PayloadGrid({
  entity,
  payload,
}: {
  entity: string | undefined;
  payload: Record<string, unknown>;
}) {
  const labels = getLabels(entity);
  const entries = Object.entries(payload).filter(([, v]) => v !== null && v !== undefined && v !== "");

  if (entries.length === 0)
    return <p className="text-xs italic text-gray-400">Aucune donnée disponible</p>;

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

type ImportErrorsPanelProps = {
  countries: Country[];
  errors: RawImport[];
  isBusy: boolean;
  onIgnore: (error: RawImport) => Promise<void>;
  onRetry: (error: RawImport, correction?: number | string) => Promise<void>;
  onForce?: (error: RawImport) => Promise<void>;
  title?: string;
  retryField?: "country" | "code";
};

export function ImportErrorsPanel({
  countries,
  errors,
  isBusy,
  onIgnore,
  onRetry,
  onForce,
  title,
  retryField,
}: ImportErrorsPanelProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [selectedCountries, setSelectedCountries] = useState<Record<number, string>>({});
  const [selectedCodes, setSelectedCodes] = useState<Record<number, string>>({});
  const [activeId, setActiveId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const sortedCountries = useMemo(
    () => [...countries].sort((a, b) => a.name_fr.localeCompare(b.name_fr)),
    [countries],
  );

  if (errors.length === 0) return null;

  async function runAction(action: () => Promise<void>, id: number) {
    setActiveId(id);
    setActionError(null);
    try {
      await action();
    } catch (error) {
      setActionError(
        error instanceof Error ? error.message : "Erreur inconnue lors de l'opération.",
      );
    } finally {
      setActiveId(null);
    }
  }

  function toggleExpand(id: number) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          {title ?? "Erreurs d'import"} ({errors.length})
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
          const countryId = Number(selectedCountries[error.id] || 0);
          const code = selectedCodes[error.id] ?? "";

          const canRetry =
            !isConflict &&
            ((retryField === "country" && !!countryId) ||
              (retryField === "code" && !!code.trim()));

          const correction =
            retryField === "country" ? countryId : retryField === "code" ? code : undefined;

          const entityName = String(error.payload?.name ?? error.external_id ?? "—");

          return (
            <div
              key={error.id}
              className={`rounded-md overflow-hidden ${isConflict ? "border border-amber-300 bg-amber-50/30" : "border border-amber-200 bg-white"}`}
            >
              {/* Summary row */}
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
                  isConflict
                    ? "bg-amber-100 text-amber-800"
                    : "bg-red-100 text-red-700"
                }`}>
                  {isConflict ? "conflit" : retryField ? "corrigeable" : "manuel"}
                </span>
              </button>

              {/* Expanded panel */}
              {isExpanded && (
                <div className="border-t border-amber-100 px-4 py-4 grid grid-cols-1 gap-6 sm:grid-cols-2">
                  {/* Left: full record */}
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

                  {/* Right: correction */}
                  <div>
                    <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Correction proposée
                    </h4>

                    {retryField === "country" && (
                      <div className="space-y-2">
                        <p className="text-xs text-gray-500">
                          Le pays n&apos;a pas pu être résolu automatiquement. Sélectionnez le pays correct.
                        </p>
                        <select
                          className="w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900"
                          disabled={busy}
                          value={selectedCountries[error.id] ?? ""}
                          onChange={(e) =>
                            setSelectedCountries((v) => ({ ...v, [error.id]: e.target.value }))
                          }
                        >
                          <option value="">Choisir un pays…</option>
                          {sortedCountries.map((country) => (
                            <option key={country.id} value={country.id}>
                              {country.name_fr} ({country.iso2})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    {retryField === "code" && (
                      <div className="space-y-2">
                        <p className="text-xs text-gray-500">
                          Le code source ne correspond à aucune entrée connue. Saisissez le code correct.
                        </p>
                        <input
                          className="w-40 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900 placeholder-gray-400 font-mono"
                          disabled={busy}
                          placeholder="Ex: SN"
                          type="text"
                          value={code}
                          onChange={(e) =>
                            setSelectedCodes((v) => ({
                              ...v,
                              [error.id]: e.target.value.toUpperCase(),
                            }))
                          }
                        />
                      </div>
                    )}

                    {isConflict && (
                      <p className="text-xs text-amber-700">
                        Cet enregistrement a été modifié localement depuis la dernière synchronisation.
                        Cliquez sur <strong>Forcer</strong> pour écraser la version locale avec les données de la source externe.
                      </p>
                    )}

                    {!isConflict && !retryField && (
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
                          <RotateCw className="h-3 w-3" />
                          Forcer la mise à jour
                        </button>
                      )}
                      {!isConflict && retryField && (
                        <button
                          className="inline-flex h-8 items-center gap-1.5 rounded-md bg-[#1E3A8A] px-3 text-xs font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={!canRetry || busy}
                          onClick={() =>
                            runAction(() => onRetry(error, correction), error.id)
                          }
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
    </div>
  );
}
