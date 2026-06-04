"use client";

import { AlertTriangle, Check, RotateCw } from "lucide-react";
import { useState } from "react";

import type { PartnerUniversity, RawImport } from "@/lib/api/types";
import type { MobilityImportRetryPayload } from "@/lib/api/mobility-mutations";

type ErrorKind =
  | "missing_university"  // can retry with partner_university_id
  | "no_correction"       // error can't be corrected via UI, ignore only
  | "category_error";     // category-related error, ignore only

function classifyError(error: RawImport): ErrorKind {
  const msg = (error.error_message ?? "").toLowerCase();

  // moveon_id missing → can't fix via UI
  if (msg.includes("moveon_id is required") || msg.includes("moveon_id")) {
    return "no_correction";
  }
  // DB constraint violation (country_id, not-null, etc.) → can't fix via UI
  if (msg.includes("violates not-null constraint") || msg.includes("country_id") || msg.includes("null value in column")) {
    return "no_correction";
  }
  // University not found → can correct by selecting an existing university
  if (
    msg.includes("missing partner university") ||
    msg.includes("partner_university") ||
    msg.includes("university reference")
  ) {
    return "missing_university";
  }
  // Category errors
  if (error.entity === "agreement_category") {
    return "category_error";
  }
  // Default: if it's an agreement error and payload has a university ref field → offer correction
  if (error.entity === "agreement") {
    return "missing_university";
  }
  return "no_correction";
}

function getCorrectionLabel(kind: ErrorKind): string {
  switch (kind) {
    case "missing_university": return "Associer à une université existante";
    case "no_correction": return "Aucune correction disponible via l'interface";
    case "category_error": return "—";
  }
}

export function MobilityImportErrorsPanel({
  errors,
  isBusy,
  onIgnore,
  onRetry,
  universities,
}: {
  errors: RawImport[];
  isBusy: boolean;
  onIgnore: (error: RawImport) => Promise<void>;
  onRetry: (error: RawImport, payload: MobilityImportRetryPayload) => Promise<void>;
  universities: PartnerUniversity[];
}) {
  const [activeId, setActiveId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [corrections, setCorrections] = useState<Record<number, MobilityImportRetryPayload>>({});

  if (errors.length === 0) return null;

  async function handleIgnore(error: RawImport) {
    setActiveId(error.id);
    setActionError(null);
    try {
      await onIgnore(error);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Impossible de traiter l'erreur.");
    } finally {
      setActiveId(null);
    }
  }

  async function handleRetry(error: RawImport) {
    setActiveId(error.id);
    setActionError(null);
    try {
      await onRetry(error, corrections[error.id] ?? {});
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Impossible de relancer l'import.");
    } finally {
      setActiveId(null);
    }
  }

  function setUniversity(errorId: number, value: string) {
    setCorrections((curr) => ({
      ...curr,
      [errorId]: { ...(curr[errorId] ?? {}), partner_university_id: value ? Number(value) : undefined },
    }));
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          Erreurs d&apos;import / sync ({errors.length})
        </h3>
      </div>

      {actionError ? (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </div>
      ) : null}

      <div className="mt-4 overflow-x-auto rounded-md border border-amber-200 bg-white">
        <table className="min-w-full divide-y divide-amber-100 text-sm">
          <thead className="bg-amber-50 text-left text-xs font-semibold uppercase text-amber-900">
            <tr>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Erreur</th>
              <th className="px-3 py-2">Correction</th>
              <th className="px-3 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {errors.map((error) => {
              const busy = isBusy || activeId === error.id;
              const kind = classifyError(error);
              const correction = corrections[error.id] ?? {};
              const canRetry = kind === "missing_university" && !!correction.partner_university_id;

              return (
                <tr key={error.id}>
                  {/* Source */}
                  <td className="whitespace-nowrap px-3 py-3">
                    <p className="font-medium text-gray-900">{error.external_id || "—"}</p>
                    <p className="text-xs text-gray-400">{error.source}</p>
                  </td>

                  {/* Erreur */}
                  <td className="px-3 py-3 max-w-xs">
                    <p className="text-red-700 text-xs break-words">{error.error_message || "Erreur inconnue"}</p>
                  </td>

                  {/* Correction contextuelle */}
                  <td className="px-3 py-3">
                    {kind === "missing_university" ? (
                      <div>
                        <p className="mb-1 text-xs text-gray-500">{getCorrectionLabel(kind)}</p>
                        <select
                          className="w-56 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900"
                          disabled={busy}
                          onChange={(e) => setUniversity(error.id, e.target.value)}
                          value={correction.partner_university_id ?? ""}
                        >
                          <option value="">Choisir une université</option>
                          {universities.map((u) => (
                            <option key={u.id} value={u.id}>{u.name}</option>
                          ))}
                        </select>
                      </div>
                    ) : (
                      <span className="text-xs italic text-gray-400">
                        {getCorrectionLabel(kind)}
                      </span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-3 py-3">
                    <div className="flex justify-end gap-2">
                      {kind === "missing_university" && (
                        <button
                          className="inline-flex h-8 items-center gap-1.5 rounded-md bg-[#1E3A8A] px-3 text-xs font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
                          disabled={!canRetry || busy}
                          onClick={() => handleRetry(error)}
                          type="button"
                        >
                          <RotateCw className="h-3 w-3" />
                          Relancer
                        </button>
                      )}
                      <button
                        className="inline-flex h-8 items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={busy}
                        onClick={() => handleIgnore(error)}
                        type="button"
                      >
                        <Check className="h-3 w-3" />
                        Ignorer
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
