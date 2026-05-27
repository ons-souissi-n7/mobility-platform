"use client";

import { AlertTriangle, Check, RotateCw } from "lucide-react";
import { useState } from "react";

import type { PartnerUniversity, RawImport } from "@/lib/api/types";
import type { MobilityImportRetryPayload } from "@/lib/api/mobility-mutations";

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

  if (errors.length === 0) {
    return null;
  }

  async function handleIgnore(error: RawImport) {
    setActiveId(error.id);
    setActionError(null);

    try {
      await onIgnore(error);
    } catch (ignoreError) {
      setActionError(
        ignoreError instanceof Error
          ? ignoreError.message
          : "Impossible de traiter l'erreur d'import.",
      );
    } finally {
      setActiveId(null);
    }
  }

  async function handleRetry(error: RawImport) {
    setActiveId(error.id);
    setActionError(null);

    try {
      await onRetry(error, corrections[error.id] ?? {});
    } catch (retryError) {
      setActionError(
        retryError instanceof Error
          ? retryError.message
          : "Impossible de relancer l'import.",
      );
    } finally {
      setActiveId(null);
    }
  }

  function updateCorrection(
    errorId: number,
    field: keyof MobilityImportRetryPayload,
    value: string,
  ) {
    setCorrections((current) => ({
      ...current,
      [errorId]: {
        ...(current[errorId] ?? {}),
        [field]: getCorrectionValue(field, value),
      },
    }));
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">Erreurs MoveON ({errors.length})</h3>
      </div>

      {actionError ? (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </div>
      ) : null}

      <div className="mt-4 overflow-hidden rounded-md border border-amber-200 bg-white">
        <table className="min-w-full divide-y divide-amber-100 text-sm">
          <thead className="bg-amber-50 text-left text-xs font-semibold uppercase text-amber-900">
            <tr>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Entite</th>
              <th className="px-3 py-2">Erreur</th>
              <th className="px-3 py-2">Correction</th>
              <th className="px-3 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {errors.map((error) => {
              const busy = isBusy || activeId === error.id;
              const correction = corrections[error.id] ?? {};
              const retryDisabled =
                busy || (error.entity === "agreement" && !correction.partner_university_id);

              return (
                <tr key={error.id}>
                  <td className="whitespace-nowrap px-3 py-3 font-medium text-gray-900">
                    {error.external_id || "-"}
                  </td>
                  <td className="px-3 py-3 text-gray-700">
                    {error.entity || String(error.payload.name || "Mobilite")}
                  </td>
                  <td className="px-3 py-3 text-red-700">
                    {error.error_message || "Import impossible"}
                  </td>
                  <td className="px-3 py-3">
                    {error.entity === "agreement" ? (
                      <select
                        className="w-64 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900"
                        disabled={busy}
                        onChange={(event) =>
                          updateCorrection(
                            error.id,
                            "partner_university_id",
                            event.target.value,
                          )
                        }
                        value={correction.partner_university_id ?? ""}
                      >
                        <option value="">Choisir une universite</option>
                        {universities.map((university) => (
                          <option key={university.id} value={university.id}>
                            {university.name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                        <div className="flex justify-end gap-2">
                          {error.entity === "agreement" ? (
                            <button
                              className="inline-flex h-9 items-center gap-2 rounded-md bg-[#1E3A8A] px-3 text-sm font-medium text-white transition-colors hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
                              disabled={retryDisabled}
                              onClick={() => handleRetry(error)}
                              type="button"
                            >
                              <RotateCw className="h-4 w-4" aria-hidden="true" />
                              Relancer
                            </button>
                          ) : null}

                          <button
                            className="inline-flex h-9 items-center gap-2 rounded-md border border-gray-300 bg-white px-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={busy}
                            onClick={() => handleIgnore(error)}
                            type="button"
                          >
                            <Check className="h-4 w-4" aria-hidden="true" />
                            Traite
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

function getCorrectionValue(
  field: keyof MobilityImportRetryPayload,
  value: string,
) {
  if (!value.trim()) {
    return undefined;
  }

  if (
    [
      "partner_university_id",
      "agreement_id",
      "academic_year_id",
      "total_places",
      "remaining_places",
      "total_duration",
    ].includes(field)
  ) {
    return Number(value);
  }

  return value;
}
