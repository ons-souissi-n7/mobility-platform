"use client";

import { AlertTriangle, Check, ChevronDown, ChevronRight, Info, RotateCw } from "lucide-react";
import { useState } from "react";

import { Pagination } from "@/components/ui/pagination";
import type { Agreement, RawImport, SelectOption } from "@/lib/api/types";
import type { WishImportCorrection } from "@/lib/api/outgoing-mutations";

const WISH_FIELD_LABELS: Record<string, string> = {
  ine: "INE",
  individu: "Individu",
  offre_de_sejour: "Offre de séjour",
  rank: "Rang",
};

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

type ErrorKind = "student_not_found" | "no_enrollment" | "agreement_not_found" | "no_correction";

function classifyWishError(error: RawImport): ErrorKind {
  const msg = (error.error_message ?? "").toLowerCase();
  if (msg.includes("étudiant introuvable") || msg.includes("etudiant introuvable")) return "student_not_found";
  if (msg.includes("inscription annuelle")) return "no_enrollment";
  if (msg.includes("accord introuvable") || msg.includes("offre de séjour")) return "agreement_not_found";
  return "no_correction";
}

type CorrectionForm = {
  student_id: number | "";
  agreement_id: number | "";
  rank: string;
};

function buildInitialForm(
  payload: Record<string, unknown>,
  students: SelectOption[],
  agreements: Agreement[],
): CorrectionForm {
  const payloadIne = String(payload.ine ?? "");
  const payloadOffer = String(payload.offre_de_sejour ?? "");
  const matchedStudent = students.find((s) => s.label.endsWith(`(${payloadIne})`));
  const matchedAgreement = agreements.find(
    (a) => a.name.toLowerCase() === payloadOffer.toLowerCase(),
  );
  return {
    student_id: matchedStudent?.id ?? "",
    agreement_id: matchedAgreement?.id ?? "",
    rank: String(payload.rank ?? ""),
  };
}

export function WishImportErrorsPanel({
  agreements,
  errors,
  isBusy,
  onIgnore,
  onRetry,
  students,
  title = "Erreurs d'import vœux",
  totalCount,
  page = 1,
  pageSize = 25,
  onPageChange,
}: {
  agreements: Agreement[];
  errors: RawImport[];
  isBusy: boolean;
  onIgnore?: (error: RawImport) => Promise<void>;
  onRetry?: (error: RawImport, correction: WishImportCorrection) => Promise<void>;
  students: SelectOption[];
  title?: string;
  totalCount?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
}) {
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
      setActionError(err instanceof Error ? err.message : "Erreur lors de l'opération.");
    } finally {
      setActiveId(null);
    }
  }

  function getForm(error: RawImport): CorrectionForm {
    if (!forms[error.id]) {
      const initial = buildInitialForm(error.payload, students, agreements);
      setForms((prev) => ({ ...prev, [error.id]: initial }));
      return initial;
    }
    return forms[error.id];
  }

  function updateForm(id: number, patch: Partial<CorrectionForm>) {
    setForms((prev) => ({
      ...prev,
      [id]: { ...(prev[id] ?? buildInitialForm({}, students, agreements)), ...patch },
    }));
  }

  function toggleExpand(id: number) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  const sortedAgreements = [...agreements].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <h3 className="text-sm font-semibold">
          {title} ({totalCount ?? errors.length})
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
          const isExpanded = expandedId === error.id;
          const form = isExpanded ? getForm(error) : null;

          return (
            <div
              key={error.id}
              className="rounded-md border border-amber-200 bg-white overflow-hidden"
            >
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
                <span className="shrink-0 ml-2 rounded-full px-2 py-0.5 text-[10px] font-medium bg-red-100 text-red-700">
                  {error.status}
                </span>
              </button>

              {isExpanded && form && (
                <div className="border-t border-amber-100 px-4 py-4 grid grid-cols-1 gap-6 sm:grid-cols-2">
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

                  <div>
                    <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Corriger et relancer
                    </h4>

                    {kind === "no_enrollment" ? (
                      <div className="flex items-start gap-2 rounded-md border border-blue-100 bg-blue-50 px-3 py-2">
                        <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" aria-hidden="true" />
                        <p className="text-xs text-blue-700">
                          Synchronisez d&apos;abord les inscriptions Pégase pour cet étudiant.
                        </p>
                      </div>
                    ) : kind === "no_correction" ? (
                      <p className="text-xs italic text-gray-400">
                        Ce type d&apos;erreur nécessite une correction manuelle dans la source de données.
                      </p>
                    ) : (
                      <div className="grid grid-cols-1 gap-2">
                        <label className="block">
                          <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Étudiant</span>
                          <select
                            className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900"
                            value={form.student_id}
                            onChange={(e) => updateForm(error.id, { student_id: e.target.value ? Number(e.target.value) : "" })}
                          >
                            <option value="">— Sélectionner un étudiant —</option>
                            {students.map((s) => (
                              <option key={s.id} value={s.id}>{s.label}</option>
                            ))}
                          </select>
                        </label>

                        <label className="block">
                          <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Offre de séjour (accord)</span>
                          <select
                            className="mt-0.5 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900"
                            value={form.agreement_id}
                            onChange={(e) => updateForm(error.id, { agreement_id: e.target.value ? Number(e.target.value) : "" })}
                          >
                            <option value="">— Sélectionner un accord —</option>
                            {sortedAgreements.map((a) => (
                              <option key={a.id} value={a.id}>
                                {a.name}
                                {a.valid_until ? ` — jusqu'au ${new Date(a.valid_until).toLocaleDateString("fr-FR")}` : ""}
                              </option>
                            ))}
                          </select>
                        </label>

                        <label className="block">
                          <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Rang</span>
                          <input
                            className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1.5 text-xs text-gray-900 font-mono focus:border-transparent focus:ring-1 focus:ring-[#1E3A8A]"
                            type="number"
                            min="1"
                            value={form.rank}
                            onChange={(e) => updateForm(error.id, { rank: e.target.value })}
                          />
                        </label>
                      </div>
                    )}

                    {(onIgnore || onRetry) && (
                      <div className="mt-4 flex gap-2">
                        {onRetry && kind !== "no_enrollment" && kind !== "no_correction" && (
                          <button
                            className="inline-flex h-8 items-center gap-1.5 rounded-md bg-[#1E3A8A] px-3 text-xs font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={busy || (form.student_id === "" && form.agreement_id === "")}
                            onClick={() =>
                              runAction(
                                () =>
                                  onRetry(error, {
                                    student_id: form.student_id !== "" ? form.student_id : undefined,
                                    agreement_id: form.agreement_id !== "" ? form.agreement_id : undefined,
                                    rank: form.rank ? Number(form.rank) : undefined,
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
                        {onIgnore && (
                          <button
                            className="inline-flex h-8 items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={busy}
                            onClick={() => runAction(() => onIgnore(error), error.id)}
                            type="button"
                          >
                            <Check className="h-3 w-3" />
                            Ignorer
                          </button>
                        )}
                      </div>
                    )}
                  </div>
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
