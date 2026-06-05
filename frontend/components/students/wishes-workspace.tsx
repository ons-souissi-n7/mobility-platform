"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Heart, RefreshCw, TrendingUp, Users, X } from "lucide-react";

import { SearchInput } from "@/components/ui/search-input";
import { StatCard } from "@/components/ui/stat-card";
import {
  getStudentImportErrors,
  getWishesByYear,
  ignoreStudentImportError,
  syncWishesFromMoveon,
} from "@/lib/api/student-mutations";
import type { AcademicYear, AgreementWish, RawImport, StudentWishes, WishSyncReport } from "@/lib/api/types";
import { StudentImportErrorsPanel } from "./student-import-errors-panel";


// ---------------------------------------------------------------------------
// Workspace
// ---------------------------------------------------------------------------

export function WishesWorkspace({ academicYears }: { academicYears: AcademicYear[] }) {
  const defaultYear =
    academicYears.find((y) => y.status !== "closed") ?? academicYears[0] ?? null;

  const [selectedYearId, setSelectedYearId] = useState<number | null>(defaultYear?.id ?? null);
  const [wishes, setWishes] = useState<StudentWishes[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [syncReport, setSyncReport] = useState<WishSyncReport | null>(null);
  const [wishImportErrors, setWishImportErrors] = useState<RawImport[]>([]);
  const [query, setQuery] = useState("");
  const [filterDept, setFilterDept] = useState("");
  const [error, setError] = useState("");

  const selectedYear = academicYears.find((y) => y.id === selectedYearId) ?? null;

  useEffect(() => {
    if (!selectedYearId) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true);
    setWishes([]);
    setError("");
    setQuery("");
    setFilterDept("");
    setSyncReport(null);

    Promise.all([
      getWishesByYear(selectedYearId),
      getStudentImportErrors(),
    ])
      .then(([w, errs]) => {
        setWishes(w);
        setWishImportErrors(errs.filter((e) => e.source === "moveon_student_wishes"));
      })
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Erreur de chargement."),
      )
      .finally(() => setIsLoading(false));
  }, [selectedYearId]);

  // Départements disponibles pour le filtre
  const deptOptions = [...new Set(wishes.map((w) => w.department_code).filter(Boolean))].sort() as string[];

  // Nombre max de vœux (pour les colonnes du tableau)
  const maxRank = wishes.reduce((m, w) => Math.max(m, w.wishes.length), 0);

  // Filtrage
  const displayed = wishes.filter((w) => {
    if (filterDept && w.department_code !== filterDept) return false;
    if (query) {
      const q = query.toLowerCase();
      return (
        w.ine.toLowerCase().includes(q) ||
        w.first_name.toLowerCase().includes(q) ||
        w.last_name.toLowerCase().includes(q)
      );
    }
    return true;
  });

  async function handleSync() {
    if (!selectedYear) return;
    setError("");
    setSyncReport(null);
    setSyncInProgress(true);
    try {
      const report = await syncWishesFromMoveon(selectedYear.id);
      setSyncReport(report);
      const [updated, errs] = await Promise.all([
        getWishesByYear(selectedYear.id),
        getStudentImportErrors(),
      ]);
      setWishes(updated);
      setWishImportErrors(errs.filter((e) => e.source === "moveon_student_wishes"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "La synchronisation MoveON a échoué.");
    } finally {
      setSyncInProgress(false);
    }
  }

  const studentsWithWishes = wishes.filter((w) => w.wishes.length > 0).length;

  return (
    <>
      {/* Sélecteur d&apos;année */}
      <div className="flex items-end gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Année universitaire</span>
          <select
            className="mt-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            value={selectedYearId ?? ""}
            onChange={(e) => {
              setSelectedYearId(e.target.value ? Number(e.target.value) : null);
            }}
          >
            <option value="">— Choisir une année —</option>
            {[...academicYears]
              .sort((a, b) => b.start_date.localeCompare(a.start_date))
              .map((y) => (
                <option key={y.id} value={y.id}>{y.label}</option>
              ))}
          </select>
        </label>
        {isLoading && (
          <span className="mb-2 text-xs text-gray-400 animate-pulse">Chargement...</span>
        )}
      </div>

      {/* Stat cards */}
      {selectedYear && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            label="Étudiants avec vœux"
            value={studentsWithWishes}
            helper={`sur ${wishes.length} inscrits`}
            icon={Users}
            tone="blue"
          />
          <StatCard
            label="Total vœux saisis"
            value={wishes.reduce((s, w) => s + w.wishes.length, 0)}
            helper="toutes destinations confondues"
            icon={Heart}
            tone="blue"
          />
          <StatCard
            label="Vœux max par étudiant"
            value={maxRank}
            helper="nombre de choix le plus élevé"
            icon={TrendingUp}
            tone="blue"
          />
        </div>
      )}

      {/* Barre d&apos;outils */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm space-y-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Rechercher par INE, nom, prénom..."
          />
          <div className="flex items-center gap-2 shrink-0">
            <button
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={syncInProgress || !selectedYear}
              onClick={handleSync}
              type="button"
            >
              <RefreshCw className={`h-4 w-4 ${syncInProgress ? "animate-spin" : ""}`} />
              {syncInProgress ? "Synchronisation..." : "Sync MoveON"}
            </button>
          </div>
        </div>

        {/* Filtre département */}
        {selectedYear && deptOptions.length > 0 && (
          <div className="flex flex-wrap items-center gap-3 pt-1 border-t border-gray-100">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Filtrer :
            </span>
            <select
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700"
              value={filterDept}
              onChange={(e) => setFilterDept(e.target.value)}
            >
              <option value="">Tous les départements</option>
              {deptOptions.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            {filterDept && (
              <button
                className="inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                onClick={() => setFilterDept("")}
                type="button"
              >
                <X className="h-3.5 w-3.5" />
                Réinitialiser
              </button>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {syncReport && (
        <SyncReportPanel report={syncReport} onClose={() => setSyncReport(null)} />
      )}

      <StudentImportErrorsPanel
        errors={wishImportErrors}
        isBusy={syncInProgress}
        title="Erreurs d'import vœux MoveON"
        onIgnore={async (err) => {
          await ignoreStudentImportError(err.id);
          setWishImportErrors((prev) => prev.filter((e) => e.id !== err.id));
        }}
      />

      {selectedYear ? (
        <WishesTable rows={displayed} maxRank={maxRank} isBusy={isLoading || syncInProgress} />
      ) : (
        <div className="rounded-md border border-dashed border-gray-300 px-4 py-12 text-center text-sm text-gray-400">
          Sélectionnez une année universitaire pour afficher les vœux.
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Tableau pivot : étudiant × rang
// ---------------------------------------------------------------------------

function WishesTable({
  rows,
  maxRank,
  isBusy,
}: {
  rows: StudentWishes[];
  maxRank: number;
  isBusy: boolean;
}) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pageItems = rows.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const firstItem = rows.length === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const lastItem = Math.min(currentPage * pageSize, rows.length);

  // Reset to page 1 when data changes
  const [prevRows, setPrevRows] = useState(rows);
  if (prevRows !== rows) { setPrevRows(rows); setPage(1); }

  if (rows.length === 0 && !isBusy) {
    return (
      <div className="rounded-md border border-dashed border-gray-300 px-4 py-10 text-center text-sm text-gray-500">
        Aucun vœu. Synchronisez depuis MoveON pour importer les vœux étudiants.
      </div>
    );
  }

  const rankCols = Array.from({ length: maxRank }, (_, i) => i + 1);

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <Th>INE</Th>
              <Th>Étudiant</Th>
              <Th>Filière</Th>
              <Th>GPA</Th>
              {rankCols.map((r) => (
                <Th key={r}>Vœu {r}</Th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {pageItems.map((row) => (
              <tr key={row.student_id} className="hover:bg-gray-50/50">
                <Td>
                  <span className="font-mono text-xs text-gray-600">{row.ine}</span>
                </Td>
                <Td>
                  <span className="font-medium text-gray-900">{row.last_name.toUpperCase()}</span>
                  {" "}
                  <span className="text-gray-600">{row.first_name}</span>
                </Td>
                <Td>
                  <div className="flex flex-col gap-0.5">
                    {row.department_code ? (
                      <span className="inline-flex w-fit items-center rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-700">
                        {row.department_code}
                      </span>
                    ) : null}
                    {row.parcours_code ? (
                      <span className="inline-flex w-fit items-center rounded bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-700">
                        {row.parcours_code}
                      </span>
                    ) : null}
                    {!row.department_code && !row.parcours_code && (
                      <span className="text-xs italic text-gray-300">—</span>
                    )}
                  </div>
                </Td>
                <Td>
                  {row.gpa != null ? (
                    <span className="font-mono text-xs text-gray-700">
                      {parseFloat(row.gpa).toFixed(2)}
                    </span>
                  ) : (
                    <span className="text-xs italic text-gray-300">—</span>
                  )}
                </Td>
                {rankCols.map((r) => {
                  const wish = row.wishes.find((w) => w.rank === r);
                  return (
                    <Td key={r}>
                      {wish ? <WishCell wish={wish} /> : (
                        <span className="text-xs italic text-gray-300">—</span>
                      )}
                    </Td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3">
        <p className="text-sm text-gray-500">
          {rows.length === 0
            ? "Aucun étudiant"
            : `${firstItem}–${lastItem} sur ${rows.length}`}
        </p>
        <div className="flex items-center gap-3">
          <select
            className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#1E3A8A]"
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
          >
            {[10, 25, 50, 100].map((s) => (
              <option key={s} value={s}>{s} / page</option>
            ))}
          </select>
          <div className="flex items-center gap-1">
            <WPagBtn disabled={currentPage === 1} onClick={() => setPage(1)} title="Premiere page">
              <ChevronLeft className="h-3.5 w-3.5" /><ChevronLeft className="-ml-2 h-3.5 w-3.5" />
            </WPagBtn>
            <WPagBtn disabled={currentPage === 1} onClick={() => setPage((p) => p - 1)} title="Page precedente">
              <ChevronLeft className="h-3.5 w-3.5" />
            </WPagBtn>
            {wBuildPages(currentPage, totalPages).map((p, i) =>
              p === "..." ? (
                <span key={`e${i}`} className="px-1 text-xs text-gray-400">…</span>
              ) : (
                <button
                  key={p}
                  className={`min-w-[2rem] rounded-md border px-2 py-1 text-xs font-medium ${p === currentPage ? "border-[#1E3A8A] bg-[#1E3A8A] text-white" : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"}`}
                  onClick={() => setPage(p as number)}
                  type="button"
                >{p}</button>
              )
            )}
            <WPagBtn disabled={currentPage === totalPages} onClick={() => setPage((p) => p + 1)} title="Page suivante">
              <ChevronRight className="h-3.5 w-3.5" />
            </WPagBtn>
            <WPagBtn disabled={currentPage === totalPages} onClick={() => setPage(totalPages)} title="Derniere page">
              <ChevronRight className="h-3.5 w-3.5" /><ChevronRight className="-ml-2 h-3.5 w-3.5" />
            </WPagBtn>
          </div>
        </div>
      </div>
    </div>
  );
}

function WishCell({ wish }: { wish: AgreementWish }) {
  return (
    <div className="min-w-40 space-y-0.5">
      <p className="text-xs font-medium text-gray-900 leading-tight truncate max-w-48">
        {wish.university_name}
      </p>
      <p className="text-xs text-gray-500 truncate max-w-48">{wish.agreement_name}</p>
      {wish.moveon_id && (
        <span className="inline-block rounded bg-blue-50 px-1 py-0.5 text-xs text-blue-600 font-mono">
          {wish.moveon_id}
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Rapport de synchronisation
// ---------------------------------------------------------------------------

function SyncReportPanel({
  report,
  onClose,
}: {
  report: WishSyncReport;
  onClose: () => void;
}) {
  const hasIssues = report.unresolved.length > 0 || report.errors.length > 0;
  return (
    <div
      className={`rounded-lg border p-4 text-sm ${
        hasIssues ? "border-amber-200 bg-amber-50" : "border-emerald-200 bg-emerald-50"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className={`font-medium ${hasIssues ? "text-amber-800" : "text-emerald-800"}`}>
            Synchronisation terminée
          </p>
          <p className={hasIssues ? "text-amber-700" : "text-emerald-700"}>
            {report.created} créé{report.created > 1 ? "s" : ""},{" "}
            {report.updated} mis à jour
            {report.skipped > 0 ? `, ${report.skipped} ignoré(s) (hors fenêtre)` : ""}
            {report.unresolved.length > 0
              ? `, ${report.unresolved.length} non résolu(s)`
              : ""}
          </p>
          {report.unresolved.length > 0 && (
            <ul className="mt-2 space-y-0.5 text-xs text-amber-700">
              {report.unresolved.slice(0, 5).map((item, i) => (
                <li key={i}>
                  {item["individu"]} rang {item["rank"]} — {item["reason"]}
                </li>
              ))}
              {report.unresolved.length > 5 && (
                <li>… et {report.unresolved.length - 5} autre(s)</li>
              )}
            </ul>
          )}
        </div>
        <button
          className="shrink-0 text-gray-400 hover:text-gray-600"
          onClick={onClose}
          type="button"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagination helpers (wishes table)
// ---------------------------------------------------------------------------

function WPagBtn({ children, disabled, onClick, title }: { children: React.ReactNode; disabled: boolean; onClick: () => void; title: string }) {
  return (
    <button
      className="flex items-center rounded-md border border-gray-200 bg-white px-1.5 py-1 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
      disabled={disabled} onClick={onClick} title={title} type="button"
    >
      {children}
    </button>
  );
}

function wBuildPages(current: number, total: number): (number | "...")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | "...")[] = [];
  const add = (p: number) => { if (!pages.includes(p)) pages.push(p); };
  add(1);
  if (current > 4) pages.push("...");
  for (let p = Math.max(2, current - 2); p <= Math.min(total - 1, current + 2); p++) add(p);
  if (current < total - 3) pages.push("...");
  add(total);
  return pages;
}

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 whitespace-nowrap">
      {children}
    </th>
  );
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-4 py-3">{children}</td>;
}
