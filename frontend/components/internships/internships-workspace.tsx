"use client";

import { useState } from "react";
import {
  Briefcase,
  ChevronDown,
  ChevronRight,
  Download,
  FileDown,
  FileSpreadsheet,
  Globe,
  Plus,
  RefreshCw,
  Upload,
  Users,
} from "lucide-react";

import { InternshipForm } from "@/components/internships/internship-form";
import { InternshipImportErrorsPanel } from "@/components/internships/internship-import-errors-panel";
import { InternshipsTable } from "@/components/internships/internships-table";
import { ErrorBanner } from "@/components/ui/alert";
import { Btn, FileBtn } from "@/components/ui/btn";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { Modal } from "@/components/ui/modal";
import { StatCard } from "@/components/ui/stat-card";
import {
  createInternship,
  deleteInternship,
  downloadInternshipTemplate,
  exportInternshipsExcel,
  forceInternshipImport,
  getInternshipImportErrors,
  ignoreInternshipImport,
  importInternshipsFromExcel,
  retryInternshipImport,
  syncInternshipsFromEudonet,
  updateInternship,
  type InternshipForcePayload,
  type InternshipPayload,
} from "@/lib/api/internship-mutations";
import { browserApi } from "@/lib/api/browser-client";
import type {
  AcademicYear,
  Country,
  Internship,
  InternshipImportError,
  PagedResponse,
} from "@/lib/api/types";

const PAGE_SIZE = 25;
const ERRORS_PAGE_SIZE = 25;

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function InternshipsWorkspace({
  initialInternships,
  initialTotalCount,
  countries,
  academicYears,
  currentYear,
  initialImportErrors,
  initialImportErrorsTotalCount,
}: {
  initialInternships: Internship[];
  initialTotalCount: number;
  countries: Country[];
  academicYears: AcademicYear[];
  currentYear: AcademicYear | null;
  initialImportErrors: InternshipImportError[];
  initialImportErrorsTotalCount: number;
}) {
  const defaultYear =
    academicYears.find((y) => y.status !== "closed") ??
    academicYears.sort((a, b) => b.start_date.localeCompare(a.start_date))[0] ??
    null;
  const [selectedYearId, setSelectedYearId] = useState<number | null>(
    currentYear?.id ?? defaultYear?.id ?? null,
  );

  const [internships, setInternships] = useState(initialInternships);
  const [totalCount, setTotalCount] = useState(initialTotalCount);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<{
    search?: string;
    country_id?: number;
  }>({});

  const [importErrors, setImportErrors] = useState(initialImportErrors);
  const [importErrorsTotalCount, setImportErrorsTotalCount] = useState(
    initialImportErrorsTotalCount,
  );
  const [importErrorsPage, setImportErrorsPage] = useState(1);
  const [errorsOpen, setErrorsOpen] = useState(initialImportErrors.length > 0);

  const selectedYear = academicYears.find((y) => y.id === selectedYearId) ?? null;
  const isReadOnly = !!selectedYear && selectedYear.status === "closed";
  // Aucun étudiant n'est encore importé en phase Initialisation — pas de stage à rattacher.
  const isInitializationPhase = !!selectedYear && selectedYear.status === "initialization";
  const canManageInternships = !!selectedYear && !isInitializationPhase && !isReadOnly;

  const [modal, setModal] = useState<{ item?: Internship } | null>(null);
  const { confirm, dialog: confirmDialog } = useConfirm();

  const [syncInProgress, setSyncInProgress] = useState(false);
  const [importInProgress, setImportInProgress] = useState(false);
  const [exportInProgress, setExportInProgress] = useState(false);
  const [actionError, setActionError] = useState("");

  // Derive stats
  const uniqueCountries = new Set(
    internships.map((i) => i.country_id).filter(Boolean),
  ).size;
  const uniqueStudents = new Set(internships.map((i) => i.student_id)).size;

  // ── Data fetch ─────────────────────────────────────────────────────────────

  async function fetchInternships(
    f: { search?: string; country_id?: number },
    p: number,
    yearId?: number | null,
  ) {
    const qs = new URLSearchParams();
    if (f.search) qs.set("search", f.search);
    const yid = yearId !== undefined ? yearId : selectedYearId;
    if (yid) qs.set("year_id", String(yid));
    if (f.country_id) qs.set("country_id", String(f.country_id));
    qs.set("page", String(p));
    qs.set("page_size", String(PAGE_SIZE));
    const data = await browserApi<PagedResponse<Internship>>(
      `/internships/?${qs.toString()}`,
      {},
    );
    setInternships(data.results);
    setTotalCount(data.count);
    setPage(p);
  }

  async function loadErrors(p: number, yearId?: number | null) {
    try {
      const yid = yearId !== undefined ? yearId : selectedYearId;
      const data = await getInternshipImportErrors({
        yearId: yid ?? undefined,
        page: p,
        pageSize: ERRORS_PAGE_SIZE,
      });
      setImportErrors(data.results);
      setImportErrorsTotalCount(data.count);
      setImportErrorsPage(p);
    } catch {
      // silently ignore
    }
  }

  // ── Year change ────────────────────────────────────────────────────────────

  function handleYearChange(yearId: number | null) {
    setSelectedYearId(yearId);
    setFilters({});
    void fetchInternships({}, 1, yearId);
    void loadErrors(1, yearId);
  }

  // ── Filter change ──────────────────────────────────────────────────────────

  function handleFilterChange(newFilters: typeof filters) {
    setFilters(newFilters);
    void fetchInternships(newFilters, 1);
  }

  function handlePageChange(p: number) {
    void fetchInternships(filters, p);
  }

  // ── CRUD ───────────────────────────────────────────────────────────────────

  async function submitInternship(payload: InternshipPayload) {
    if (!modal) return;
    if (modal.item) {
      const updated = await updateInternship(modal.item.id, payload);
      setInternships((items) => items.map((i) => (i.id === updated.id ? updated : i)));
    } else {
      const created = await createInternship(payload);
      setInternships((items) => [created, ...items]);
      setTotalCount((c) => c + 1);
    }
    setModal(null);
  }

  async function handleDelete(item: Internship) {
    if (
      !(await confirm(
        `Supprimer le stage de ${item.student_name} chez ${item.company_name} ?`,
      ))
    )
      return;
    setActionError("");
    try {
      await deleteInternship(item.id);
      await fetchInternships(filters, page);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Impossible de supprimer.");
    }
  }

  // ── Sync Eudonet ───────────────────────────────────────────────────────────

  async function handleSync() {
    setActionError("");
    setSyncInProgress(true);
    try {
      await syncInternshipsFromEudonet(selectedYearId ?? undefined);
      await delay(3000);
      await fetchInternships(filters, 1);
      await loadErrors(1);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "La synchronisation a échoué.");
    } finally {
      setSyncInProgress(false);
    }
  }

  // ── Import Excel ───────────────────────────────────────────────────────────

  async function handleExcelImport(file: File) {
    setActionError("");
    setImportInProgress(true);
    const yearId = selectedYearId;
    if (!yearId) {
      setActionError("Sélectionnez une année académique avant d'importer.");
      setImportInProgress(false);
      return;
    }
    try {
      await importInternshipsFromExcel(yearId, file);
      await delay(3000);
      await fetchInternships(filters, 1);
      await loadErrors(1);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "L'import Excel a échoué.");
    } finally {
      setImportInProgress(false);
    }
  }

  // ── Export ─────────────────────────────────────────────────────────────────

  async function handleExport() {
    setActionError("");
    setExportInProgress(true);
    try {
      await exportInternshipsExcel(selectedYearId ?? undefined, filters.country_id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Erreur export.");
    } finally {
      setExportInProgress(false);
    }
  }

  // ── Import error handlers ──────────────────────────────────────────────────

  async function handleRetryError(error: InternshipImportError) {
    await retryInternshipImport(error.id);
    await Promise.all([loadErrors(importErrorsPage), fetchInternships(filters, page)]);
  }

  async function handleIgnoreError(error: InternshipImportError) {
    await ignoreInternshipImport(error.id);
    await loadErrors(importErrorsPage);
  }

  async function handleForceError(
    error: InternshipImportError,
    payload: InternshipForcePayload,
  ) {
    await forceInternshipImport(error.id, payload);
    await Promise.all([loadErrors(importErrorsPage), fetchInternships(filters, page)]);
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {confirmDialog}

      {/* Sélecteur d'année */}
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

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <StatCard
          icon={Briefcase}
          label="Stages total"
          value={totalCount}
          helper=""
          tone="blue"
        />
        <StatCard
          icon={Globe}
          label="Pays représentés"
          value={uniqueCountries}
          helper=""
          tone="emerald"
        />
        <StatCard
          icon={Users}
          label="Étudiants"
          value={uniqueStudents}
          helper=""
          tone="amber"
        />
      </div>

      {/* Bannière sync/import désactivés */}
      {isInitializationPhase && (
        <div className="flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-800">
          Synchronisation, import et ajout de stages disponibles à partir de la phase <span className="font-semibold mx-1">Recommandation</span> (aucun étudiant importé en phase Initialisation).
        </div>
      )}

      {/* Bannière année clôturée */}
      {isReadOnly && (
        <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          <span className="font-semibold">Année clôturée</span> — consultation seule, imports et synchronisation désactivés.
        </div>
      )}

      {/* Toolbar */}
      <div className="flex flex-wrap gap-2">
        <Btn disabled={syncInProgress || !canManageInternships} onClick={handleSync}>
          <RefreshCw className={`h-4 w-4 ${syncInProgress ? "animate-spin" : ""}`} />
          {syncInProgress ? "Synchronisation..." : "Sync Eudonet"}
        </Btn>
        <FileBtn disabled={importInProgress || !canManageInternships} onFile={handleExcelImport}>
          {importInProgress ? (
            <Upload className="h-4 w-4 animate-bounce" />
          ) : (
            <FileSpreadsheet className="h-4 w-4" />
          )}
          {importInProgress ? "Import..." : "Importer Excel"}
        </FileBtn>
        <Btn disabled={exportInProgress} onClick={handleExport}>
          <FileDown className="h-4 w-4" />
          {exportInProgress ? "Export..." : "Exporter"}
        </Btn>
        <Btn
          disabled={!selectedYearId}
          onClick={() => selectedYearId && downloadInternshipTemplate(selectedYearId)}
        >
          <Download className="h-4 w-4" />
          Template
        </Btn>
        <Btn disabled={!canManageInternships} variant="primary" onClick={() => setModal({})}>
          <Plus className="h-4 w-4" />
          Ajouter
        </Btn>
      </div>

      <ErrorBanner message={actionError} onDismiss={() => setActionError("")} />

      {/* Table */}
      <InternshipsTable
        internships={internships}
        totalCount={totalCount}
        page={page}
        pageSize={PAGE_SIZE}
        countries={countries}
        readOnly={isReadOnly}
        onPageChange={handlePageChange}
        onEdit={(item) => setModal({ item })}
        onDelete={handleDelete}
        onFilterChange={handleFilterChange}
      />

      {/* Erreurs d'import — section dépliable */}
      {importErrors.length > 0 || importErrorsTotalCount > 0 ? (
        <div className="rounded-lg border border-amber-200">
          <button
            type="button"
            className="w-full flex items-center gap-3 px-4 py-3 text-left"
            onClick={() => setErrorsOpen((v) => !v)}
          >
            {errorsOpen ? (
              <ChevronDown className="h-4 w-4 text-amber-600" />
            ) : (
              <ChevronRight className="h-4 w-4 text-amber-600" />
            )}
            <span className="text-sm font-semibold text-amber-900">
              Erreurs d&apos;import ({importErrorsTotalCount})
            </span>
          </button>
          {errorsOpen && (
            <div className="border-t border-amber-100 p-4">
              <InternshipImportErrorsPanel
                errors={importErrors}
                isBusy={syncInProgress || importInProgress || isReadOnly}
                onRetry={handleRetryError}
                onIgnore={handleIgnoreError}
                onForce={handleForceError}
                countries={countries}
                selectedYearId={selectedYearId ?? undefined}
                totalCount={importErrorsTotalCount}
                page={importErrorsPage}
                pageSize={ERRORS_PAGE_SIZE}
                onPageChange={loadErrors}
              />
            </div>
          )}
        </div>
      ) : null}

      {/* Modal formulaire */}
      {modal !== null ? (
        <Modal
          description={
            modal.item ? "Modifier les informations du stage." : "Créer un nouveau stage."
          }
          onClose={() => setModal(null)}
          title={modal.item ? "Modifier le stage" : "Nouveau stage"}
        >
          <InternshipForm
            academicYears={academicYears}
            countries={countries}
            item={modal.item}
            onCancel={() => setModal(null)}
            onSubmit={submitInternship}
          />
        </Modal>
      ) : null}
    </div>
  );
}
