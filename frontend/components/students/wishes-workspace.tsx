"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Download, FileDown, FileSpreadsheet, Heart, RefreshCw, TrendingUp, Upload, Users, X } from "lucide-react";

import { ErrorBanner } from "@/components/ui/alert";
import { Btn, FileBtn } from "@/components/ui/btn";
import { ImportReportPanel } from "@/components/ui/import-report-panel";
import { Pagination } from "@/components/ui/pagination";
import { StatCard } from "@/components/ui/stat-card";
import { Toolbar } from "@/components/ui/toolbar";
import {
  downloadWishTemplate,
  exportWishesExcel,
  getStudentImportErrors,
  getStudentsByYear,
  getWishesByYear,
  ignoreStudentImportError,
  importWishesFromExcel,
  retryWishImportError,
  syncWishesFromMoveon,
  type WishImportCorrection,
} from "@/lib/api/student-mutations";
import { getAgreements } from "@/lib/api/mobility-mutations";
import type { Agreement, AcademicYear, AgreementWish, RawImport, StudentWithEnrollment, StudentWishes, WishSyncReport } from "@/lib/api/types";
import { WishImportErrorsPanel } from "./wish-import-errors-panel";


// ---------------------------------------------------------------------------
// Workspace
// ---------------------------------------------------------------------------

export function WishesWorkspace({ academicYears }: { academicYears: AcademicYear[] }) {
  const defaultYear =
    academicYears.find((y) => y.status !== "closed") ?? academicYears[0] ?? null;

  const [selectedYearId, setSelectedYearId] = useState<number | null>(defaultYear?.id ?? null);
  const [wishes, setWishes] = useState<StudentWishes[]>([]);
  const [enrolledStudents, setEnrolledStudents] = useState<StudentWithEnrollment[]>([]);
  const [agreements, setAgreements] = useState<Agreement[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [syncReport, setSyncReport] = useState<WishSyncReport | null>(null);
  const [excelInProgress, setExcelInProgress] = useState(false);
  const [excelReport, setExcelReport] = useState<WishSyncReport | null>(null);
  const [exportInProgress, setExportInProgress] = useState(false);
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
    setExcelReport(null);

    Promise.all([
      getWishesByYear(selectedYearId),
      getStudentImportErrors(),
      getStudentsByYear(selectedYearId),
      getAgreements(),
    ])
      .then(([w, errs, students, agr]) => {
        setWishes(w);
        setWishImportErrors(errs.filter((e) => e.source === "moveon_student_wishes"));
        setEnrolledStudents(students);
        setAgreements(agr);
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

  async function handleTemplateDownload() {
    if (!selectedYear) return;
    setError("");
    try {
      await downloadWishTemplate(selectedYear.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de télécharger le template.");
    }
  }

  async function handleExcelImport(file: File) {
    if (!selectedYear) return;
    setError("");
    setExcelReport(null);
    setExcelInProgress(true);
    try {
      const report = await importWishesFromExcel(selectedYear.id, file);
      setExcelReport(report);
      const [updated, errs] = await Promise.all([
        getWishesByYear(selectedYear.id),
        getStudentImportErrors(),
      ]);
      setWishes(updated);
      setWishImportErrors(errs.filter((e) => e.source === "moveon_student_wishes"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "L'import Excel a échoué.");
    } finally {
      setExcelInProgress(false);
    }
  }

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

  async function handleExport() {
    if (!selectedYear) return;
    setError("");
    setExportInProgress(true);
    try {
      await exportWishesExcel(selectedYear.id, { deptCode: filterDept || undefined });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur export.");
    } finally {
      setExportInProgress(false);
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

      <Toolbar
        search={{ value: query, onChange: setQuery, placeholder: "Rechercher par INE, nom, prénom..." }}
        actions={
          <>
            <Btn disabled={!selectedYear} onClick={handleTemplateDownload} title="Télécharger le template Excel vœux">
              <Download className="h-4 w-4" />
              Template
            </Btn>
            <FileBtn disabled={!selectedYear || excelInProgress} onFile={(file) => { handleExcelImport(file).catch(() => null); }}>
              {excelInProgress ? <Upload className="h-4 w-4 animate-bounce" /> : <FileSpreadsheet className="h-4 w-4" />}
              {excelInProgress ? "Import..." : "Importer Excel"}
            </FileBtn>
            <span className="hidden h-6 w-px bg-gray-200 md:block" />
            <Btn disabled={syncInProgress || !selectedYear} onClick={handleSync}>
              <RefreshCw className={`h-4 w-4 ${syncInProgress ? "animate-spin" : ""}`} />
              {syncInProgress ? "Synchronisation..." : "Sync MoveON"}
            </Btn>
            <span className="hidden h-6 w-px bg-gray-200 md:block" />
            <Btn disabled={!selectedYear || exportInProgress || isLoading} onClick={handleExport}>
              <FileDown className="h-4 w-4" />
              {exportInProgress ? "Export..." : "Exporter"}
            </Btn>
          </>
        }
        filters={selectedYear && deptOptions.length > 0 ? (
          <>
            <select
              className="w-40 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700"
              value={filterDept}
              onChange={(e) => setFilterDept(e.target.value)}
            >
              <option value="">Tous les départements</option>
              {deptOptions.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
            {filterDept && (
              <button
                className="shrink-0 inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                onClick={() => setFilterDept("")}
                type="button"
              >
                <X className="h-3.5 w-3.5" /> Réinitialiser
              </button>
            )}
          </>
        ) : undefined}
      />

      <ErrorBanner message={error} />

      {syncReport && (
        <ImportReportPanel
          report={syncReport}
          title="Synchronisation MoveON terminée"
          onClose={() => setSyncReport(null)}
        />
      )}

      {excelReport && (
        <ImportReportPanel
          report={excelReport}
          title="Import Excel terminé"
          onClose={() => setExcelReport(null)}
        />
      )}

      <WishImportErrorsPanel
        agreements={agreements}
        errors={wishImportErrors}
        isBusy={syncInProgress}
        students={enrolledStudents}
        title="Erreurs d'import vœux MoveON"
        onIgnore={async (err) => {
          await ignoreStudentImportError(err.id);
          setWishImportErrors((prev) => prev.filter((e) => e.id !== err.id));
        }}
        onRetry={async (err, correction: WishImportCorrection) => {
          await retryWishImportError(err.id, correction);
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

      <Pagination
        page={currentPage}
        totalPages={totalPages}
        totalItems={rows.length}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
        emptyLabel="Aucun étudiant"
      />
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
// Primitives
// ---------------------------------------------------------------------------

function Th({ children }: { children: ReactNode }) {
  return (
    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 whitespace-nowrap">
      {children}
    </th>
  );
}

function Td({ children }: { children: ReactNode }) {
  return <td className="px-4 py-3">{children}</td>;
}
