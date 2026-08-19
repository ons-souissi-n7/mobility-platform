"use client";

import { AlertTriangle, Check, ChevronDown, ChevronRight, RefreshCw, RotateCw } from "lucide-react";
import { useState } from "react";

import { ExistingComparisonView } from "@/components/ui/existing-comparison";
import { Pagination } from "@/components/ui/pagination";
import type { PartnerUniversity, RawImport } from "@/lib/api/types";
import type { MobilityImportRetryPayload } from "@/lib/api/mobility-mutations";

type ErrorKind = "conflict" | "missing_university" | "category_error" | "no_correction";

const AGREEMENT_LABELS: Record<string, string> = {
  moveon_id: "ID MoveON",
  reference: "Référence",
  name: "Nom de l'accord",
  partner_university_moveon_id: "ID université MoveON",
  partner_university_erasmus_code: "Code Erasmus",
  partner_university_name: "Université partenaire",
  relation_type: "Type de relation",
  category_name: "Cadre d'accord",
  direction: "Direction",
  level: "Niveau",
  discipline: "Discipline",
  status: "Statut",
  start_date: "Début",
  end_date: "Fin",
  start_academic_year: "Année début",
  end_academic_year: "Année fin",
  remarks: "Remarques",
};

const CATEGORY_LABELS: Record<string, string> = {
  moveon_id: "ID MoveON",
  moveon_framework_id: "ID cadre MoveON",
  name: "Nom",
};

function getLabels(entity: string | undefined): Record<string, string> {
  if (entity === "agreement") return AGREEMENT_LABELS;
  if (entity === "agreement_category") return CATEGORY_LABELS;
  return {};
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    return obj.name ? String(obj.name) : JSON.stringify(value);
  }
  return String(value);
}

function PayloadGrid({ entity, payload }: { entity: string | undefined; payload: Record<string, unknown> }) {
  const labels = getLabels(entity);
  const entries = Object.entries(payload).filter(([key, v]) => {
    if (v === null || v === undefined || v === "") return false;
    if (Array.isArray(v) && v.length === 0) return false;
    if (typeof v === "object" && !Array.isArray(v)) {
      return key === "country" || key === "partner_university";
    }
    return true;
  });
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

function classifyError(error: RawImport): ErrorKind {
  if (error.status === "conflict") return "conflict";
  const msg = (error.error_message ?? "").toLowerCase();
  if (msg.includes("moveon_id is required") || msg.includes("null value in column")) return "no_correction";
  if (msg.includes("missing partner university") || msg.includes("partner_university") || msg.includes("university reference")) return "missing_university";
  if (error.entity === "agreement_category") return "category_error";
  if (error.entity === "agreement") return "missing_university";
  return "no_correction";
}

type CorrectionForm = {
  name: string;
  reference: string;
  partner_university_id: number | "";
};

function buildInitialForm(payload: Record<string, unknown>): CorrectionForm {
  return {
    name: String(payload.name ?? ""),
    reference: String(payload.reference ?? ""),
    partner_university_id: "",
  };
}

export function MobilityImportErrorsPanel({
  errors,
  isBusy,
  onIgnore,
  onRetry,
  onForce,
  universities,
  totalCount,
  page = 1,
  pageSize = 25,
  onPageChange,
}: Readonly<{
  errors: RawImport[];
  isBusy: boolean;
  onIgnore: (error: RawImport) => Promise<void>;
  onRetry: (error: RawImport, payload: MobilityImportRetryPayload) => Promise<void>;
  onForce?: (error: RawImport) => Promise<void>;
  universities: PartnerUniversity[];
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
      setActionError(err instanceof Error ? err.message : "Impossible de traiter l'erreur.");
    } finally {
      setActiveId(null);
    }
  }

  function getForm(error: RawImport): CorrectionForm {
    if (!forms[error.id]) {
      const initial = buildInitialForm(error.payload);
      setForms((prev) => ({ ...prev, [error.id]: initial }));
      return initial;
    }
    return forms[error.id];
  }

  function updateForm(id: number, patch: Partial<CorrectionForm>) {
    setForms((prev) => ({
      ...prev,
      [id]: { ...(prev[id] ?? buildInitialForm({})), ...patch },
    }));
  }

  function toggleExpand(id: number) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  const sortedUniversities = [...universities].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          Erreurs d&apos;import / sync ({totalCount ?? errors.length})
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
          const kind = classifyError(error);
          const isConflict = kind === "conflict";
          const isExpanded = expandedId === error.id;
          const existing = isExpanded
            ? (error.payload?._existing as Record<string, unknown> | undefined)
            : undefined;
          const sourceData = existing
            ? (Object.fromEntries(Object.entries(error.payload).filter(([k]) => k !== "_existing")) as Record<string, unknown>)
            : null;
          const form = isExpanded && !existing ? getForm(error) : null;
          const entityName = String(error.payload?.name ?? error.payload?.reference ?? error.external_id ?? "—");
          const partnerUniversityName =
            typeof error.payload?.partner_university_name === "string"
              ? error.payload.partner_university_name
              : undefined;

          return (
            <div
              key={error.id}
              className={`rounded-md overflow-hidden border ${isConflict ? "border-amber-400 bg-amber-50/60" : "border-amber-200 bg-white"}`}
            >
              <button
                type="button"
                className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${isConflict ? "hover:bg-amber-100/60" : "hover:bg-amber-50"}`}
                onClick={() => toggleExpand(error.id)}
              >
                <span className="shrink-0 text-amber-500">
                  {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </span>
                <span className="font-mono text-xs text-gray-500 shrink-0 w-24 truncate">
                  {error.external_id || "—"}
                </span>
                <span className="shrink-0 text-xs font-medium text-gray-700 w-48 truncate">
                  {entityName}
                </span>
                <span className={`flex-1 text-xs truncate ${isConflict ? "text-amber-800" : "text-red-700"}`}>
                  {error.error_message || "Erreur inconnue"}
                </span>
                <span className={`shrink-0 ml-2 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  isConflict
                    ? "bg-amber-100 text-amber-800"
                    : kind === "missing_university"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-red-100 text-red-700"
                }`}>
                  {isConflict ? "conflit" : kind === "missing_university" ? "corrigeable" : "manuel"}
                </span>
              </button>

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
                        labels={getLabels(error.entity)}
                      />
                      <div className={`mt-3 rounded-md border px-3 py-2 ${isConflict ? "border-amber-200 bg-amber-50" : "border-red-100 bg-red-50"}`}>
                        <p className={`text-xs font-semibold ${isConflict ? "text-amber-800" : "text-red-700"}`}>
                          {isConflict ? "Motif du conflit" : "Motif d'échec"}
                        </p>
                        <p className={`mt-0.5 text-xs ${isConflict ? "text-amber-700" : "text-red-600"}`}>
                          {error.error_message || "Erreur inconnue"}
                        </p>
                      </div>
                      <div className="mt-4 flex gap-2">
                        {isConflict && onForce && (
                          <button
                            className="inline-flex h-8 items-center gap-1.5 rounded-md bg-amber-600 px-3 text-xs font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={busy}
                            onClick={() => runAction(() => onForce(error), error.id)}
                            type="button"
                          >
                            <RefreshCw className="h-3 w-3" />
                            Remplacer par les données sources
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
                  ) : form ? (
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                      <div>
                        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                          Enregistrement complet
                        </h4>
                        <div className="rounded-md border border-gray-100 bg-gray-50 p-3">
                          <PayloadGrid entity={error.entity} payload={error.payload} />
                        </div>
                        <div className={`mt-3 rounded-md border px-3 py-2 ${isConflict ? "border-amber-200 bg-amber-50" : "border-red-100 bg-red-50"}`}>
                          <p className={`text-xs font-semibold ${isConflict ? "text-amber-800" : "text-red-700"}`}>
                            {isConflict ? "Détail du conflit" : "Motif d'échec"}
                          </p>
                          <p className={`mt-0.5 text-xs ${isConflict ? "text-amber-700" : "text-red-600"}`}>
                            {error.error_message || "Erreur inconnue"}
                          </p>
                        </div>
                      </div>

                      <div>
                        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                          {isConflict ? "Action requise" : "Corriger et relancer"}
                        </h4>

                        {isConflict ? (
                          <p className="text-xs text-amber-800">
                            Cet enregistrement a été modifié localement. Cliquez sur{" "}
                            <strong>Forcer</strong> pour écraser la version locale avec les données source.
                          </p>
                        ) : kind === "no_correction" ? (
                          <p className="text-xs italic text-gray-400">
                            Ce type d&apos;erreur nécessite une correction manuelle dans MoveON avant de relancer.
                          </p>
                        ) : (
                          <div className="grid grid-cols-1 gap-2">
                            <label className="block">
                              <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Nom de l&apos;accord</span>
                              <input
                                className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1.5 text-xs text-gray-900 font-mono focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A]"
                                type="text"
                                value={form.name}
                                onChange={(e) => updateForm(error.id, { name: e.target.value })}
                              />
                            </label>

                            <label className="block">
                              <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Référence</span>
                              <input
                                className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1.5 text-xs text-gray-900 font-mono focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A]"
                                type="text"
                                value={form.reference}
                                onChange={(e) => updateForm(error.id, { reference: e.target.value })}
                              />
                            </label>

                            {(kind === "missing_university" || kind === "category_error") && (
                              <label className="block">
                                <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Université partenaire</span>
                                {partnerUniversityName && (
                                  <p className="mt-0.5 text-xs text-gray-400">
                                    Source : <span className="font-mono">{partnerUniversityName}</span>
                                  </p>
                                )}
                                <select
                                  className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900"
                                  value={form.partner_university_id}
                                  onChange={(e) => updateForm(error.id, { partner_university_id: e.target.value ? Number(e.target.value) : "" })}
                                >
                                  <option value="">— Sélectionner —</option>
                                  {sortedUniversities.map((u) => (
                                    <option key={u.id} value={u.id}>{u.name}</option>
                                  ))}
                                </select>
                              </label>
                            )}
                          </div>
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
                              Forcer
                            </button>
                          )}
                          {!isConflict && kind !== "no_correction" && (
                            <button
                              className="inline-flex h-8 items-center gap-1.5 rounded-md bg-[#1E3A8A] px-3 text-xs font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
                              disabled={busy}
                              onClick={() =>
                                runAction(
                                  () =>
                                    onRetry(error, {
                                      ...(form.partner_university_id !== "" ? { partner_university_id: form.partner_university_id } : {}),
                                      ...(form.name ? { name: form.name } : {}),
                                      ...(form.reference ? { reference: form.reference } : {}),
                                    }),
                                  error.id,
                                )
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
