"use client";

import { useState } from "react";
import { CheckCircle2, Clock, ExternalLink, Eye, FileText, Loader2, XCircle } from "lucide-react";
import { ErrorBanner } from "@/components/ui/alert";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { Modal } from "@/components/ui/modal";
import { Pagination } from "@/components/ui/pagination";
import { StatCard } from "@/components/ui/stat-card";
import { Toolbar } from "@/components/ui/toolbar";
import {
  fetchComplementaryMobilitiesAdmin,
  rejectMobility,
  validateMobility,
} from "@/lib/api/complementary";
import type { AcademicYear, ComplementaryMobility } from "@/lib/api/types";
import { formatDateShort } from "@/lib/utils";
import { MobilityStatusBadge } from "./status-badge";

const PAGE_SIZE = 25;

const STATUS_OPTIONS = [
  { value: "", label: "Tous les statuts" },
  { value: "pending", label: "En attente" },
  { value: "validated", label: "Validées" },
  { value: "rejected", label: "Rejetées" },
];

type RejectModal = {
  mobilityId: number;
  reason: string;
  submitting: boolean;
  error: string;
};

type Props = {
  initialMobilities: ComplementaryMobility[];
  initialTotalCount: number;
  academicYears: AcademicYear[];
  currentYear: AcademicYear | null;
};

export function ComplementaryWorkspace({
  initialMobilities,
  initialTotalCount,
  academicYears,
  currentYear,
}: Readonly<Props>) {
  const defaultYear =
    academicYears.find((y) => y.status !== "closed") ??
    [...academicYears].sort((a, b) => b.start_date.localeCompare(a.start_date))[0] ??
    null;

  const [selectedYearId, setSelectedYearId] = useState<number | null>(
    currentYear?.id ?? defaultYear?.id ?? null,
  );

  const [mobilities, setMobilities] = useState(initialMobilities);
  const [totalCount, setTotalCount] = useState(initialTotalCount);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [expTypeFilter, setExpTypeFilter] = useState("");

  const [loading, setLoading] = useState(false);
  const [actionError, setActionError] = useState("");
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [modal, setModal] = useState<RejectModal | null>(null);

  const { confirm, dialog: confirmDialog } = useConfirm();
  const [viewModal, setViewModal] = useState<ComplementaryMobility | null>(null);

  const selectedYear = academicYears.find((y) => y.id === selectedYearId) ?? null;
  const isReadOnly = !!selectedYear && selectedYear.status === "closed";

  const closedYearIds = new Set(
    academicYears.filter((y) => y.status === "closed").map((y) => y.id),
  );

  const pendingCount = mobilities.filter((m) => m.status === "pending").length;
  const validatedCount = mobilities.filter((m) => m.status === "validated").length;
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  // ── Data fetch ────────────────────────────────────────────────────────────

  async function fetchMobilities(opts: {
    s?: string;
    st?: string;
    exp?: string;
    p?: number;
    yId?: number | null;
  }) {
    setLoading(true);
    setActionError("");
    try {
      const yid = opts.yId !== undefined ? opts.yId : selectedYearId;
      const data = await fetchComplementaryMobilitiesAdmin({
        student_search: (opts.s ?? search) || undefined,
        status: (opts.st ?? statusFilter) || undefined,
        experience_type: (opts.exp ?? expTypeFilter) || undefined,
        year_id: yid ?? undefined,
        page: opts.p ?? page,
        page_size: PAGE_SIZE,
      });
      setMobilities(data.results);
      setTotalCount(data.count);
      if (opts.p !== undefined) setPage(opts.p);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Erreur lors du chargement.");
    } finally {
      setLoading(false);
    }
  }

  // ── Year change ───────────────────────────────────────────────────────────

  function handleYearChange(yearId: number | null) {
    setSelectedYearId(yearId);
    setSearch("");
    setStatusFilter("");
    setExpTypeFilter("");
    void fetchMobilities({ s: "", st: "", exp: "", p: 1, yId: yearId });
  }

  // ── Validate ──────────────────────────────────────────────────────────────

  async function handleValidate(id: number) {
    if (!(await confirm("Valider cette mobilité complémentaire ?", "Valider"))) return;
    setActionLoading(id);
    setActionError("");
    try {
      const updated = await validateMobility(id);
      setMobilities((prev) => prev.map((m) => (m.id === id ? updated : m)));
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Erreur lors de la validation.");
    } finally {
      setActionLoading(null);
    }
  }

  // ── Reject ────────────────────────────────────────────────────────────────

  async function handleRejectSubmit(e: React.SubmitEvent) {
    e.preventDefault();
    if (!modal) return;
    setModal((m) => m && { ...m, submitting: true, error: "" });
    try {
      const updated = await rejectMobility(modal.mobilityId, modal.reason);
      setMobilities((prev) =>
        prev.map((m) => (m.id === modal.mobilityId ? updated : m)),
      );
      setModal(null);
    } catch (err) {
      setModal((m) =>
        m && {
          ...m,
          submitting: false,
          error: err instanceof Error ? err.message : "Erreur lors du rejet.",
        },
      );
    }
  }

  // ── Edit ─────────────────────────────────────────────────────────────────

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {confirmDialog}

      {/* Sélecteur d'année universitaire */}
      <div>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Année universitaire</span>
          <select
            className="mt-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            value={selectedYearId ?? ""}
            onChange={(e) =>
              handleYearChange(e.target.value ? Number(e.target.value) : null)
            }
          >
            <option value="">Toutes les années</option>
            {[...academicYears]
              .sort((a, b) => b.start_date.localeCompare(a.start_date))
              .map((y) => (
                <option key={y.id} value={y.id}>
                  {y.label}
                  {y.status === "closed" ? " (clôturée)" : ""}
                </option>
              ))}
          </select>
        </label>
      </div>

      {/* Statistiques */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <StatCard
          icon={FileText}
          label="Total déclarations"
          value={totalCount}
          helper=""
          tone="blue"
        />
        <StatCard
          icon={Clock}
          label="En attente"
          value={pendingCount}
          helper="À traiter sur cette page"
          tone="amber"
        />
        <StatCard
          icon={CheckCircle2}
          label="Validées"
          value={validatedCount}
          helper="Sur cette page"
          tone="emerald"
        />
      </div>

      {/* Bannière année clôturée */}
      {isReadOnly && (
        <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          <span className="font-semibold">Année clôturée</span> — consultation seule,
          validation et rejet désactivés.
        </div>
      )}

      <ErrorBanner message={actionError} onDismiss={() => setActionError("")} />

      {/* Barre de filtres */}
      <Toolbar
        search={{
          value: search,
          onChange: (v) => {
            setSearch(v);
            void fetchMobilities({ s: v, p: 1 });
          },
          placeholder: "Nom ou INE de l'étudiant…",
        }}
        filters={
          <>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                void fetchMobilities({ st: e.target.value, p: 1 });
              }}
              className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>

            <input
              type="text"
              value={expTypeFilter}
              onChange={(e) => {
                setExpTypeFilter(e.target.value);
                void fetchMobilities({ exp: e.target.value, p: 1 });
              }}
              placeholder="Type d'expérience…"
              className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            />
          </>
        }
      />

      {/* Table + pagination */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-gray-400">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          <span className="text-sm">Chargement…</span>
        </div>
      ) : mobilities.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-400">
          Aucune mobilité complémentaire pour ces critères.
        </p>
      ) : (
        <div className="rounded-lg border bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {[
                    "Étudiant",
                    "Type d'expérience",
                    "Destination",
                    "Dates",
                    ...(selectedYearId === null ? ["Année"] : []),
                    "Statut",
                    "Justificatif",
                    "Actions",
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {mobilities.map((m) => (
                  <tr key={m.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">
                        {m.student_last_name} {m.student_first_name}
                      </p>
                      <p className="text-xs text-gray-400">{m.student_ine}</p>
                    </td>

                    <td className="px-4 py-3 text-gray-700">{m.experience_type}</td>

                    <td className="px-4 py-3">
                      <p className="text-gray-700">{m.destination_country_name}</p>
                      {m.destination_institution && (
                        <p className="text-xs text-gray-400">{m.destination_institution}</p>
                      )}
                    </td>

                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                      {formatDateShort(m.start_date)} → {formatDateShort(m.end_date)}
                    </td>

                    {selectedYearId === null && (
                      <td className="px-4 py-3 text-gray-600">{m.academic_year_label}</td>
                    )}

                    <td className="px-4 py-3">
                      <MobilityStatusBadge status={m.status} />
                      {m.status === "rejected" && m.rejection_reason && (
                        <p className="mt-1 max-w-48 text-xs text-red-600">
                          {m.rejection_reason}
                        </p>
                      )}
                    </td>

                    <td className="px-4 py-3">
                      {m.document_url ? (
                        <a
                          href={m.document_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-medium text-[#1E3A8A] hover:underline"
                        >
                          {m.document_name || "Justificatif"}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        <span className="text-xs text-gray-300">—</span>
                      )}
                    </td>

                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-2">
                        <button
                          type="button"
                          onClick={() => setViewModal(m)}
                          title="Voir le détail"
                          className="w-fit rounded-md border border-gray-200 p-1.5 text-gray-400 hover:bg-gray-50 hover:text-gray-700"
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </button>
                        {m.status === "pending" && !closedYearIds.has(m.academic_year_id) && (
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              disabled={actionLoading === m.id}
                              onClick={() => handleValidate(m.id)}
                              className="inline-flex items-center gap-1 rounded-md bg-green-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
                            >
                              {actionLoading === m.id ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <CheckCircle2 className="h-3 w-3" />
                              )}
                              Valider
                            </button>
                            <button
                              type="button"
                              disabled={actionLoading === m.id}
                              onClick={() =>
                                setModal({
                                  mobilityId: m.id,
                                  reason: "",
                                  submitting: false,
                                  error: "",
                                })
                              }
                              className="inline-flex items-center gap-1 rounded-md bg-red-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                            >
                              <XCircle className="h-3 w-3" />
                              Rejeter
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            totalItems={totalCount}
            pageSize={PAGE_SIZE}
            onPageChange={(p) => void fetchMobilities({ p })}
            emptyLabel="Aucune mobilité"
          />
        </div>
      )}

      {/* Modal détail */}
      {viewModal && (
        <Modal
          title={`${viewModal.student_last_name} ${viewModal.student_first_name}`}
          description={viewModal.student_ine}
          onClose={() => setViewModal(null)}
        >
          <div className="space-y-5">
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Déclaration
              </h3>
              <div className="space-y-2 text-sm">
                <DetailRow label="Type d'expérience" value={viewModal.experience_type} />
                <DetailRow
                  label="Destination"
                  value={
                    viewModal.destination_institution
                      ? `${viewModal.destination_institution} (${viewModal.destination_country_name})`
                      : viewModal.destination_country_name
                  }
                />
                <DetailRow
                  label="Période"
                  value={`${formatDateShort(viewModal.start_date)} → ${formatDateShort(viewModal.end_date)}`}
                />
                <DetailRow label="Année universitaire" value={viewModal.academic_year_label} />
              </div>
            </div>

            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Statut
              </h3>
              <MobilityStatusBadge status={viewModal.status} />
              {viewModal.status === "rejected" && viewModal.rejection_reason && (
                <p className="mt-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {viewModal.rejection_reason}
                </p>
              )}
            </div>

            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Justificatif
              </h3>
              {viewModal.document_url ? (
                <a
                  href={viewModal.document_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-[#1E3A8A] hover:bg-gray-50"
                >
                  <FileText className="h-4 w-4" />
                  {viewModal.document_name || "Ouvrir le justificatif"}
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              ) : (
                <p className="text-sm italic text-gray-400">
                  Aucun justificatif disponible (peut-être expiré ou supprimé après rejet).
                </p>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Modal rejet */}
      {modal && (
        <Modal
          title="Rejeter la demande"
          description="Indiquez le motif du rejet pour informer l'étudiant."
          onClose={() => setModal(null)}
        >
          <form onSubmit={handleRejectSubmit} className="space-y-4">
            {modal.error && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {modal.error}
              </div>
            )}

            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700" htmlFor="complementary-reject-reason">
                Motif du rejet *
              </label>
              <textarea
                id="complementary-reject-reason"
                required
                rows={4}
                value={modal.reason}
                onChange={(e) => setModal((m) => m && { ...m, reason: e.target.value })}
                placeholder="Indiquez le motif du rejet…"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
              />
            </div>

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setModal(null)}
                disabled={modal.submitting}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={modal.submitting || !modal.reason.trim()}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {modal.submitting ? "Rejet en cours…" : "Confirmer le rejet"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function DetailRow({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <div className="flex gap-3">
      <span className="w-36 shrink-0 text-xs text-gray-500">{label}</span>
      <span className="text-sm text-gray-900">{value || "—"}</span>
    </div>
  );
}
