"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Download,
  FileDown,
  FileSpreadsheet,
  Globe,
  Info,
  PlaneLanding,
  X,
} from "lucide-react";

import { IncomingImportErrorsPanel } from "@/components/incoming/incoming-import-errors-panel";
import { CollapsibleStatsPanel } from "@/components/ui/collapsible-stats-panel";
import { ErrorBanner } from "@/components/ui/alert";
import { Btn, FileBtn } from "@/components/ui/btn";
import { StatCard } from "@/components/ui/stat-card";
import { Toolbar } from "@/components/ui/toolbar";
import { Pagination } from "@/components/ui/pagination";
import {
  downloadIncomingTemplate,
  exportIncomingExcel,
  getIncomingImportErrors,
  getIncomingStatsCountry,
  getIncomingStatsUniv,
  ignoreIncomingImportError,
  importIncomingFromExcel,
  listIncomingStudents,
} from "@/lib/api/incoming-mutations";
import type {
  AcademicYear,
  Country,
  Department,
  IncomingImportError,
  IncomingStatCountry,
  IncomingStatUniv,
  IncomingStudent,
  Level,
  MobilityCategory,
  Parcours,
  SelectOption,
} from "@/lib/api/types";

const ERRORS_PAGE_SIZE = 25;

function delay(ms: number) {
  return new Promise((res) => setTimeout(res, ms));
}

export function IncomingWorkspace({
  initialStudents,
  initialTotalCount,
  initialImportErrors,
  initialImportErrorsCount,
  academicYears,
  currentYear,
  countries,
  departments,
  levels,
  parcours,
  mobilityCategories,
  universities,
}: {
  initialStudents: IncomingStudent[];
  initialTotalCount: number;
  initialImportErrors: IncomingImportError[];
  initialImportErrorsCount: number;
  academicYears: AcademicYear[];
  currentYear: AcademicYear | null;
  countries: Country[];
  departments: Department[];
  levels: Level[];
  parcours: Parcours[];
  mobilityCategories: MobilityCategory[];
  universities: SelectOption[];
}) {
  const defaultYear =
    academicYears.find((y) => y.status !== "closed") ??
    [...academicYears].sort((a, b) => b.start_date.localeCompare(a.start_date))[0] ??
    null;

  const [selectedYearId, setSelectedYearId] = useState<number | null>(
    currentYear?.id ?? defaultYear?.id ?? null,
  );
  const selectedYear = academicYears.find((y) => y.id === selectedYearId) ?? null;
  const isReadOnly = !!selectedYear && selectedYear.status === "closed";
  const isInitializationPhase = !!selectedYear && selectedYear.status === "initialization";
  const canManage = !!selectedYear && !isInitializationPhase && !isReadOnly;

  const [students, setStudents] = useState(initialStudents);
  const [totalCount, setTotalCount] = useState(initialTotalCount);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [search, setSearch] = useState("");
  const [filterCountryId, setFilterCountryId] = useState<number | undefined>();
  const [filterDeptId, setFilterDeptId] = useState<number | undefined>();
  const [filterLevelId, setFilterLevelId] = useState<number | undefined>();
  const [filterParcoursId, setFilterParcoursId] = useState<number | undefined>();
  const [filterCategoryId, setFilterCategoryId] = useState<number | undefined>();
  const [filterUniversityId, setFilterUniversityId] = useState<number | undefined>();

  const hasActiveFilter = !!(
    search || filterCountryId || filterDeptId || filterLevelId ||
    filterParcoursId || filterCategoryId || filterUniversityId
  );

  const [importErrors, setImportErrors] = useState(initialImportErrors);
  const [importErrorsCount, setImportErrorsCount] = useState(initialImportErrorsCount);
  const [errorsPage, setErrorsPage] = useState(1);


  const [statsUniv, setStatsUniv] = useState<IncomingStatUniv[]>([]);
  const [statsCountry, setStatsCountry] = useState<IncomingStatCountry[]>([]);
  const [statsOpen, setStatsOpen] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);

  const [importInProgress, setImportInProgress] = useState(false);
  const [exportInProgress, setExportInProgress] = useState(false);
  const [actionError, setActionError] = useState("");

  // Unique countries in current list for quick stat
  const uniqueCountries = new Set(students.map((s) => s.country_id).filter(Boolean)).size;

  // ── Fetch ───────────────────────────────────────────────────────────────────

  async function fetchStudents(
    p: number,
    overrides: {
      s?: string;
      cId?: number;
      dId?: number;
      lId?: number;
      pId?: number;
      catId?: number;
      univId?: number;
      yId?: number | null;
      ps?: number;
    } = {},
  ) {
    const ps = overrides.ps ?? pageSize;
    const data = await listIncomingStudents({
      year_id: overrides.yId !== undefined ? overrides.yId ?? undefined : selectedYearId ?? undefined,
      search: overrides.s ?? search,
      country_id: overrides.cId ?? filterCountryId,
      department_id: overrides.dId ?? filterDeptId,
      level_id: overrides.lId ?? filterLevelId,
      parcours_id: overrides.pId ?? filterParcoursId,
      mobility_category_id: overrides.catId ?? filterCategoryId,
      university_id: overrides.univId ?? filterUniversityId,
      page: p,
      page_size: ps,
    });
    setStudents(data.results);
    setTotalCount(data.count);
    setPage(p);
  }

  async function loadErrors(p: number, yId?: number | null) {
    try {
      const yid = yId !== undefined ? yId ?? undefined : selectedYearId ?? undefined;
      const data = await getIncomingImportErrors({
        year_id: yid,
        page: p,
        page_size: ERRORS_PAGE_SIZE,
      });
      setImportErrors(data.results);
      setImportErrorsCount(data.count);
      setErrorsPage(p);
    } catch {
      // silently ignore
    }
  }

  // ── Year change ─────────────────────────────────────────────────────────────

  function handleYearChange(yearId: number | null) {
    setSelectedYearId(yearId);
    setSearch("");
    setFilterCountryId(undefined);
    setFilterDeptId(undefined);
    setFilterLevelId(undefined);
    setFilterParcoursId(undefined);
    setFilterCategoryId(undefined);
    setFilterUniversityId(undefined);
    void fetchStudents(1, {
      s: "", cId: undefined, dId: undefined, lId: undefined,
      pId: undefined, catId: undefined, univId: undefined, yId: yearId,
    });
    void loadErrors(1, yearId);
    if (statsOpen) void loadStats(yearId);
  }

  // ── Search / filter ─────────────────────────────────────────────────────────

  function handleSearch(v: string) {
    setSearch(v);
    void fetchStudents(1, { s: v });
  }

  function handleCountryFilter(e: React.ChangeEvent<HTMLSelectElement>) {
    const v = e.target.value ? Number(e.target.value) : undefined;
    setFilterCountryId(v);
    void fetchStudents(1, { cId: v });
  }

  function handleDeptFilter(e: React.ChangeEvent<HTMLSelectElement>) {
    const v = e.target.value ? Number(e.target.value) : undefined;
    setFilterDeptId(v);
    void fetchStudents(1, { dId: v });
  }

  function handleLevelFilter(e: React.ChangeEvent<HTMLSelectElement>) {
    const v = e.target.value ? Number(e.target.value) : undefined;
    setFilterLevelId(v);
    void fetchStudents(1, { lId: v });
  }

  function handleParcoursFilter(e: React.ChangeEvent<HTMLSelectElement>) {
    const v = e.target.value ? Number(e.target.value) : undefined;
    setFilterParcoursId(v);
    void fetchStudents(1, { pId: v });
  }

  function handleCategoryFilter(e: React.ChangeEvent<HTMLSelectElement>) {
    const v = e.target.value ? Number(e.target.value) : undefined;
    setFilterCategoryId(v);
    void fetchStudents(1, { catId: v });
  }

  function handleUniversityFilter(e: React.ChangeEvent<HTMLSelectElement>) {
    const v = e.target.value ? Number(e.target.value) : undefined;
    setFilterUniversityId(v);
    void fetchStudents(1, { univId: v });
  }

  function handleResetFilters() {
    setSearch("");
    setFilterCountryId(undefined);
    setFilterDeptId(undefined);
    setFilterLevelId(undefined);
    setFilterParcoursId(undefined);
    setFilterCategoryId(undefined);
    setFilterUniversityId(undefined);
    void fetchStudents(1, {
      s: "", cId: undefined, dId: undefined, lId: undefined,
      pId: undefined, catId: undefined, univId: undefined,
    });
  }

  // ── Import Excel ─────────────────────────────────────────────────────────────

  async function handleImport(file: File) {
    if (!selectedYearId) {
      setActionError("Sélectionnez une année académique avant d'importer.");
      return;
    }
    setActionError("");
    setImportInProgress(true);
    try {
      await importIncomingFromExcel(selectedYearId, file);
      await delay(3000);
      await fetchStudents(1, {});
      await loadErrors(1);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "L'import Excel a échoué.");
    } finally {
      setImportInProgress(false);
    }
  }

  // ── Export ───────────────────────────────────────────────────────────────────

  async function handleExport() {
    setActionError("");
    setExportInProgress(true);
    try {
      await exportIncomingExcel(selectedYearId ?? undefined, {
        countryId: filterCountryId,
        departmentId: filterDeptId,
      });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Erreur export.");
    } finally {
      setExportInProgress(false);
    }
  }

  // ── Stats ────────────────────────────────────────────────────────────────────

  async function loadStats(yId?: number | null) {
    setStatsLoading(true);
    try {
      const yid = yId !== undefined ? yId ?? undefined : selectedYearId ?? undefined;
      const [su, sc] = await Promise.all([
        getIncomingStatsUniv(yid),
        getIncomingStatsCountry(yid),
      ]);
      setStatsUniv(su);
      setStatsCountry(sc);
    } catch {
      // silently ignore
    } finally {
      setStatsLoading(false);
    }
  }

  function toggleStats() {
    const next = !statsOpen;
    setStatsOpen(next);
    if (next && statsUniv.length === 0) void loadStats();
  }

  // ── Ignore error ─────────────────────────────────────────────────────────────

  async function handleIgnoreError(error: IncomingImportError) {
    await ignoreIncomingImportError(error.id);
    await loadErrors(errorsPage);
  }

  // ── Template download ─────────────────────────────────────────────────────────

  async function handleTemplate() {
    if (!selectedYearId) {
      setActionError("Sélectionnez une année pour télécharger le gabarit.");
      return;
    }
    await downloadIncomingTemplate(selectedYearId);
  }

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Year selector */}
      <div>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Année universitaire</span>
          <select
            className="mt-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            value={selectedYearId ?? ""}
            onChange={(e) => handleYearChange(e.target.value ? Number(e.target.value) : null)}
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

      {/* Stats cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <StatCard
          icon={PlaneLanding}
          label="Étudiants entrants"
          value={totalCount}
          helper=""
          tone="blue"
        />
        <StatCard
          icon={Globe}
          label="Pays représentés"
          value={uniqueCountries}
          helper=""
          tone="amber"
        />
        <StatCard
          icon={AlertTriangle}
          label="Erreurs d'import"
          value={importErrorsCount}
          helper=""
          tone={importErrorsCount > 0 ? "amber" : "emerald"}
        />
      </div>

      {/* Phase banner */}
      {selectedYear && isInitializationPhase && (
        <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          <Info className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            Les mobilités entrantes sont gérées à partir de la phase{" "}
            <strong>Recommandation</strong>. L&apos;import et la saisie seront disponibles dès
            le passage à cette phase.
          </span>
        </div>
      )}

      {/* Action error */}
      {actionError && <ErrorBanner message={actionError} onDismiss={() => setActionError("")} />}

      {/* Toolbar */}
      <Toolbar
        search={{ value: search, onChange: handleSearch, placeholder: "Rechercher nom, prénom, email…" }}
        searchClassName="w-44 shrink-0"
        actions={
          <>
            <Btn variant="ghost" disabled={!canManage} onClick={handleTemplate}>
              <FileDown className="h-4 w-4" />
              Template
            </Btn>
            <FileBtn variant="primary" disabled={!canManage || importInProgress} onFile={handleImport}>
              <FileSpreadsheet className="h-4 w-4" />
              {importInProgress ? "Import en cours…" : "Importer Excel"}
            </FileBtn>
            <Btn variant="ghost" disabled={exportInProgress} onClick={handleExport}>
              <Download className="h-4 w-4" />
              {exportInProgress ? "Export…" : "Exporter"}
            </Btn>
          </>
        }
        filters={
          <>
            <select
              className="w-28 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700"
              value={filterDeptId ?? ""}
              onChange={handleDeptFilter}
            >
              <option value="">Département</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.code}</option>
              ))}
            </select>
            <select
              className="w-32 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700"
              value={filterCountryId ?? ""}
              onChange={handleCountryFilter}
            >
              <option value="">Pays</option>
              {[...countries].sort((a, b) => a.name_fr.localeCompare(b.name_fr)).map((c) => (
                <option key={c.id} value={c.id}>{c.name_fr}</option>
              ))}
            </select>
            <select
              className="w-24 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700"
              value={filterLevelId ?? ""}
              onChange={handleLevelFilter}
            >
              <option value="">Niveau</option>
              {levels.map((l) => (
                <option key={l.id} value={l.id}>{l.code}</option>
              ))}
            </select>
            <select
              className="w-28 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700"
              value={filterParcoursId ?? ""}
              onChange={handleParcoursFilter}
            >
              <option value="">Parcours</option>
              {parcours.map((p) => (
                <option key={p.id} value={p.id}>{p.code}</option>
              ))}
            </select>
            <select
              className="w-28 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700"
              value={filterCategoryId ?? ""}
              onChange={handleCategoryFilter}
            >
              <option value="">Cadre</option>
              {mobilityCategories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <select
              className="w-36 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700"
              value={filterUniversityId ?? ""}
              onChange={handleUniversityFilter}
            >
              <option value="">Université</option>
              {[...universities].sort((a, b) => a.label.localeCompare(b.label)).map((u) => (
                <option key={u.id} value={u.id}>{u.label}</option>
              ))}
            </select>
            {hasActiveFilter && (
              <button
                type="button"
                className="shrink-0 inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
                onClick={handleResetFilters}
              >
                <X className="h-3.5 w-3.5" /> Réinitialiser
              </button>
            )}
          </>
        }
      />

      {/* Students table */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead className="bg-gray-50 text-left font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                <th className="whitespace-nowrap px-3 py-3">Dept</th>
                <th className="whitespace-nowrap px-3 py-3">Civ.</th>
                <th className="whitespace-nowrap px-3 py-3">Nom</th>
                <th className="whitespace-nowrap px-3 py-3">Prénom</th>
                <th className="whitespace-nowrap px-3 py-3">Pays</th>
                <th className="whitespace-nowrap px-3 py-3">Université d&apos;origine</th>
                <th className="whitespace-nowrap px-3 py-3">Date naiss.</th>
                <th className="whitespace-nowrap px-3 py-3">Cadre</th>
                <th className="whitespace-nowrap px-3 py-3">Email personnel</th>
                <th className="whitespace-nowrap px-3 py-3">Email ENSEEIHT</th>
                <th className="whitespace-nowrap px-3 py-3">Durée</th>
                <th className="whitespace-nowrap px-3 py-3">Niveau</th>
                <th className="whitespace-nowrap px-3 py-3">Parcours</th>
                <th className="whitespace-nowrap px-3 py-3">Remarques</th>
                <th className="whitespace-nowrap px-3 py-3">Stage</th>
                <th className="whitespace-nowrap px-3 py-3">Diplôme</th>
                <th className="whitespace-nowrap px-3 py-3">Doctorat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {students.length === 0 ? (
                <tr>
                  <td colSpan={17} className="px-4 py-8 text-center text-gray-400">
                    Aucun étudiant entrant pour cette sélection.
                  </td>
                </tr>
              ) : (
                students.map((s) => {
                  const isOver30 =
                    s.birth_date != null &&
                    new Date().getFullYear() - new Date(s.birth_date).getFullYear() > 30;
                  return (
                    <tr key={s.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.department_code ?? "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.civility || "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 font-medium text-gray-900">{s.last_name}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-700">{s.first_name}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.country_name_fr ?? "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.origin_university_name || "—"}</td>
                      <td className={`whitespace-nowrap px-3 py-2 font-mono ${isOver30 ? "font-semibold text-red-600" : "text-gray-600"}`}>
                        {s.birth_date
                          ? new Date(s.birth_date + "T00:00:00").toLocaleDateString("fr-FR")
                          : "—"}
                        {isOver30 && (
                          <span className="ml-1.5 inline-flex items-center rounded bg-red-100 px-1 py-0.5 text-[10px] font-semibold text-red-700">
                            +30 ans
                          </span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.mobility_category_name ?? "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.personal_email || "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.n7_email || "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.duration || "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.level_code ?? "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">{s.parcours_code ?? "—"}</td>
                      <td className="max-w-[160px] truncate px-3 py-2 text-gray-600" title={s.remarks}>{s.remarks || "—"}</td>
                      <td className="max-w-[160px] truncate px-3 py-2 text-gray-600" title={s.internship_info}>{s.internship_info || "—"}</td>
                      <td className="max-w-[160px] truncate px-3 py-2 text-gray-600" title={s.diploma_info}>{s.diploma_info || "—"}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-gray-600">
                        {s.doctoral_continuation ? (
                          <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">Oui</span>
                        ) : "Non"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        <Pagination
          page={page}
          totalPages={Math.max(1, Math.ceil(totalCount / pageSize))}
          totalItems={totalCount}
          pageSize={pageSize}
          onPageChange={(p) => { void fetchStudents(p); }}
          onPageSizeChange={(ps) => {
            setPageSize(ps);
            void fetchStudents(1, { ps });
          }}
          emptyLabel="Aucun étudiant entrant pour cette sélection."
        />
      </div>

      {/* Statistics (collapsible) */}
      <CollapsibleStatsPanel
        isOpen={statsOpen}
        onToggle={toggleStats}
        isLoading={statsLoading}
        tables={[
          {
            heading: "Université d'origine × Département N7",
            dimensionLabel: "Université",
            showYear: false,
            rows: statsUniv.map((r) => ({
              dimension: r.university,
              department_code: r.department_code,
              department_name: r.department_name,
              academic_year_label: r.academic_year_label,
              count: r.count,
            })),
          },
          {
            heading: "Pays × Département N7",
            dimensionLabel: "Pays",
            showYear: false,
            rows: statsCountry.map((r) => ({
              dimension: r.country,
              department_code: r.department_code,
              department_name: r.department_name,
              academic_year_label: r.academic_year_label,
              count: r.count,
            })),
          },
        ]}
      />

      {/* Import errors */}
      <IncomingImportErrorsPanel
        errors={importErrors}
        isBusy={false}
        canManage={canManage}
        countries={countries}
        departments={departments}
        onIgnore={handleIgnoreError}
        onForce={async (err, payload) => {
          const { forceIncomingImportError } = await import("@/lib/api/incoming-mutations");
          await forceIncomingImportError(err.id, payload);
          await fetchStudents(1, {});
          await loadErrors(errorsPage);
        }}
        totalCount={importErrorsCount}
        page={errorsPage}
        pageSize={ERRORS_PAGE_SIZE}
        onPageChange={(p) => void loadErrors(p)}
      />
    </div>
  );
}
