"use client";

import React, { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import {
  CheckCircle2,
  Clock,
  Download,
  FileDown,
  FileSpreadsheet,
  Heart,
  Loader2,
  Play,
  RefreshCw,
  TrendingUp,
  Upload,
  Users,
  X,
  XCircle,
} from "lucide-react";

import { ErrorBanner } from "@/components/ui/alert";
import { Btn, FileBtn } from "@/components/ui/btn";
import { Pagination } from "@/components/ui/pagination";
import { StatCard } from "@/components/ui/stat-card";
import { Toolbar } from "@/components/ui/toolbar";
import { DEFAULT_PAGE_SIZE } from "@/lib/config";
import { applyAcademicYearTransition } from "@/lib/api/academic-year-mutations";
import { getValidAgreements } from "@/lib/api/mobility-mutations";
import {
  downloadWishTemplate,
  exportWishesExcel,
  getAssignmentResults,
  getAssignmentStats,
  getAssignmentsForYear,
  getWishImportErrors,
  getWishesByYear,
  importWishesFromExcel,
  retryWishImportError,
  syncWishesFromMoveon,
  type WishImportCorrection,
} from "@/lib/api/outgoing-mutations";
import {
  getStudentSelectOptions,
  ignoreStudentImportError,
} from "@/lib/api/student-mutations";
import type {
  AcademicYear,
  Agreement,
  AgreementWish,
  Assignment,
  AssignmentResult,
  AssignmentStats,
  RawImport,
  SelectOption,
  StudentWishes,
} from "@/lib/api/types";
import { WishImportErrorsPanel } from "@/components/students/wish-import-errors-panel";

// ─── Labels métier ────────────────────────────────────────────────────────────
const SLOT_LABELS: Record<string, string> = {
  dept:        "Quota département",
  surplus:     "Quota mutualisé",
  alternative: "Destination alternative",
  unassigned:  "Non affecté",
};
const SLOT_COLORS: Record<string, string> = {
  dept:        "bg-emerald-100 text-emerald-800",
  surplus:     "bg-teal-100 text-teal-800",
  alternative: "bg-amber-100 text-amber-800",
  unassigned:  "bg-red-100 text-red-800",
};

const WISH_ERRORS_PAGE_SIZE = 25;
const POLL_INTERVAL_MS      = 3_000;
const POLL_TIMEOUT_MS       = 90_000;

// ─── Main component ──────────────────────────────────────────────────────────
export function OutgoingWorkspace({ academicYears }: { academicYears: AcademicYear[] }) {
  const defaultYear =
    academicYears.find((y) => y.status !== "closed") ?? academicYears[0] ?? null;

  // ── Wishes state (from WishesWorkspace) ──────────────────────────────────
  const [selectedYearId, setSelectedYearId]       = useState<number | null>(defaultYear?.id ?? null);
  const [wishes, setWishes]                       = useState<StudentWishes[]>([]);
  const [enrolledStudents, setEnrolledStudents]   = useState<SelectOption[]>([]);
  const [agreements, setAgreements]               = useState<Agreement[]>([]);
  const [isLoading, setIsLoading]                 = useState(false);
  const [syncInProgress, setSyncInProgress]       = useState(false);
  const [excelInProgress, setExcelInProgress]     = useState(false);
  const [exportInProgress, setExportInProgress]   = useState(false);
  const [wishImportErrors, setWishImportErrors]   = useState<RawImport[]>([]);
  const [wishErrorsTotalCount, setWishErrorsTotalCount] = useState(0);
  const [wishErrorsPage, setWishErrorsPage]       = useState(1);
  const [query, setQuery]                         = useState("");
  const [filterDept, setFilterDept]               = useState("");
  const [error, setError]                         = useState("");

  // ── Assignment state ──────────────────────────────────────────────────────
  const [assignment, setAssignment]   = useState<Assignment | null>(null);
  const [stats, setStats]             = useState<AssignmentStats | null>(null);
  const [resultsMap, setResultsMap]   = useState<Map<string, AssignmentResult>>(new Map());
  const [launching, setLaunching]     = useState(false);
  const [polling, setPolling]         = useState(false);

  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const selectedYear = academicYears.find((y) => y.id === selectedYearId) ?? null;

  // ── Stop poll ─────────────────────────────────────────────────────────────
  const stopPolling = useCallback(() => {
    if (pollingRef.current) clearTimeout(pollingRef.current);
    pollingRef.current = null;
    setPolling(false);
  }, []);

  // ── Load assignment results ───────────────────────────────────────────────
  const loadAssignment = useCallback(async (yearId: number) => {
    try {
      const data = await getAssignmentsForYear(yearId);
      const latest = data.results[0] ?? null;
      setAssignment(latest);
      if (latest) {
        const [resultsData, statsData] = await Promise.all([
          getAssignmentResults(latest.id, { page_size: 500 }),
          getAssignmentStats(latest.id),
        ]);
        const map = new Map<string, AssignmentResult>();
        for (const r of resultsData.results) map.set(r.student_ine, r);
        setResultsMap(map);
        setStats(statsData);
      } else {
        setResultsMap(new Map());
        setStats(null);
      }
    } catch {
      // silently ignore assignment load errors
    }
  }, []);

  // ── Load all data for a year ──────────────────────────────────────────────
  useEffect(() => {
    if (!selectedYearId) return;
    setIsLoading(true);
    setWishes([]);
    setError("");
    setQuery("");
    setFilterDept("");
    setAssignment(null);
    setStats(null);
    setResultsMap(new Map());
    stopPolling();

    Promise.all([
      getWishesByYear(selectedYearId),
      getWishImportErrors({ page: 1, page_size: WISH_ERRORS_PAGE_SIZE }),
      getStudentSelectOptions(selectedYearId),
      getValidAgreements(),
      getAssignmentsForYear(selectedYearId),
    ])
      .then(async ([w, errs, students, agr, assignmentsData]) => {
        setWishes(w);
        setWishImportErrors(errs.results);
        setWishErrorsTotalCount(errs.count);
        setWishErrorsPage(1);
        setEnrolledStudents(students);
        setAgreements(agr);

        const latest = assignmentsData.results[0] ?? null;
        setAssignment(latest);
        if (latest) {
          const [resultsData, statsData] = await Promise.all([
            getAssignmentResults(latest.id, { page_size: 500 }),
            getAssignmentStats(latest.id),
          ]);
          const map = new Map<string, AssignmentResult>();
          for (const r of resultsData.results) map.set(r.student_ine, r);
          setResultsMap(map);
          setStats(statsData);
        }
      })
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Erreur de chargement."),
      )
      .finally(() => setIsLoading(false));
  }, [selectedYearId, stopPolling]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => () => stopPolling(), [stopPolling]);

  // ── Polling after launch ──────────────────────────────────────────────────
  const startPolling = useCallback(
    (yearId: number, previousAssignmentId: number | null) => {
      setPolling(true);
      const startedAt = Date.now();

      const tick = async () => {
        if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
          stopPolling();
          setError("Le calcul dépasse 90 secondes. Veuillez rafraîchir la page.");
          return;
        }
        try {
          const data = await getAssignmentsForYear(yearId);
          const newest = data.results[0] ?? null;
          if (newest && newest.id !== previousAssignmentId) {
            stopPolling();
            await loadAssignment(yearId);
            return;
          }
        } catch { /* ignore */ }
        pollingRef.current = setTimeout(tick, POLL_INTERVAL_MS);
      };

      pollingRef.current = setTimeout(tick, POLL_INTERVAL_MS);
    },
    [stopPolling, loadAssignment],
  );

  // ── Launch affectation ────────────────────────────────────────────────────
  async function handleLaunch() {
    if (!selectedYearId) return;
    setLaunching(true);
    setError("");
    const previousId = assignment?.id ?? null;
    try {
      await applyAcademicYearTransition(selectedYearId, "launch-pre-assignment");
      startPolling(selectedYearId, previousId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors du lancement.");
    } finally {
      setLaunching(false);
    }
  }

  // ── Wishes actions ────────────────────────────────────────────────────────
  async function handleTemplateDownload() {
    if (!selectedYear) return;
    setError("");
    try { await downloadWishTemplate(selectedYear.id); }
    catch (err) { setError(err instanceof Error ? err.message : "Impossible de télécharger le template."); }
  }

  async function handleExcelImport(file: File) {
    if (!selectedYear) return;
    setError("");
    setExcelInProgress(true);
    try { await importWishesFromExcel(selectedYear.id, file); }
    catch (err) { setError(err instanceof Error ? err.message : "L'import Excel a échoué."); }
    finally { setExcelInProgress(false); }
  }

  async function handleSync() {
    if (!selectedYear) return;
    setError("");
    setSyncInProgress(true);
    try { await syncWishesFromMoveon(selectedYear.id); }
    catch (err) { setError(err instanceof Error ? err.message : "La synchronisation MoveON a échoué."); }
    finally { setSyncInProgress(false); }
  }

  async function handleExport() {
    if (!selectedYear) return;
    setError("");
    setExportInProgress(true);
    try { await exportWishesExcel(selectedYear.id, { deptCode: filterDept || undefined }); }
    catch (err) { setError(err instanceof Error ? err.message : "Erreur export."); }
    finally { setExportInProgress(false); }
  }

  async function loadWishErrors(page: number) {
    try {
      const errs = await getWishImportErrors({ page, page_size: WISH_ERRORS_PAGE_SIZE });
      setWishImportErrors(errs.results);
      setWishErrorsTotalCount(errs.count);
      setWishErrorsPage(page);
    } catch { /* silently ignore */ }
  }

  // ── Computed values ───────────────────────────────────────────────────────
  const deptOptions = [...new Set(wishes.map((w) => w.department_code).filter(Boolean))].sort() as string[];
  const maxRank     = wishes.reduce((m, w) => Math.max(m, w.wishes.length), 0);
  const studentsWithWishes = wishes.filter((w) => w.wishes.length > 0).length;

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

  const assignedPct =
    assignment && assignment.total_students > 0
      ? Math.round((assignment.assigned_count / assignment.total_students) * 100)
      : 0;

  // Année clôturée = lecture seule totale
  const isReadOnly = selectedYear?.status === "closed";
  // Verrouillé pendant le calcul ou pour une année clôturée
  const isLocked = polling || isReadOnly;

  // Fill-rate par département — total calculé depuis les résultats de l'affectation (même run que stats)
  const totalByDept = [...resultsMap.values()].reduce<Record<string, number>>((acc, r) => {
    if (r.department_code) acc[r.department_code] = (acc[r.department_code] ?? 0) + 1;
    return acc;
  }, {});
  const deptWithFillRate = stats
    ? stats.by_department.map((d) => {
        const total = totalByDept[d.department_code] ?? d.count;
        return { ...d, total, fill_rate: total > 0 ? Math.round((d.count / total) * 100) : 0 };
      })
    : [];

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Sélecteur d'année */}
      <div className="flex items-end gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Année universitaire</span>
          <select
            className="mt-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            value={selectedYearId ?? ""}
            onChange={(e) => setSelectedYearId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">— Choisir une année —</option>
            {[...academicYears]
              .sort((a, b) => b.start_date.localeCompare(a.start_date))
              .map((y) => (
                <option key={y.id} value={y.id}>
                  {y.label}{y.status === "closed" ? " (clôturée)" : ""}
                </option>
              ))}
          </select>
        </label>
        {isLoading && (
          <span className="mb-2 text-xs text-gray-400 animate-pulse">Chargement...</span>
        )}
      </div>

      {/* Bannière année clôturée */}
      {isReadOnly && (
        <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          <span className="font-semibold">Année clôturée</span> — consultation seule, imports et synchronisation désactivés.
        </div>
      )}

      {/* Bannière statut affectation */}
      {selectedYear && !isLoading && !isReadOnly && (
        <div className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${
          polling
            ? "border-amber-200 bg-amber-50"
            : assignment
              ? "border-emerald-200 bg-emerald-50"
              : "border-gray-200 bg-gray-50"
        }`}>
          {polling
            ? <Loader2 className="h-5 w-5 animate-spin text-amber-600" />
            : assignment
              ? <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              : <Clock className="h-5 w-5 text-gray-400" />}
          <span className={`text-sm font-medium ${
            polling ? "text-amber-700" : assignment ? "text-emerald-700" : "text-gray-600"
          }`}>
            {polling
              ? "Algorithme Gale-Shapley en cours — les résultats s'afficheront automatiquement."
              : assignment
                ? `Affectation calculée — ${assignment.assigned_count} étudiants placés sur ${assignment.total_students} (${assignedPct}%)`
                : "Aucune affectation calculée pour cette année. Cliquez sur « Lancer l'affectation »."}
          </span>
        </div>
      )}

      {/* Bannière statut affectation (lecture seule) */}
      {selectedYear && !isLoading && isReadOnly && assignment && (
        <div className="flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          <span className="text-sm font-medium text-emerald-700">
            {`Affectation calculée — ${assignment.assigned_count} étudiants placés sur ${assignment.total_students} (${assignedPct}%)`}
          </span>
        </div>
      )}

      {/* Stat cards vœux */}
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

      {/* Stat cards affectation */}
      {assignment && stats && !polling && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Taux d'affectation"
            value={`${assignedPct}%`}
            helper={`${assignment.assigned_count} étudiants partent en mobilité`}
            icon={CheckCircle2}
            tone="emerald"
          />
          <StatCard
            label="Sans affectation"
            value={assignment.unassigned_count}
            helper="Tous les quotas étaient pleins"
            icon={XCircle}
            tone="amber"
          />
          <StatCard
            label="Via quota département"
            value={stats.by_slot_type["dept"] ?? 0}
            helper="Place dans le quota réservé au département"
            icon={CheckCircle2}
            tone="blue"
          />
          <StatCard
            label="Via quota mutualisé"
            value={stats.by_slot_type["surplus"] ?? 0}
            helper="Place dans le pool partagé entre tous les depts"
            icon={CheckCircle2}
            tone="blue"
          />
        </div>
      )}

      {/* Toolbar */}
      <Toolbar
        search={{ value: query, onChange: setQuery, placeholder: "Rechercher par INE, nom, prénom..." }}
        actions={
          <>
            <Btn disabled={!selectedYear || isLocked} onClick={handleTemplateDownload}>
              <Download className="h-4 w-4" />
              Template
            </Btn>
            <FileBtn
              disabled={!selectedYear || excelInProgress || isLocked}
              onFile={(file) => { handleExcelImport(file).catch(() => null); }}
            >
              {excelInProgress ? <Upload className="h-4 w-4 animate-bounce" /> : <FileSpreadsheet className="h-4 w-4" />}
              {excelInProgress ? "Import..." : "Importer Excel"}
            </FileBtn>
            <span className="hidden h-6 w-px bg-gray-200 md:block" />
            <Btn disabled={syncInProgress || !selectedYear || isLocked} onClick={handleSync}>
              <RefreshCw className={`h-4 w-4 ${syncInProgress ? "animate-spin" : ""}`} />
              {syncInProgress ? "Synchronisation..." : "Sync MoveON"}
            </Btn>
            <span className="hidden h-6 w-px bg-gray-200 md:block" />
            <Btn disabled={!selectedYear || exportInProgress || isLoading} onClick={handleExport}>
              <FileDown className="h-4 w-4" />
              {exportInProgress ? "Export..." : "Exporter"}
            </Btn>
            <span className="hidden h-6 w-px bg-gray-200 md:block" />
            <Btn
              variant="primary"
              disabled={launching || isLocked || !selectedYear}
              onClick={() => { handleLaunch().catch(() => null); }}
            >
              {launching || polling
                ? <Loader2 className="h-4 w-4 animate-spin" />
                : <Play className="h-4 w-4" />}
              {launching ? "Lancement..." : polling ? "Calcul en cours..." : "Lancer l'affectation"}
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

      {/* Table principale */}
      {selectedYear ? (
        <WishesAssignmentTable
          rows={displayed}
          maxRank={maxRank}
          isBusy={isLoading || syncInProgress}
          resultsMap={resultsMap}
          hasAssignment={!!assignment}
        />
      ) : (
        <div className="rounded-md border border-dashed border-gray-300 px-4 py-12 text-center text-sm text-gray-400">
          Sélectionnez une année universitaire pour afficher les vœux.
        </div>
      )}

      {/* Taux de remplissage des quotas */}
      {stats && !polling && (stats.by_agreement.length > 0 || deptWithFillRate.length > 0) && (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="text-base font-semibold text-gray-900">
              Taux de remplissage des quotas
            </h2>
            <p className="mt-0.5 text-xs text-gray-500">
              Répartition des affectations par accord de mobilité et par département.
            </p>
          </div>

          {/* Par accord */}
          {stats.by_agreement.length > 0 && (
            <>
              <div className="border-b border-gray-100 bg-gray-50/60 px-6 py-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Par accord de mobilité</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                      <th className="px-6 py-3">Accord / Département</th>
                      <th className="px-6 py-3">Université partenaire</th>
                      <th className="px-6 py-3 text-right">Quota N7 / Quota dept</th>
                      <th className="px-6 py-3 text-right">Placés</th>
                      <th className="px-6 py-3 text-right">Taux</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {stats.by_agreement.map((row) => (
                      <React.Fragment key={row.agreement_year_id}>
                        {/* Ligne accord */}
                        <tr className="bg-white hover:bg-gray-50/80">
                          <td className="px-6 py-2.5 font-semibold text-gray-900">{row.agreement_name}</td>
                          <td className="px-6 py-2.5 text-gray-600">{row.university_name}</td>
                          <td className="px-6 py-2.5 text-right font-mono text-gray-700">{row.total_places}</td>
                          <td className="px-6 py-2.5 text-right font-mono text-gray-700">{row.assigned}</td>
                          <td className="px-6 py-2.5 text-right">
                            <FillRateCell rate={row.fill_rate} />
                          </td>
                        </tr>
                        {/* Sous-lignes par département */}
                        {row.by_department.map((dept) => (
                          <tr
                            key={`${row.agreement_year_id}-${dept.dept_code}`}
                            className="bg-gray-50/50 text-xs"
                          >
                            <td className="py-1.5 pl-10 pr-6 text-gray-500">
                              <span className="inline-flex items-center gap-1.5">
                                <span className="text-gray-300">└</span>
                                <span className="inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-600">
                                  {dept.dept_code}
                                </span>
                                <span className="text-gray-400">{dept.dept_name}</span>
                              </span>
                            </td>
                            <td className="px-6 py-1.5 text-gray-400">
                              {dept.quota === 0 ? (
                                <span className="rounded bg-amber-50 px-1.5 py-0.5 text-amber-600 text-xs">surplus inter-dépt</span>
                              ) : null}
                            </td>
                            <td className="px-6 py-1.5 text-right font-mono text-gray-500">
                              {dept.quota > 0 ? dept.quota : "—"}
                            </td>
                            <td className="px-6 py-1.5 text-right font-mono text-gray-600">{dept.assigned}</td>
                            <td className="px-6 py-1.5 text-right">
                              {dept.quota > 0 ? (
                                <FillRateCell rate={Math.round(dept.assigned / dept.quota * 100)} />
                              ) : (
                                <span className="text-xs text-gray-400">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Par département */}
          {deptWithFillRate.length > 0 && (
            <>
              <div className={`border-b border-gray-100 bg-gray-50/60 px-6 py-2 ${stats.by_agreement.length > 0 ? "border-t border-gray-200" : ""}`}>
                <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Par département</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                      <th className="px-6 py-3">Département</th>
                      <th className="px-6 py-3 text-right">Étudiants inscrits</th>
                      <th className="px-6 py-3 text-right">Étudiants placés</th>
                      <th className="px-6 py-3 text-right">Non affectés</th>
                      <th className="px-6 py-3 text-right">Taux d'affectation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {deptWithFillRate.map((row) => (
                      <tr key={row.department_id} className="hover:bg-gray-50">
                        <td className="px-6 py-3">
                          <span className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-700 mr-2">
                            {row.department_code}
                          </span>
                          <span className="text-gray-700">{row.department_name}</span>
                        </td>
                        <td className="px-6 py-3 text-right text-gray-700">{row.total}</td>
                        <td className="px-6 py-3 text-right text-gray-700">{row.count}</td>
                        <td className="px-6 py-3 text-right text-gray-500">{row.total - row.count}</td>
                        <td className="px-6 py-3 text-right">
                          <FillRateCell rate={row.fill_rate} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Par pays */}
          {stats.by_country.length > 0 && (
            <>
              <div className="border-t border-gray-200 border-b border-gray-100 bg-gray-50/60 px-6 py-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Par pays de destination</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                      <th className="px-6 py-3">Pays</th>
                      <th className="px-6 py-3 text-right">Étudiants placés</th>
                      <th className="px-6 py-3 text-right">Part (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {stats.by_country.map((row) => (
                      <tr key={row.country_iso2 || row.country_name_fr} className="hover:bg-gray-50">
                        <td className="px-6 py-3 font-medium text-gray-900">{row.country_name_fr}</td>
                        <td className="px-6 py-3 text-right font-mono text-gray-700">{row.count}</td>
                        <td className="px-6 py-3 text-right">
                          <FillRateCell rate={stats.assigned_count > 0 ? Math.round(row.count / stats.assigned_count * 100) : 0} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Par département × pays */}
          {stats.by_dept_country.length > 0 && (() => {
            const depts = [...new Set(stats.by_dept_country.map((r) => r.department_code))];
            return (
              <>
                <div className="border-t border-gray-200 border-b border-gray-100 bg-gray-50/60 px-6 py-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Par département et pays de destination</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                        <th className="px-6 py-3">Département / Pays</th>
                        <th className="px-6 py-3 text-right">Étudiants placés</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {depts.map((deptCode) => {
                        const rows = stats.by_dept_country.filter((r) => r.department_code === deptCode);
                        const deptName = rows[0]?.department_name ?? "";
                        const deptTotal = rows.reduce((s, r) => s + r.count, 0);
                        return (
                          <React.Fragment key={deptCode}>
                            <tr className="bg-white">
                              <td className="px-6 py-2.5 font-semibold text-gray-900">
                                <span className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-700 mr-2">{deptCode}</span>
                                {deptName}
                              </td>
                              <td className="px-6 py-2.5 text-right font-mono font-semibold text-gray-700">{deptTotal}</td>
                            </tr>
                            {rows.map((row) => (
                              <tr key={`${deptCode}-${row.country_iso2}`} className="bg-gray-50/50 text-xs">
                                <td className="py-1.5 pl-10 pr-6 text-gray-500">
                                  <span className="inline-flex items-center gap-1.5">
                                    <span className="text-gray-300">└</span>
                                    <span className="text-gray-600">{row.country_name_fr}</span>
                                  </span>
                                </td>
                                <td className="px-6 py-1.5 text-right font-mono text-gray-600">{row.count}</td>
                              </tr>
                            ))}
                          </React.Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            );
          })()}
        </div>
      )}

      {/* Erreurs d'import vœux — lecture seule si affectation déjà calculée */}
      <WishImportErrorsPanel
        agreements={agreements}
        errors={wishImportErrors}
        isBusy={syncInProgress}
        students={enrolledStudents}
        title="Erreurs d'import vœux MoveON"
        totalCount={wishErrorsTotalCount}
        page={wishErrorsPage}
        pageSize={WISH_ERRORS_PAGE_SIZE}
        onPageChange={loadWishErrors}
        {...(!isLocked && {
          onIgnore: async (err) => {
            await ignoreStudentImportError(err.id);
            await loadWishErrors(wishErrorsPage);
          },
          onRetry: async (err, correction: WishImportCorrection) => {
            await retryWishImportError(err.id, correction);
            await loadWishErrors(wishErrorsPage);
          },
        })}
      />
    </>
  );
}

// ─── Fill-rate cell ──────────────────────────────────────────────────────────
function FillRateCell({ rate }: { rate: number }) {
  const color = rate >= 80 ? "bg-emerald-500" : rate >= 50 ? "bg-amber-400" : "bg-red-400";
  const textColor = rate >= 80 ? "text-emerald-600" : rate >= 50 ? "text-amber-600" : "text-red-600";
  return (
    <div className="flex items-center justify-end gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-gray-200">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(rate, 100)}%` }} />
      </div>
      <span className={`w-12 text-right font-semibold ${textColor}`}>{rate}%</span>
    </div>
  );
}

// ─── Tableau pivot vœux + décision ───────────────────────────────────────────
function WishesAssignmentTable({
  rows,
  maxRank,
  isBusy,
  resultsMap,
  hasAssignment,
}: {
  rows: StudentWishes[];
  maxRank: number;
  isBusy: boolean;
  resultsMap: Map<string, AssignmentResult>;
  hasAssignment: boolean;
}) {
  const [page, setPage]       = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const totalPages   = Math.max(1, Math.ceil(rows.length / pageSize));
  const currentPage  = Math.min(page, totalPages);
  const pageItems    = rows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

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
              {rankCols.map((r) => <Th key={r}>Vœu {r}</Th>)}
              {hasAssignment && (
                <Th>
                  <span className="text-emerald-700">Décision d'affectation</span>
                </Th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {pageItems.map((row) => {
              const result = resultsMap.get(row.ine) ?? null;
              const isAssigned = result && result.slot_type !== "unassigned";
              return (
                <tr key={row.student_id} className="hover:bg-gray-50/50">
                  <Td>
                    <span className="font-mono text-xs text-gray-600">{row.ine}</span>
                  </Td>
                  <Td>
                    <div className="flex flex-col gap-0.5">
                      <div>
                        <span className="font-medium text-gray-900">{row.last_name.toUpperCase()}</span>
                        {" "}
                        <span className="text-gray-600">{row.first_name}</span>
                      </div>
                      {row.nationality_name_fr && (
                        <span className="text-xs text-gray-400">{row.nationality_name_fr}</span>
                      )}
                    </div>
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
                    const isChosen = isAssigned && result?.assigned_rank === r;
                    return (
                      <Td key={r}>
                        {wish ? (
                          <WishCell wish={wish} highlighted={!!isChosen} />
                        ) : (
                          <span className="text-xs italic text-gray-300">—</span>
                        )}
                      </Td>
                    );
                  })}
                  {hasAssignment && (
                    <Td>
                      <DecisionCell result={result} />
                    </Td>
                  )}
                </tr>
              );
            })}
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

// ─── Cellule vœu ─────────────────────────────────────────────────────────────
function WishCell({ wish, highlighted }: { wish: AgreementWish; highlighted: boolean }) {
  return (
    <div className={`min-w-40 space-y-0.5 rounded px-1.5 py-1 ${highlighted ? "bg-emerald-50 ring-1 ring-emerald-200" : ""}`}>
      <p className={`text-xs font-medium leading-tight truncate max-w-48 ${highlighted ? "text-emerald-800" : "text-gray-900"}`}>
        {wish.university_name}
      </p>
      <p className={`text-xs truncate max-w-48 ${highlighted ? "text-emerald-600" : "text-gray-500"}`}>
        {wish.agreement_name}
      </p>
      {wish.moveon_id && (
        <span className="inline-block rounded bg-blue-50 px-1 py-0.5 text-xs text-blue-600 font-mono">
          {wish.moveon_id}
        </span>
      )}
      {highlighted && (
        <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-emerald-700">
          <CheckCircle2 className="h-3 w-3" /> Vœu retenu
        </span>
      )}
    </div>
  );
}

// ─── Cellule décision ─────────────────────────────────────────────────────────
function DecisionCell({ result }: { result: AssignmentResult | null }) {
  if (!result) {
    return <span className="text-xs italic text-gray-300">—</span>;
  }

  const isAssigned = result.slot_type !== "unassigned";

  return (
    <div className="flex flex-col gap-1 min-w-44">
      {isAssigned ? (
        <>
          <p className="text-xs font-medium text-gray-900 truncate max-w-48">
            {result.agreement_name ?? "—"}
          </p>
          {result.university_name && (
            <p className="text-xs text-gray-500 truncate max-w-48">{result.university_name}</p>
          )}
        </>
      ) : null}
      <span className={`inline-flex w-fit items-center rounded-full px-2 py-0.5 text-xs font-medium ${SLOT_COLORS[result.slot_type] ?? "bg-gray-100 text-gray-700"}`}>
        {SLOT_LABELS[result.slot_type] ?? result.slot_type}
      </span>
    </div>
  );
}

// ─── Primitives ───────────────────────────────────────────────────────────────
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
