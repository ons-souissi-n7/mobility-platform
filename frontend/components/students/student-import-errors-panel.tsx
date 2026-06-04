"use client";

import { AlertTriangle, Check } from "lucide-react";
import { useState } from "react";

import type { RawImport } from "@/lib/api/types";

export function StudentImportErrorsPanel({
  errors,
  isBusy,
  onIgnore,
}: {
  errors: RawImport[];
  isBusy: boolean;
  onIgnore: (error: RawImport) => Promise<void>;
}) {
  const [activeId, setActiveId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

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

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          Erreurs d&apos;import étudiants ({errors.length})
        </h3>
      </div>

      {actionError && (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </div>
      )}

      <div className="mt-4 overflow-x-auto rounded-md border border-amber-200 bg-white">
        <table className="min-w-full divide-y divide-amber-100 text-sm">
          <thead className="bg-amber-50 text-left text-xs font-semibold uppercase text-amber-900">
            <tr>
              <th className="px-3 py-2">INE</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Erreur</th>
              <th className="px-3 py-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {errors.map((error) => {
              const busy = isBusy || activeId === error.id;
              return (
                <tr key={error.id}>
                  <td className="whitespace-nowrap px-3 py-3 font-mono text-xs text-gray-700">
                    {error.external_id || "—"}
                  </td>
                  <td className="whitespace-nowrap px-3 py-3 text-xs text-gray-400">
                    {error.source}
                  </td>
                  <td className="px-3 py-3 max-w-sm">
                    <p className="text-xs text-red-700 break-words">
                      {error.error_message || "Erreur inconnue"}
                    </p>
                  </td>
                  <td className="px-3 py-3 text-right">
                    <button
                      className="inline-flex h-8 items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={busy}
                      onClick={() => handleIgnore(error)}
                      type="button"
                    >
                      <Check className="h-3 w-3" />
                      Ignorer
                    </button>
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
