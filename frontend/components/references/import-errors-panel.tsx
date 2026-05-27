"use client";

import { AlertTriangle, Check, RotateCw } from "lucide-react";
import { useMemo, useState } from "react";

import type { Country, RawImport } from "@/lib/api/types";

type ImportErrorsPanelProps = {
  countries: Country[];
  errors: RawImport[];
  isBusy: boolean;
  onIgnore: (error: RawImport) => Promise<void>;
  onRetry: (error: RawImport, correction?: number | string) => Promise<void>;
  title?: string;
  retryField?: "country" | "code";
};

export function ImportErrorsPanel({
  countries,
  errors,
  isBusy,
  onIgnore,
  onRetry,
  title,
  retryField,
}: ImportErrorsPanelProps) {
  const [selectedCountries, setSelectedCountries] = useState<Record<number, string>>({});
  const [selectedCodes, setSelectedCodes] = useState<Record<number, string>>({});
  const [activeId, setActiveId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const sortedCountries = useMemo(
    () => [...countries].sort((a, b) => a.name_fr.localeCompare(b.name_fr)),
    [countries],
  );

  if (errors.length === 0) {
    return null;
  }

  async function runAction(action: () => Promise<void>, id: number) {
    setActiveId(id);
    setActionError(null);

    try {
      await action();
    } catch (error) {
      console.error(error);
      setActionError(
        error instanceof Error
          ? error.message
          : "Erreur inconnue lors de l'opération.",
      );
    } finally {
      setActiveId(null);
    }
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          {title ?? `Erreurs MoveON`} ({errors.length})
        </h3>
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
              const payload = error.payload;
              const countryId = Number(selectedCountries[error.id] || 0);
              const code = selectedCodes[error.id] ?? "";
              const busy = isBusy || activeId === error.id;

              const retryDisabled =
                busy ||
                (retryField === "country" && !countryId) ||
                (retryField === "code" && !code.trim());

              const correction =
                retryField === "country" ? countryId : retryField === "code" ? code : undefined;

              return (
                <tr key={error.id}>
                  <td className="whitespace-nowrap px-3 py-3 font-medium text-gray-900">
                    {error.external_id || "-"}
                  </td>
                  <td className="px-3 py-3 text-gray-700">
                    {String(payload.name || "Universite inconnue")}
                  </td>
                  <td className="px-3 py-3 text-red-700">
                    {error.error_message || "Import impossible"}
                  </td>
                  <td className="px-3 py-3">
                    {retryField === "country" ? (
                      <select
                        className="w-52 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900"
                        disabled={busy}
                        onChange={(e) =>
                          setSelectedCountries((v) => ({ ...v, [error.id]: e.target.value }))
                        }
                        value={selectedCountries[error.id] ?? ""}
                      >
                        <option value="">Choisir un pays</option>
                        {sortedCountries.map((country) => (
                          <option key={country.id} value={country.id}>
                            {country.name_fr} ({country.iso2})
                          </option>
                        ))}
                      </select>
                    ) : retryField === "code" ? (
                      <input
                        className="w-32 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900 placeholder-gray-400"
                        disabled={busy}
                        onChange={(e) =>
                          setSelectedCodes((v) => ({ ...v, [error.id]: e.target.value.toUpperCase() }))
                        }
                        placeholder="Ex: SN"
                        type="text"
                        value={code}
                      />
                    ) : null}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex justify-end gap-2">
                      <button
                        className="inline-flex h-9 items-center gap-2 rounded-md bg-[#1E3A8A] px-3 text-sm font-medium text-white transition-colors hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={retryDisabled}
                        onClick={() =>
                          runAction(() => onRetry(error, correction), error.id)
                        }
                        type="button"
                      >
                        <RotateCw className="h-4 w-4" aria-hidden="true" />
                        Relancer
                      </button>
                      <button
                        className="inline-flex h-9 items-center gap-2 rounded-md border border-gray-300 bg-white px-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={busy}
                        onClick={() => runAction(() => onIgnore(error), error.id)}
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
