"use client";

import { AlertTriangle, Check, Info, RotateCw } from "lucide-react";
import { useState } from "react";

import type { Agreement, RawImport, StudentWithEnrollment } from "@/lib/api/types";
import type { WishImportCorrection } from "@/lib/api/student-mutations";

type ErrorKind = "student_not_found" | "no_enrollment" | "agreement_not_found" | "no_correction";

function classifyWishError(error: RawImport): ErrorKind {
  const msg = (error.error_message ?? "").toLowerCase();
  if (msg.includes("étudiant introuvable") || msg.includes("etudiant introuvable")) return "student_not_found";
  if (msg.includes("inscription annuelle")) return "no_enrollment";
  if (msg.includes("accord introuvable") || msg.includes("offre de séjour")) return "agreement_not_found";
  return "no_correction";
}

export function WishImportErrorsPanel({
  agreements,
  errors,
  isBusy,
  onIgnore,
  onRetry,
  students,
  title = "Erreurs d'import vœux",
}: {
  agreements: Agreement[];
  errors: RawImport[];
  isBusy: boolean;
  onIgnore: (error: RawImport) => Promise<void>;
  onRetry: (error: RawImport, correction: WishImportCorrection) => Promise<void>;
  students: StudentWithEnrollment[];
  title?: string;
}) {
  const [activeId, setActiveId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [corrections, setCorrections] = useState<Record<number, WishImportCorrection>>({});

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

  function setCorrection(id: number, patch: Partial<WishImportCorrection>) {
    setCorrections((prev) => ({ ...prev, [id]: { ...(prev[id] ?? {}), ...patch } }));
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          {title} ({errors.length})
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
              <th className="px-3 py-2">Identifiant</th>
              <th className="px-3 py-2">Erreur</th>
              <th className="px-3 py-2">Correction</th>
              <th className="px-3 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {errors.map((error) => {
              const busy = isBusy || activeId === error.id;
              const kind = classifyWishError(error);
              const correction = corrections[error.id] ?? {};
              const canRetry =
                (kind === "student_not_found" && !!correction.student_id) ||
                (kind === "agreement_not_found" && !!correction.agreement_id);

              return (
                <tr key={error.id}>
                  <td className="whitespace-nowrap px-3 py-3 font-mono text-xs text-gray-700">
                    {error.external_id || "—"}
                  </td>
                  <td className="max-w-xs px-3 py-3">
                    <p className="break-words text-xs text-red-700">
                      {error.error_message || "Erreur inconnue"}
                    </p>
                  </td>
                  <td className="px-3 py-3">
                    {kind === "student_not_found" && (
                      <div>
                        <p className="mb-1 text-xs text-gray-500">Associer à un étudiant inscrit</p>
                        <select
                          className="w-56 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900"
                          disabled={busy}
                          value={correction.student_id ?? ""}
                          onChange={(e) =>
                            setCorrection(error.id, {
                              student_id: e.target.value ? Number(e.target.value) : undefined,
                            })
                          }
                        >
                          <option value="">Choisir un étudiant</option>
                          {students.map((s) => (
                            <option key={s.student_id} value={s.student_id}>
                              {s.ine} — {s.last_name} {s.first_name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                    {kind === "agreement_not_found" && (
                      <div>
                        <p className="mb-1 text-xs text-gray-500">Associer à un accord existant</p>
                        <select
                          className="w-56 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900"
                          disabled={busy}
                          value={correction.agreement_id ?? ""}
                          onChange={(e) =>
                            setCorrection(error.id, {
                              agreement_id: e.target.value ? Number(e.target.value) : undefined,
                            })
                          }
                        >
                          <option value="">Choisir un accord</option>
                          {agreements.map((a) => (
                            <option key={a.id} value={a.id}>
                              {a.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                    {kind === "no_enrollment" && (
                      <div className="flex items-center gap-1.5 text-xs text-blue-700">
                        <Info className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                        Synchronisez d&apos;abord les inscriptions Pégase
                      </div>
                    )}
                    {kind === "no_correction" && (
                      <span className="text-xs italic text-gray-400">
                        Correction manuelle requise
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex justify-end gap-2">
                      {(kind === "student_not_found" || kind === "agreement_not_found") && (
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
