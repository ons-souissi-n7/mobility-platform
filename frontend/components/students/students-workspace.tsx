"use client";

import { useEffect, useMemo, useRef, useState, type ElementType, type ReactNode } from "react";
import { BookOpen, Download, Eye, FileDown, FileSpreadsheet, GraduationCap, RefreshCw, Upload, Users, X } from "lucide-react";

import { ErrorBanner } from "@/components/ui/alert";
import { Btn, FileBtn } from "@/components/ui/btn";
import { Pagination } from "@/components/ui/pagination";
import { DEFAULT_PAGE_SIZE } from "@/lib/config";
import { StatCard } from "@/components/ui/stat-card";
import { Toolbar } from "@/components/ui/toolbar";
import {
  downloadStudentTemplate,
  exportStudentsExcel,
  getStudentDetail,
  getStudentImportErrors,
  getStudentStatsForYear,
  getStudentsByYear,
  ignoreStudentImportError,
  importStudentsFromExcel,
  retryStudentImportError,
  syncStudentsFromPegase,
  type StudentByYearFilters,
  type StudentImportCorrection,
} from "@/lib/api/student-mutations";

const ERRORS_PAGE_SIZE = 25;
import type {
  AcademicYear,
  Country,
  Department,
  Level,
  PagedResponse,
  Parcours,
  RawImport,
  StudentDetail,
  StudentStats,
  StudentWithEnrollment,
} from "@/lib/api/types";
import { StudentImportErrorsPanel } from "./student-import-errors-panel";

// ---------------------------------------------------------------------------
// Workspace
// ---------------------------------------------------------------------------

export function StudentsWorkspace({
  academicYears,
  countries,
  departments,
  levels,
  parcourses,
}: {
  academicYears: AcademicYear[];
  countries: Country[];
  departments: Department[];
  levels: Level[];
  parcourses: Parcours[];
}) {
  const defaultYear =
    academicYears.find((y) => y.status !== "closed") ?? academicYears[0] ?? null;

  const [selectedYearId, setSelectedYearId] = useState<number | null>(defaultYear?.id ?? null);
  const [stats, setStats] = useState<StudentStats | null>(null);
  const [pagedData, setPagedData] = useState<PagedResponse<StudentWithEnrollment> | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  const [query, setQuery] = useState("");
  const [filterLevel, setFilterLevel] = useState("");
  const [filterDept, setFilterDept] = useState("");
  const [filterParcours, setFilterParcours] = useState("");

  const [importInProgress, setImportInProgress] = useState(false);
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [exportInProgress, setExportInProgress] = useState(false);

  const [importErrors, setImportErrors] = useState<RawImport[]>([]);
  const [errorsTotalCount, setErrorsTotalCount] = useState(0);
  const [errorsPage, setErrorsPage] = useState(1);
  const [error, setError] = useState("");
  const [selectedStudent, setSelectedStudent] = useState<StudentWithEnrollment | null>(null);

  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const selectedYear = useMemo(
    () => academicYears.find((y) => y.id === selectedYearId) ?? null,
    [academicYears, selectedYearId],
  );

  function buildFilters(overrides: Partial<StudentByYearFilters> = {}): StudentByYearFilters {
    return {
      search: (overrides.search ?? query) || undefined,
      level_id: (overrides.level_id !== undefined ? overrides.level_id : filterLevel ? Number(filterLevel) : undefined),
      department_id: (overrides.department_id !== undefined ? overrides.department_id : filterDept ? Number(filterDept) : undefined),
      parcours_id: (overrides.parcours_id !== undefined ? overrides.parcours_id : filterParcours ? Number(filterParcours) : undefined),
    };
  }

  async function doFetch(yearId: number, page: number, filters: StudentByYearFilters) {
    setIsLoading(true);
    try {
      const data = await getStudentsByYear(yearId, { ...filters, page, page_size: DEFAULT_PAGE_SIZE });
      setPagedData(data);
      setCurrentPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur de chargement.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (!selectedYearId) return;
    const id = selectedYearId;
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setStats(null);
      setPagedData(null);
      setCurrentPage(1);
      setError("");
      setFilterLevel("");
      setFilterDept("");
      setFilterParcours("");
      setQuery("");
      try {
        const [s, data, errs] = await Promise.all([
          getStudentStatsForYear(id),
          getStudentsByYear(id, { page: 1, page_size: DEFAULT_PAGE_SIZE }),
          getStudentImportErrors({ page: 1, page_size: ERRORS_PAGE_SIZE, year_id: id }),
        ]);
        if (cancelled) return;
        setStats(s);
        setPagedData(data);
        setImportErrors(errs.results);
        setErrorsTotalCount(errs.count);
        setErrorsPage(1);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Erreur de chargement.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void load();
    return () => { cancelled = true; };
  }, [selectedYearId]);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  async function loadStudentErrors(page: number) {
    try {
      const errs = await getStudentImportErrors({ page, page_size: ERRORS_PAGE_SIZE, year_id: selectedYearId ?? undefined });
      setImportErrors(errs.results);
      setErrorsTotalCount(errs.count);
      setErrorsPage(page);
    } catch {
      // silently ignore errors refresh failures
    }
  }

  async function refreshYear() {
    if (!selectedYearId) return;
    setIsLoading(true);
    try {
      const [s, data, errs] = await Promise.all([
        getStudentStatsForYear(selectedYearId),
        getStudentsByYear(selectedYearId, { ...buildFilters(), page: currentPage, page_size: DEFAULT_PAGE_SIZE }),
        getStudentImportErrors({ page: errorsPage, page_size: ERRORS_PAGE_SIZE, year_id: selectedYearId }),
      ]);
      setStats(s);
      setPagedData(data);
      setImportErrors(errs.results);
      setErrorsTotalCount(errs.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur de rechargement.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleQueryChange(value: string) {
    setQuery(value);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      if (!selectedYearId) return;
      setCurrentPage(1);
      void doFetch(selectedYearId, 1, buildFilters({ search: value }));
    }, 350);
  }

  function handleFilterLevel(value: string) {
    setFilterLevel(value);
    setFilterDept("");
    setFilterParcours("");
    setCurrentPage(1);
    if (selectedYearId) void doFetch(selectedYearId, 1, { ...buildFilters(), level_id: value ? Number(value) : undefined, department_id: undefined, parcours_id: undefined });
  }

  function handleFilterDept(value: string) {
    setFilterDept(value);
    setFilterParcours("");
    setCurrentPage(1);
    if (selectedYearId) void doFetch(selectedYearId, 1, { ...buildFilters(), department_id: value ? Number(value) : undefined, parcours_id: undefined });
  }

  function handleFilterParcours(value: string) {
    setFilterParcours(value);
    setCurrentPage(1);
    if (selectedYearId) void doFetch(selectedYearId, 1, { ...buildFilters(), parcours_id: value ? Number(value) : undefined });
  }

  function handleResetFilters() {
    setFilterLevel("");
    setFilterDept("");
    setFilterParcours("");
    setCurrentPage(1);
    if (selectedYearId) void doFetch(selectedYearId, 1, { search: query || undefined });
  }

  function handlePageChange(page: number) {
    setCurrentPage(page);
    if (selectedYearId) void doFetch(selectedYearId, page, buildFilters());
  }

  async function handleIgnoreImportError(err: RawImport) {
    await ignoreStudentImportError(err.id);
    await loadStudentErrors(errorsPage);
  }

  async function handleRetryImportError(err: RawImport, correction: StudentImportCorrection) {
    await retryStudentImportError(err.id, correction);
    await Promise.all([loadStudentErrors(errorsPage), refreshYear()]);
  }

  async function handleExcelImport(file: File) {
    if (!selectedYear) { setError("Selectionnez une annee universitaire."); return; }
    setError(""); setImportInProgress(true);
    try {
      await importStudentsFromExcel(selectedYear.id, file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "L'import Excel a echoue.");
    } finally { setImportInProgress(false); }
  }

  async function handleSync() {
    if (!selectedYear) { setError("Selectionnez une annee universitaire."); return; }
    setError(""); setSyncInProgress(true);
    try {
      await syncStudentsFromPegase(selectedYear.id);
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await refreshYear();
    } catch (err) {
      setError(err instanceof Error ? err.message : "La synchronisation Pegase a echoue.");
    } finally { setSyncInProgress(false); }
  }

  async function handleTemplateDownload() {
    setTemplateLoading(true);
    try { await downloadStudentTemplate(); }
    catch (err) { setError(err instanceof Error ? err.message : "Erreur telechargement."); }
    finally { setTemplateLoading(false); }
  }

  async function handleExport() {
    if (!selectedYear) return;
    setError("");
    setExportInProgress(true);
    try {
      await exportStudentsExcel(selectedYear.id, {
        levelId: filterLevel || undefined,
        deptId: filterDept || undefined,
        parcoursId: filterParcours || undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur export.");
    } finally {
      setExportInProgress(false);
    }
  }

  const hasFilter = !!(filterLevel || filterDept || filterParcours);
  const isBusy = importInProgress || syncInProgress || isLoading;
  const isLocked = !!selectedYear && selectedYear.status !== "initialization";

  const sortedLevels = useMemo(() => [...levels].sort((a, b) => a.code.localeCompare(b.code)), [levels]);
  const sortedDepts = useMemo(() => [...departments].sort((a, b) => a.code.localeCompare(b.code)), [departments]);
  const sortedParcourses = useMemo(() => [...parcourses].sort((a, b) => a.code.localeCompare(b.code)), [parcourses]);

  return (
    <>
      {/* Year selector */}
      <div className="flex items-end gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Annee universitaire</span>
          <select
            className="mt-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            onChange={(e) => {
              setSelectedYearId(e.target.value ? Number(e.target.value) : null);
              setError("");
            }}
            value={selectedYearId ?? ""}
          >
            <option value="">— Choisir une annee —</option>
            {[...academicYears]
              .sort((a, b) => b.start_date.localeCompare(a.start_date))
              .map((y) => (
                <option key={y.id} value={y.id}>
                  {y.label}{y.status === "closed" ? " (clôturée)" : ""}</option>
              ))}
          </select>
        </label>
        {isLoading && (
          <span className="mb-2 text-xs text-gray-400 animate-pulse">Chargement...</span>
        )}
      </div>

      {isLocked && selectedYear?.status !== "closed" && (
        <div className="flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-800">
          <span className="font-semibold">Campagne en cours</span> — consultation seule, imports et synchronisation désactivés.
        </div>
      )}
      {selectedYear?.status === "closed" && (
        <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          <span className="font-semibold">Année clôturée</span> — consultation seule, imports et synchronisation désactivés.
        </div>
      )}

      {/* Stat cards */}
      {selectedYear && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            helper={`Inscrits en ${selectedYear.label}`}
            icon={Users}
            label="Total inscrits"
            tone="blue"
            value={stats?.total ?? "—"}
          />
          <BreakdownCard
            icon={GraduationCap}
            isLoading={isLoading}
            items={(stats?.by_level ?? []).map((l) => ({ code: l.level_code, label: l.level_name, count: l.count }))}
            title="Par niveau"
          />
          <BreakdownCard
            icon={BookOpen}
            isLoading={isLoading}
            items={(stats?.by_department ?? []).map((d) => ({ code: d.department_code, label: d.department_name, count: d.count }))}
            title="Par departement"
          />
          <BreakdownCard
            icon={BookOpen}
            isLoading={isLoading}
            items={(stats?.by_parcours ?? []).map((p) => ({ code: p.parcours_code ?? "—", label: p.parcours_label ?? "Sans parcours", count: p.count }))}
            title="Par parcours"
          />
        </div>
      )}

      <Toolbar
        search={{ value: query, onChange: handleQueryChange, placeholder: "Rechercher par INE, nom, prénom..." }}
        actions={
          <>
            <TemplateButton isLoading={templateLoading} disabled={isLocked} onClick={handleTemplateDownload} />
            <ExcelImportButton isLoading={importInProgress} disabled={selectedYear?.status === "closed" || isLocked} onImport={handleExcelImport} />
            <SyncButton isLoading={syncInProgress} disabled={selectedYear?.status === "closed" || isLocked} onClick={handleSync} />
            <span className="hidden h-6 w-px bg-gray-200 md:block" />
            <Btn disabled={!selectedYear || exportInProgress || isLoading} onClick={handleExport}>
              <FileDown className="h-4 w-4" />
              {exportInProgress ? "Export..." : "Exporter"}
            </Btn>
          </>
        }
        filters={selectedYear ? (
          <>
            <select
              className="w-36 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700"
              value={filterLevel}
              onChange={(e) => handleFilterLevel(e.target.value)}
              disabled={isLoading}
            >
              <option value="">Tous les niveaux</option>
              {sortedLevels.map((l) => (
                <option key={l.id} value={l.id}>{l.code}{l.name && l.name !== l.code ? ` — ${l.name}` : ""}</option>
              ))}
            </select>
            <select
              className="w-40 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700"
              value={filterDept}
              onChange={(e) => handleFilterDept(e.target.value)}
              disabled={isLoading}
            >
              <option value="">Tous les départements</option>
              {sortedDepts.map((d) => (
                <option key={d.id} value={d.id}>{d.code}{d.name && d.name !== d.code ? ` — ${d.name}` : ""}</option>
              ))}
            </select>
            <select
              className="w-40 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700"
              value={filterParcours}
              onChange={(e) => handleFilterParcours(e.target.value)}
              disabled={isLoading}
            >
              <option value="">Tous les parcours</option>
              {sortedParcourses.map((p) => (
                <option key={p.id} value={p.id}>{p.code}{p.label && p.label !== p.code ? ` — ${p.label}` : ""}</option>
              ))}
            </select>
            {hasFilter && (
              <button
                className="shrink-0 inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                onClick={handleResetFilters}
                type="button"
              >
                <X className="h-3.5 w-3.5" /> Réinitialiser
              </button>
            )}
            {pagedData && (
              <span className="shrink-0 text-xs text-gray-400">
                {pagedData.count} étudiant{pagedData.count > 1 ? "s" : ""}
              </span>
            )}
          </>
        ) : undefined}
      />

      <ErrorBanner message={error} />

      {selectedStudent && (
        <StudentDetailPanel student={selectedStudent} onClose={() => setSelectedStudent(null)} />
      )}

      <div id="inscriptions">
        {selectedYear ? (
          <EnrollmentTable
            items={pagedData?.results ?? []}
            totalItems={pagedData?.count ?? 0}
            page={currentPage}
            pageSize={DEFAULT_PAGE_SIZE}
            isBusy={isBusy}
            onView={setSelectedStudent}
            onPageChange={handlePageChange}
          />
        ) : (
          <div className="rounded-md border border-dashed border-gray-300 px-4 py-12 text-center text-sm text-gray-400">
            Selectionnez une annee universitaire pour afficher les inscriptions.
          </div>
        )}
      </div>

      <div id="erreurs">
        <StudentImportErrorsPanel
          countries={countries}
          departments={departments}
          errors={importErrors}
          isBusy={isBusy || isLocked}
          levels={levels}
          onIgnore={handleIgnoreImportError}
          onRetry={handleRetryImportError}
          parcourses={parcourses}
          totalCount={errorsTotalCount}
          page={errorsPage}
          pageSize={ERRORS_PAGE_SIZE}
          onPageChange={loadStudentErrors}
        />
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Breakdown card (summary)
// ---------------------------------------------------------------------------

function BreakdownCard({
  title,
  items,
  isLoading,
  icon: Icon,
}: {
  title: string;
  items: { code: string; label: string; count: number }[];
  isLoading: boolean;
  icon: ElementType;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-4 w-4 text-gray-400" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        {items.length > 0 && <span className="ml-auto text-xs text-gray-400">{items.length}</span>}
      </div>
      {isLoading ? (
        <div className="space-y-1.5">
          {[1, 2, 3].map((i) => <div key={i} className="h-4 rounded bg-gray-100 animate-pulse" />)}
        </div>
      ) : items.length === 0 ? (
        <p className="text-xs italic text-gray-400">Aucune donnee</p>
      ) : (
        <div className="space-y-1.5">
          {items.map((item) => (
            <div key={item.code} className="flex items-center justify-between gap-2">
              <div className="min-w-0 flex items-center gap-1.5">
                <span className="shrink-0 text-xs font-medium text-gray-800">{item.code}</span>
                {item.label && item.label !== item.code && (
                  <span className="truncate text-xs text-gray-400">{item.label}</span>
                )}
              </div>
              <span className="shrink-0 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
                {item.count}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Enrollment table (server-paginated)
// ---------------------------------------------------------------------------

function EnrollmentTable({
  items,
  totalItems,
  page,
  pageSize,
  isBusy,
  onView,
  onPageChange,
}: {
  items: StudentWithEnrollment[];
  totalItems: number;
  page: number;
  pageSize: number;
  isBusy: boolean;
  onView: (s: StudentWithEnrollment) => void;
  onPageChange: (page: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  if (items.length === 0 && !isBusy) {
    return (
      <div className="rounded-md border border-dashed border-gray-300 px-4 py-10 text-center text-sm text-gray-500">
        Aucun etudiant. Importez un fichier Excel ou synchronisez depuis Pegase.
      </div>
    );
  }

  return (
    <div className={`overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-opacity ${isBusy ? "opacity-60" : ""}`}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <Th>INE</Th><Th>Nom</Th><Th>Prenom</Th><Th>Email</Th>
              <Th>Genre</Th><Th>Nationalité</Th><Th>Departement</Th><Th>Niveau</Th><Th>Parcours</Th><Th>GPA</Th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {items.map((e) => (
              <tr key={`${e.student_id}-${e.level_id}`} className="hover:bg-gray-50/50">
                <Td><span className="font-mono text-xs text-gray-600">{e.ine}</span></Td>
                <Td><span className="font-medium text-gray-900">{e.last_name.toUpperCase()}</span></Td>
                <Td>{e.first_name}</Td>
                <Td><span className="text-gray-600">{e.email || "—"}</span></Td>
                <Td>
                  {e.gender ? (
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      e.gender === "M" ? "bg-blue-50 text-blue-700" : "bg-pink-50 text-pink-700"
                    }`}>
                      {e.gender === "M" ? "Homme" : "Femme"}
                    </span>
                  ) : <span className="text-xs italic text-gray-300">—</span>}
                </Td>
                <Td>
                  <span className="text-xs text-gray-700">
                    {e.nationality_name_fr ?? "—"}
                  </span>
                </Td>
                <Td>
                  <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
                    {e.department_code}
                  </span>
                </Td>
                <Td>
                  <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                    {e.level_code}
                  </span>
                </Td>
                <Td>
                  {e.parcours_code
                    ? <span className="text-xs text-gray-600">{e.parcours_code}</span>
                    : <span className="text-xs italic text-gray-300">—</span>}
                </Td>
                <Td>
                  {e.gpa != null
                    ? <span className="font-mono text-xs text-gray-700">{parseFloat(e.gpa).toFixed(2)}</span>
                    : <span className="text-xs italic text-gray-300">—</span>}
                </Td>
                <td className="px-4 py-3 text-right">
                  <button
                    className="rounded-md border border-gray-200 p-1.5 text-gray-400 hover:bg-gray-50 hover:text-gray-700"
                    onClick={() => onView(e)}
                    title="Voir le détail"
                    type="button"
                  >
                    <Eye className="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination
        page={page}
        totalPages={totalPages}
        totalItems={totalItems}
        pageSize={pageSize}
        onPageChange={onPageChange}
        emptyLabel="Aucun étudiant"
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Student detail panel
// ---------------------------------------------------------------------------

function StudentDetailPanel({
  student,
  onClose,
}: {
  student: StudentWithEnrollment;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<StudentDetail | null>(null);
  const [loadedId, setLoadedId] = useState<number | null>(null);
  const loading = loadedId !== student.student_id;

  useEffect(() => {
    getStudentDetail(student.student_id).then((data) => {
      setDetail(data);
      setLoadedId(student.student_id);
    });
  }, [student.student_id]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 px-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white shadow-xl">

        {/* Header */}
        <div className="flex items-start justify-between border-b border-gray-200 px-6 py-5">
          <div>
            <h2 className="text-lg font-bold text-gray-900">
              {student.last_name.toUpperCase()} {student.first_name}
            </h2>
            <p className="mt-1 font-mono text-sm text-gray-500">{student.ine}</p>
          </div>
          <button
            className="rounded-md p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700"
            onClick={onClose}
            title="Fermer"
            type="button"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-6 px-6 py-5">

          {/* Informations personnelles */}
          <DetailSection title="Informations personnelles">
            <div className="space-y-2">
              <InfoRow label="Email" value={student.email || "—"} />
              <InfoRow
                label="Genre"
                value={student.gender === "M" ? "Homme" : student.gender === "F" ? "Femme" : "—"}
              />
              <InfoRow
                label="Nationalité"
                value={student.nationality_name_fr ?? "—"}
              />
            </div>
          </DetailSection>

          {/* Inscription courante */}
          <DetailSection title="Inscription (année en cours)">
            <div className="space-y-2">
              <InfoRow label="Département" value={student.department_code} />
              <InfoRow label="Niveau" value={student.level_code} />
              <InfoRow label="Parcours" value={student.parcours_code ?? "—"} />
              <InfoRow
                label="GPA"
                value={student.gpa != null ? <span className="font-mono">{student.gpa}</span> : "—"}
              />
            </div>
          </DetailSection>

          {/* Historique */}
          <DetailSection title="Historique des inscriptions">
            {loading ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="h-12 animate-pulse rounded-md bg-gray-100" />
                ))}
              </div>
            ) : detail?.enrollments.length ? (
              <div className="space-y-3">
                {detail.enrollments.map((e) => (
                  <div key={e.id} className="rounded-md border border-gray-100 bg-gray-50 px-4 py-3">
                    <p className="mb-2 text-sm font-semibold text-gray-800">{e.academic_year_label}</p>
                    <div className="space-y-1.5">
                      <InfoRow
                        label="Département"
                        value={
                          <span className="rounded bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-700">
                            {e.department_code}
                          </span>
                        }
                      />
                      <InfoRow
                        label="Niveau"
                        value={
                          <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                            {e.level_code}
                          </span>
                        }
                      />
                      <InfoRow
                        label="Parcours"
                        value={e.parcours_code ?? "—"}
                      />
                      <InfoRow
                        label="GPA"
                        value={
                          e.gpa != null
                            ? <span className="font-mono">{parseFloat(e.gpa).toFixed(2)}</span>
                            : "—"
                        }
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm italic text-gray-400">Aucune inscription enregistrée.</p>
            )}
          </DetailSection>

        </div>
      </div>
    </div>
  );
}

function DetailSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</h3>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex gap-3">
      <span className="w-28 shrink-0 text-xs text-gray-500">{label}</span>
      <span className="text-sm text-gray-900">{value ?? "—"}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

function Th({ children }: { children: ReactNode }) {
  return (
    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
      {children}
    </th>
  );
}

function Td({ children }: { children: ReactNode }) {
  return <td className="px-4 py-3">{children}</td>;
}

function TemplateButton({ isLoading, disabled, onClick }: { isLoading: boolean; disabled?: boolean; onClick: () => void }) {
  return (
    <Btn disabled={isLoading || disabled} onClick={onClick}>
      <Download className="h-4 w-4" />
      Template
    </Btn>
  );
}

function ExcelImportButton({ isLoading, disabled, onImport }: { isLoading: boolean; disabled?: boolean; onImport: (file: File) => void }) {
  return (
    <FileBtn disabled={isLoading || disabled} onFile={onImport}>
      {isLoading ? <Upload className="h-4 w-4 animate-bounce" /> : <FileSpreadsheet className="h-4 w-4" />}
      {isLoading ? "Import..." : "Importer Excel"}
    </FileBtn>
  );
}

function SyncButton({ isLoading, disabled, onClick }: { isLoading: boolean; disabled?: boolean; onClick: () => void }) {
  return (
    <Btn disabled={isLoading || disabled} onClick={onClick}>
      <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
      {isLoading ? "Synchronisation..." : "Sync Pegase"}
    </Btn>
  );
}
