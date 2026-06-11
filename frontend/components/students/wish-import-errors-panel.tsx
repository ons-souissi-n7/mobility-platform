"use client";

import { AlertTriangle, Check, ChevronDown, ChevronRight, Info, RotateCw } from "lucide-react";
import { useState } from "react";

import type { Agreement, RawImport, StudentWithEnrollment } from "@/lib/api/types";
import type { WishImportCorrection } from "@/lib/api/student-mutations";

type ErrorKind = "student_not_found" | "no_enrollment" | "agreement_not_found" | "no_correction";

const WISH_FIELD_LABELS: Record<string, string> = {
  ine: "INE",
  individu: "Individu",
  offre_de_sejour: "Offre de séjour",
  rank: "Rang",
};

function classifyWishError(error: RawImport): ErrorKind {
  const msg = (error.error_message ?? "").toLowerCase();
  if (msg.includes("étudiant introuvable") || msg.includes("etudiant introuvable")) return "student_not_found";
  if (msg.includes("inscription annuelle")) return "no_enrollment";
  if (msg.includes("accord introuvable") || msg.includes("offre de séjour")) return "agreement_not_found";
  return "no_correction";
}

function PayloadGrid({ payload }: { payload: Record<string, unknown> }) {
  const entries = Object.entries(payload).filter(([, v]) => v !== null && v !== undefined && v !== "");
  if (entries.length === 0) return <p className="text-xs text-gray-400 italic">Aucune donnée disponible</p>;

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">
            {WISH_FIELD_LABELS[key] ?? key}
          </dt>
          <dd className="mt-0.5 font-mono text-xs text-gray-800 break-all">
            {String(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
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
  const [expandedId, setExpandedId] = useState<number | null>(null);
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

  function toggleExpand(id: number) {
    setExpandedId((prev) => (prev === id ? null : id));
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

      <div className="mt-4 space-y-2">
        {errors.map((error) => {
          const busy = isBusy || activeId === error.id;
          const kind = classifyWishError(error);
          const correction = corrections[error.id] ?? {};
          const isExpanded = expandedId === error.id;
          const canRetry =
            (kind === "student_not_found" && !!correction.student_id) ||
            (kind === "agreement_not_found" && !!correction.agreement_id);

          return (
            <div
              key={error.id}
              className="rounded-md border border-amber-200 bg-white overflow-hidden"
            >
              {/* Summary row — click to expand */}
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
                <span className="font-mono text-xs text-gray-600 shrink-0 w-40 truncate">
                  {error.external_id || "—"}
                </span>
                <span className="flex-1 text-xs text-red-700 truncate">
                  {error.error_message || "Erreur inconnue"}
                </span>
                <span
                  className="shrink-0 ml-2 rounded-full px-2 py-0.5 text-[10px] font-medium bg-red-100 text-red-700"
                  onClick={(e) => e.stopPropagation()}
                >
                  {kind === "no_correction" ? "manuel" : "corrigeable"}
                </span>
              </button>

              {/* Expanded detail panel */}
              {isExpanded && (
                <div className="border-t border-amber-100 px-4 py-4 grid grid-cols-1 gap-6 sm:grid-cols-2">
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
                      <p className="mt-0.5 text-xs text-red-600">{error.error_message || "Erreur inconnue"}</p>
                    </div>
                  </div>

                  {/* Right: correction + actions */}
                  <div>
                    <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Correction proposée
                    </h4>

                    {kind === "student_not_found" && (
                      <div className="space-y-2">
                        <p className="text-xs text-gray-500">Associer à un étudiant inscrit</p>
                        <select
                          className="w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900"
                          disabled={busy}
                          value={correction.student_id ?? ""}
                          onChange={(e) =>
                            setCorrection(error.id, {
                              student_id: e.target.value ? Number(e.target.value) : undefined,
                            })
                          }
                        >
                          <option value="">Choisir un étudiant…</option>
                          {students.map((s) => (
                            <option key={s.student_id} value={s.student_id}>
                              {s.ine} — {s.last_name} {s.first_name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    {kind === "agreement_not_found" && (
                      <div className="space-y-2">
                        <p className="text-xs text-gray-500">Associer à un accord existant</p>
                        <select
                          className="w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-900"
                          disabled={busy}
                          value={correction.agreement_id ?? ""}
                          onChange={(e) =>
                            setCorrection(error.id, {
                              agreement_id: e.target.value ? Number(e.target.value) : undefined,
                            })
                          }
                        >
                          <option value="">Choisir un accord…</option>
                          {agreements.map((a) => (
                            <option key={a.id} value={a.id}>
                              {a.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    {kind === "no_enrollment" && (
                      <div className="flex items-start gap-2 rounded-md border border-blue-100 bg-blue-50 px-3 py-2">
                        <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" aria-hidden="true" />
                        <p className="text-xs text-blue-700">
                          Synchronisez d&apos;abord les inscriptions Pégase pour cet étudiant.
                        </p>
                      </div>
                    )}

                    {kind === "no_correction" && (
                      <p className="text-xs italic text-gray-400">
                        Ce type d&apos;erreur nécessite une correction manuelle dans la source de données.
                      </p>
                    )}

                    <div className="mt-4 flex gap-2">
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
