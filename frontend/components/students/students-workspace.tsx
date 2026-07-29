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
  deleteStudentEnrollment,
  downloadStudentTemplate,
  exportStudentsExcel,
  getStudentImportErrors,
  getStudentStatsForYear,
  getStudentsByYear,
  ignoreStudentImportError,
  importStudentsFromExcel,
  retryStudentImportError,
  syncStudentsFromPegase,
  updateStudentEnrollment,
  type EnrollmentPatch,
  type StudentByYearFilters,
  type StudentImportCorrection,
} from "@/lib/api/student-mutations";
import { ActionButtons } from "@/components/ui/action-buttons";

const ERRORS_PAGE_SIZE = 25;
import type {
  AcademicYear,
  Country,
  Department,
  Level,
  PagedResponse,
  Parcours,
  RawImport,
  StudentStats,
  StudentWithEnrollment,
} from "@/lib/api/types";
import { Modal } from "@/components/ui/modal";
import { StudentImportErrorsPanel } from "./student-import-errors-panel";
import { StudentDetailPanel } from "./student-detail-panel";

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
  const [editModal, setEditModal] = useState<{ item: StudentWithEnrollment } | null>(null);

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
    if (!selectedYear) { setError("Sélectionnez une année universitaire."); return; }
    setError(""); setImportInProgress(true);
    try {
      await importStudentsFromExcel(selectedYear.id, file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "L'import Excel a échoué.");
    } finally { setImportInProgress(false); }
  }

  async function handleSync() {
    if (!selectedYear) { setError("Sélectionnez une année universitaire."); return; }
    setError(""); setSyncInProgress(true);
    try {
      await syncStudentsFromPegase(selectedYear.id);
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await refreshYear();
    } catch (err) {
      setError(err instanceof Error ? err.message : "La synchronisation Pégase a échoué.");
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

  async function handleDeleteEnrollment(enrollment: StudentWithEnrollment) {
    if (!window.confirm(`Supprimer l'inscription de ${enrollment.last_name} ${enrollment.first_name} (${enrollment.ine}) ? Cette action est irréversible.`)) return;
    setError("");
    try {
      await deleteStudentEnrollment(enrollment.enrollment_id);
      setPagedData((prev) => prev ? {
        ...prev,
        count: prev.count - 1,
        results: prev.results.filter((e) => e.enrollment_id !== enrollment.enrollment_id),
      } : prev);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de supprimer l'inscription.");
    }
  }

  async function handleSubmitEdit(patch: EnrollmentPatch) {
    if (!editModal) return;
    setError("");
    try {
      const updated = await updateStudentEnrollment(editModal.item.enrollment_id, patch);
      setPagedData((prev) => prev ? {
        ...prev,
        results: prev.results.map((e) => e.enrollment_id === updated.enrollment_id ? updated : e),
      } : prev);
      setEditModal(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de modifier l'inscription.");
    }
  }

  const hasFilter = !!(filterLevel || filterDept || filterParcours);
  const isBusy = importInProgress || syncInProgress || isLoading;
  const isLocked = !!selectedYear && selectedYear.status !== "initialization";
  const canModify = !!selectedYear && !isLocked;

  const sortedLevels = useMemo(() => [...levels].sort((a, b) => a.code.localeCompare(b.code)), [levels]);
  const sortedDepts = useMemo(() => [...departments].sort((a, b) => a.code.localeCompare(b.code)), [departments]);
  const sortedParcourses = useMemo(() => [...parcourses].sort((a, b) => a.code.localeCompare(b.code)), [parcourses]);

  return (
    <>
      {/* Year selector */}
      <div className="flex items-end gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Année universitaire</span>
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

      {editModal && (
        <Modal
          title="Modifier l'inscription"
          description={`${editModal.item.last_name} ${editModal.item.first_name} — ${editModal.item.ine}`}
          onClose={() => setEditModal(null)}
        >
          <EnrollmentEditForm
            item={editModal.item}
            departments={departments}
            levels={levels}
            parcourses={parcourses}
            onCancel={() => setEditModal(null)}
            onSubmit={handleSubmitEdit}
          />
        </Modal>
      )}

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
            canEdit={canModify}
            canDelete={canModify}
            onEdit={(e) => setEditModal({ item: e })}
            onView={setSelectedStudent}
            onDelete={handleDeleteEnrollment}
            onPageChange={handlePageChange}
          />
        ) : (
          <div className="rounded-md border border-dashed border-gray-300 px-4 py-12 text-center text-sm text-gray-400">
            Sélectionnez une année universitaire pour afficher les inscriptions.
          </div>
        )}
      </div>

      <div id="erreurs">
        <StudentImportErrorsPanel
          countries={countries}
          departments={departments}
          errors={importErrors}
          isBusy={isBusy}
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
  canEdit = true,
  canDelete = true,
  onView,
  onEdit,
  onDelete,
  onPageChange,
}: {
  items: StudentWithEnrollment[];
  totalItems: number;
  page: number;
  pageSize: number;
  isBusy: boolean;
  canEdit?: boolean;
  canDelete?: boolean;
  onView: (s: StudentWithEnrollment) => void;
  onEdit: (s: StudentWithEnrollment) => void;
  onDelete: (s: StudentWithEnrollment) => void;
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
              <Th>INE</Th><Th>Nom</Th><Th>Prénom</Th><Th>Email</Th>
              <Th>Genre</Th><Th>Nationalité</Th><Th>Département</Th><Th>Niveau</Th><Th>Parcours</Th><Th>GPA</Th>
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
                  <div className="flex items-center justify-end gap-1">
                    <button
                      className="rounded-md border border-gray-200 p-1.5 text-gray-400 hover:bg-gray-50 hover:text-gray-700"
                      onClick={() => onView(e)}
                      title="Voir le détail"
                      type="button"
                    >
                      <Eye className="h-3.5 w-3.5" />
                    </button>
                    <ActionButtons
                      onEdit={() => onEdit(e)}
                      editDisabled={!canEdit}
                      editDisabledTitle="Non autorisé dans cette phase"
                      onDelete={() => onDelete(e)}
                      deleteDisabled={!canDelete}
                      deleteDisabledTitle="Non autorisé dans cette phase"
                    />
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
        totalItems={totalItems}
        pageSize={pageSize}
        onPageChange={onPageChange}
        emptyLabel="Aucun étudiant"
      />
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

// ---------------------------------------------------------------------------
// Enrollment edit form
// ---------------------------------------------------------------------------

function EnrollmentEditForm({
  item,
  departments,
  levels,
  parcourses,
  onCancel,
  onSubmit,
}: {
  item: StudentWithEnrollment;
  departments: Department[];
  levels: Level[];
  parcourses: Parcours[];
  onCancel: () => void;
  onSubmit: (patch: EnrollmentPatch) => Promise<void>;
}) {
  const [deptId, setDeptId] = useState(String(item.department_id));
  const [levelId, setLevelId] = useState(String(item.level_id));
  const [parcoursId, setParcoursId] = useState(item.parcours_id ? String(item.parcours_id) : "");
  const [gpa, setGpa] = useState(item.gpa ?? "");
  const [isAlternant, setIsAlternant] = useState(item.is_alternant);
  const [isScholarship, setIsScholarship] = useState(item.is_scholarship);
  const [saving, setSaving] = useState(false);

  const sortedDepts = useMemo(() => [...departments].sort((a, b) => a.code.localeCompare(b.code)), [departments]);
  const sortedLevels = useMemo(() => [...levels].sort((a, b) => a.code.localeCompare(b.code)), [levels]);
  const filteredParcourses = useMemo(
    () => parcourses.filter((p) => p.department_id === Number(deptId)).sort((a, b) => a.code.localeCompare(b.code)),
    [parcourses, deptId],
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await onSubmit({
        department_id: Number(deptId),
        level_id: Number(levelId),
        parcours_id: parcoursId ? Number(parcoursId) : null,
        gpa: gpa || null,
        is_alternant: isAlternant,
        is_scholarship: isScholarship,
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Département *</label>
          <select
            className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
            value={deptId}
            onChange={(e) => { setDeptId(e.target.value); setParcoursId(""); }}
            required
          >
            {sortedDepts.map((d) => (
              <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Niveau *</label>
          <select
            className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
            value={levelId}
            onChange={(e) => setLevelId(e.target.value)}
            required
          >
            {sortedLevels.map((l) => (
              <option key={l.id} value={l.id}>{l.code}{l.name && l.name !== l.code ? ` — ${l.name}` : ""}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Parcours</label>
          <select
            className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
            value={parcoursId}
            onChange={(e) => setParcoursId(e.target.value)}
          >
            <option value="">— Aucun —</option>
            {filteredParcourses.map((p) => (
              <option key={p.id} value={p.id}>{p.code}{p.label && p.label !== p.code ? ` — ${p.label}` : ""}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">GPA</label>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            type="number"
            step="0.01"
            min="0"
            max="20"
            placeholder="Ex: 14.50"
            value={gpa}
            onChange={(e) => setGpa(e.target.value)}
          />
        </div>
      </div>
      <div className="flex gap-6">
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={isAlternant}
            onChange={(e) => setIsAlternant(e.target.checked)}
            className="rounded border-gray-300"
          />
          Alternant (FISA)
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={isScholarship}
            onChange={(e) => setIsScholarship(e.target.checked)}
            className="rounded border-gray-300"
          />
          Boursier
        </label>
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onCancel} className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
          Annuler
        </button>
        <button type="submit" disabled={saving} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
          {saving ? "Enregistrement..." : "Enregistrer"}
        </button>
      </div>
    </form>
  );
}
