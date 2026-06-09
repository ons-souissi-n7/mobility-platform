"use client";

import { useEffect, useMemo, useState, type ElementType, type ReactNode } from "react";
import { BookOpen, Download, Eye, FileDown, FileSpreadsheet, GraduationCap, RefreshCw, Upload, Users, X } from "lucide-react";

import { ErrorBanner } from "@/components/ui/alert";
import { Btn, FileBtn } from "@/components/ui/btn";
import { ImportReportPanel } from "@/components/ui/import-report-panel";
import { Pagination } from "@/components/ui/pagination";
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
  syncStudentsFromPegase,
} from "@/lib/api/student-mutations";
import type {
  AcademicYear,
  ImportReport,
  RawImport,
  StudentDetail,
  StudentStats,
  StudentWithEnrollment,
} from "@/lib/api/types";
import { StudentImportErrorsPanel } from "./student-import-errors-panel";

// ---------------------------------------------------------------------------
// Workspace
// ---------------------------------------------------------------------------

export function StudentsWorkspace({ academicYears }: { academicYears: AcademicYear[] }) {
  const defaultYear =
    academicYears.find((y) => y.status !== "closed") ?? academicYears[0] ?? null;

  const [selectedYearId, setSelectedYearId] = useState<number | null>(defaultYear?.id ?? null);
  const [stats, setStats] = useState<StudentStats | null>(null);
  const [enrollments, setEnrollments] = useState<StudentWithEnrollment[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Text search
  const [query, setQuery] = useState("");

  // Breakdown filters
  const [filterLevel, setFilterLevel] = useState("");
  const [filterDept, setFilterDept] = useState("");
  const [filterParcours, setFilterParcours] = useState("");

  const [importInProgress, setImportInProgress] = useState(false);
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [exportInProgress, setExportInProgress] = useState(false);
  const [importReport, setImportReport] = useState<ImportReport | null>(null);
  const [importErrors, setImportErrors] = useState<RawImport[]>([]);
  const [error, setError] = useState("");
  const [selectedStudent, setSelectedStudent] = useState<StudentWithEnrollment | null>(null);

  const selectedYear = useMemo(
    () => academicYears.find((y) => y.id === selectedYearId) ?? null,
    [academicYears, selectedYearId],
  );

  useEffect(() => {
    if (!selectedYearId) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true);
    setStats(null);
    setEnrollments([]);
    setError("");
    setFilterLevel("");
    setFilterDept("");
    setFilterParcours("");

    Promise.all([
      getStudentStatsForYear(selectedYearId),
      getStudentsByYear(selectedYearId),
      getStudentImportErrors(),
    ])
      .then(([s, e, errs]) => {
        setStats(s);
        setEnrollments(e);
        setImportErrors(errs.filter((err) => err.source !== "moveon_student_wishes"));
      })
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Erreur de chargement."),
      )
      .finally(() => setIsLoading(false));
  }, [selectedYearId]);

  // ---------------------------------------------------------------------------
  // Filter options derived from current enrollments
  // ---------------------------------------------------------------------------

  const levelOptions = useMemo(() => {
    const seen = new Map<number, { id: number; code: string; name: string }>();
    for (const e of enrollments) {
      if (!seen.has(e.level_id))
        seen.set(e.level_id, { id: e.level_id, code: e.level_code, name: e.level_name });
    }
    return [...seen.values()].sort((a, b) => a.code.localeCompare(b.code));
  }, [enrollments]);

  const deptOptions = useMemo(() => {
    const seen = new Map<number, { id: number; code: string; name: string }>();
    for (const e of enrollments) {
      if (filterLevel && e.level_id !== Number(filterLevel)) continue;
      if (!seen.has(e.department_id))
        seen.set(e.department_id, { id: e.department_id, code: e.department_code, name: e.department_name });
    }
    return [...seen.values()].sort((a, b) => a.code.localeCompare(b.code));
  }, [enrollments, filterLevel]);

  const parcoursOptions = useMemo(() => {
    const seen = new Map<string, { key: string; code: string | null; label: string | null }>();
    for (const e of enrollments) {
      if (filterLevel && e.level_id !== Number(filterLevel)) continue;
      if (filterDept && e.department_id !== Number(filterDept)) continue;
      const key = e.parcours_id === null ? "none" : String(e.parcours_id);
      if (!seen.has(key)) seen.set(key, { key, code: e.parcours_code, label: e.parcours_label });
    }
    return [...seen.values()].sort((a, b) => (a.code ?? "").localeCompare(b.code ?? ""));
  }, [enrollments, filterLevel, filterDept]);

  // ---------------------------------------------------------------------------
  // Filtered + sorted enrollments
  // ---------------------------------------------------------------------------

  const displayEnrollments = useMemo(() => {
    const q = query.trim().toLowerCase();
    let result = enrollments;

    // Text search
    if (q) {
      result = result.filter((e) =>
        [e.ine, e.first_name, e.last_name, e.email, e.department_code, e.level_code, e.parcours_code ?? ""]
          .join(" ")
          .toLowerCase()
          .includes(q),
      );
    }

    // Breakdown filters
    if (filterLevel) result = result.filter((e) => e.level_id === Number(filterLevel));
    if (filterDept) result = result.filter((e) => e.department_id === Number(filterDept));
    if (filterParcours) {
      result = result.filter((e) =>
        filterParcours === "none" ? e.parcours_id === null : e.parcours_id === Number(filterParcours),
      );
    }

    // Sort: breakdown dims then name
    const hasFilter = filterLevel || filterDept || filterParcours;
    if (hasFilter) {
      result = [...result].sort((a, b) => {
        const lc = a.level_code.localeCompare(b.level_code);
        if (lc !== 0) return lc;
        const dc = a.department_code.localeCompare(b.department_code);
        if (dc !== 0) return dc;
        const pc = (a.parcours_code ?? "").localeCompare(b.parcours_code ?? "");
        if (pc !== 0) return pc;
        const ln = a.last_name.localeCompare(b.last_name);
        return ln !== 0 ? ln : a.first_name.localeCompare(b.first_name);
      });
    }

    return result;
  }, [enrollments, query, filterLevel, filterDept, filterParcours]);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  async function refreshYear() {
    if (!selectedYearId) return;
    setIsLoading(true);
    try {
      const [s, e, errs] = await Promise.all([
        getStudentStatsForYear(selectedYearId),
        getStudentsByYear(selectedYearId),
        getStudentImportErrors(),
      ]);
      setStats(s);
      setEnrollments(e);
      setImportErrors(errs.filter((err) => err.source !== "moveon_student_wishes"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur de rechargement.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleIgnoreImportError(err: RawImport) {
    await ignoreStudentImportError(err.id);
    setImportErrors((prev) => prev.filter((e) => e.id !== err.id));
  }

  async function handleExcelImport(file: File) {
    if (!selectedYear) { setError("Selectionnez une annee universitaire."); return; }
    setError(""); setImportReport(null); setImportInProgress(true);
    try {
      const report = await importStudentsFromExcel(selectedYear.id, file);
      setImportReport(report);
      await refreshYear();
    } catch (err) {
      setError(err instanceof Error ? err.message : "L'import Excel a echoue.");
    } finally { setImportInProgress(false); }
  }

  async function handleSync() {
    if (!selectedYear) { setError("Selectionnez une annee universitaire."); return; }
    setError(""); setImportReport(null); setSyncInProgress(true);
    try {
      const report = await syncStudentsFromPegase(selectedYear.id);
      setImportReport(report);
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
              setQuery("");
              setImportReport(null);
              setError("");
            }}
            value={selectedYearId ?? ""}
          >
            <option value="">— Choisir une annee —</option>
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
        search={{ value: query, onChange: setQuery, placeholder: "Rechercher par INE, nom, prénom, email..." }}
        actions={
          <>
            <TemplateButton isLoading={templateLoading} onClick={handleTemplateDownload} />
            <ExcelImportButton isLoading={importInProgress} onImport={handleExcelImport} />
            <SyncButton isLoading={syncInProgress} onClick={handleSync} />
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
              onChange={(e) => { setFilterLevel(e.target.value); setFilterDept(""); setFilterParcours(""); }}
              disabled={isLoading || levelOptions.length === 0}
            >
              <option value="">Tous les niveaux</option>
              {levelOptions.map((l) => (
                <option key={l.id} value={l.id}>{l.code}{l.name && l.name !== l.code ? ` — ${l.name}` : ""}</option>
              ))}
            </select>
            <select
              className="w-40 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700"
              value={filterDept}
              onChange={(e) => { setFilterDept(e.target.value); setFilterParcours(""); }}
              disabled={isLoading || deptOptions.length === 0}
            >
              <option value="">Tous les départements</option>
              {deptOptions.map((d) => (
                <option key={d.id} value={d.id}>{d.code}{d.name && d.name !== d.code ? ` — ${d.name}` : ""}</option>
              ))}
            </select>
            <select
              className="w-40 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700"
              value={filterParcours}
              onChange={(e) => setFilterParcours(e.target.value)}
              disabled={isLoading || parcoursOptions.length === 0}
            >
              <option value="">Tous les parcours</option>
              {parcoursOptions.map((p) => (
                <option key={p.key} value={p.key}>
                  {p.key === "none" ? "Tronc commun" : `${p.code ?? "—"}${p.label && p.label !== p.code ? ` — ${p.label}` : ""}`}
                </option>
              ))}
            </select>
            {hasFilter && (
              <button
                className="shrink-0 inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                onClick={() => { setFilterLevel(""); setFilterDept(""); setFilterParcours(""); }}
                type="button"
              >
                <X className="h-3.5 w-3.5" /> Réinitialiser
              </button>
            )}
            {hasFilter && (
              <span className="shrink-0 text-xs text-gray-400">
                {displayEnrollments.length} étudiant{displayEnrollments.length > 1 ? "s" : ""}
              </span>
            )}
          </>
        ) : undefined}
      />

      <ErrorBanner message={error} />

      {importReport && (
        <ImportReportPanel
          report={importReport}
          title="Import terminé"
          onClose={() => setImportReport(null)}
        />
      )}

      <div id="erreurs">
        <StudentImportErrorsPanel
          errors={importErrors}
          isBusy={isBusy}
          onIgnore={handleIgnoreImportError}
        />
      </div>

      {selectedStudent && (
        <StudentDetailPanel student={selectedStudent} onClose={() => setSelectedStudent(null)} />
      )}

      <div id="inscriptions">
        {selectedYear ? (
          <EnrollmentTable enrollments={displayEnrollments} isBusy={isBusy} onView={setSelectedStudent} />
        ) : (
          <div className="rounded-md border border-dashed border-gray-300 px-4 py-12 text-center text-sm text-gray-400">
            Selectionnez une annee universitaire pour afficher les inscriptions.
          </div>
        )}
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
// Enrollment table
// ---------------------------------------------------------------------------

function EnrollmentTable({
  enrollments,
  isBusy,
  onView,
}: {
  enrollments: StudentWithEnrollment[];
  isBusy: boolean;
  onView: (s: StudentWithEnrollment) => void;
}) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const totalPages = Math.max(1, Math.ceil(enrollments.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pageItems = enrollments.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { setPage(1); }, [enrollments]);

  if (enrollments.length === 0 && !isBusy) {
    return (
      <div className="rounded-md border border-dashed border-gray-300 px-4 py-10 text-center text-sm text-gray-500">
        Aucun etudiant. Importez un fichier Excel ou synchronisez depuis Pegase.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <Th>INE</Th><Th>Nom</Th><Th>Prenom</Th><Th>Email</Th>
              <Th>Genre</Th><Th>Nationalité</Th><Th>Departement</Th><Th>Niveau</Th><Th>Parcours</Th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {pageItems.map((e) => (
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
        page={currentPage}
        totalPages={totalPages}
        totalItems={enrollments.length}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
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

function TemplateButton({ isLoading, onClick }: { isLoading: boolean; onClick: () => void }) {
  return (
    <Btn disabled={isLoading} onClick={onClick}>
      <Download className="h-4 w-4" />
      Template
    </Btn>
  );
}

function ExcelImportButton({ isLoading, onImport }: { isLoading: boolean; onImport: (file: File) => void }) {
  return (
    <FileBtn disabled={isLoading} onFile={onImport}>
      {isLoading ? <Upload className="h-4 w-4 animate-bounce" /> : <FileSpreadsheet className="h-4 w-4" />}
      {isLoading ? "Import..." : "Importer Excel"}
    </FileBtn>
  );
}

function SyncButton({ isLoading, onClick }: { isLoading: boolean; onClick: () => void }) {
  return (
    <Btn disabled={isLoading} onClick={onClick}>
      <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
      {isLoading ? "Synchronisation..." : "Sync Pegase"}
    </Btn>
  );
}

