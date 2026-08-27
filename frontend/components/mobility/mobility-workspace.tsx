"use client";

import { useMemo, useRef, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronRight, Download, FileDown, FileSpreadsheet, FileText, Gauge, History, Landmark, Layers, Plus, RefreshCw, Upload } from "lucide-react";

import { AgreementForm } from "@/components/mobility/agreement-form";
import { MobilityCategoryForm } from "@/components/mobility/agreement-framework-form";
import { MobilityCategorysTable } from "@/components/mobility/agreement-frameworks-table";
import { AgreementsHistoryTable } from "@/components/mobility/agreements-history-table";
import { AgreementsTable } from "@/components/mobility/agreements-table";
import { MobilityImportErrorsPanel } from "@/components/mobility/mobility-import-errors-panel";
import { MobilitySection } from "@/components/mobility/mobility-section";
import { ErrorBanner } from "@/components/ui/alert";
import { Btn, FileBtn } from "@/components/ui/btn";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { Modal } from "@/components/ui/modal";
import { PageTabBar } from "@/components/ui/page-tab-bar";
import { SearchInput } from "@/components/ui/search-input";
import { StatCard } from "@/components/ui/stat-card";
import {
  adjustAgreementYearInp,
  createAgreement,
  createMobilityCategory,
  deleteAgreement,
  deleteMobilityCategory,
  downloadExcelTemplate,
  exportAgreementsExcel,
  fetchAgreementYearDepartments,
  fetchAgreementYearsList,
  fetchAgreements,
  fetchMobilityCategories,
  fetchMobilityImportErrors,
  forceMobilityImport,
  getMoveonMobilityImportErrors,
  ignoreMobilityImport,
  importAgreementsFromExcel,
  restoreAgreement,
  retryMobilityImport,
  syncMobilityFromMoveon,
  syncMobilityCategoriesFromMoveon,
  toggleAgreementYearActive,
  updateAgreement,
  updateAgreementYear,
  updateAgreementYearDepartment,
  updateMobilityCategory,
  validateAgreementYear,
  type MobilityImportRetryPayload,
  type MobilityCategoryPayload,
} from "@/lib/api/mobility-mutations";

const MOBILITY_ERRORS_PAGE_SIZE = 25;
import type {
  AcademicYear,
  Agreement,
  AgreementYear,
  AgreementYearDepartment,
  Country,
  Department,
  Level,
  MobilityCategory,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

const PAGE_LOAD_MS = Date.now();

type ModalState =
  | { kind: "agreement"; item?: Agreement }
  | { kind: "framework"; item?: MobilityCategory };

export function MobilityWorkspace({
  academicYears,
  mobilityCategories: initialMobilityCategories,
  countries,
  currentYear,
  initialAgreementYears,
  initialAgreements,
  initialAllAgreements,
  initialAgreementYearDepartments,
  initialImportErrors,
  initialImportErrorsTotalCount,
  initialExpiringAgreements,
  departments,
  mobilityLevels,
  universities,
}: Readonly<{
  academicYears: AcademicYear[];
  mobilityCategories: MobilityCategory[];
  countries: Country[];
  currentYear: AcademicYear | null;
  initialAgreementYears: AgreementYear[];
  initialAgreements: Agreement[];
  initialAllAgreements: Agreement[];
  initialAgreementYearDepartments: AgreementYearDepartment[];
  initialImportErrors: RawImport[];
  initialImportErrorsTotalCount: number;
  initialExpiringAgreements: Agreement[];
  departments: Department[];
  mobilityLevels: Level[];
  universities: PartnerUniversity[];
}>) {
  const [agreements, setAgreements] = useState(initialAgreements);
  const [allAgreements, setAllAgreements] = useState(initialAllAgreements);
  const [showHistory, setShowHistory] = useState(false);
  const [expiringAgreements] = useState(initialExpiringAgreements);
  const [mobilityCategories, setMobilityCategories] = useState(initialMobilityCategories);
  const [agreementYears, setAgreementYears] = useState(initialAgreementYears);
  const [agreementYearDepartments, setAgreementYearDepartments] = useState(initialAgreementYearDepartments);
  const [importErrors, setImportErrors] = useState(initialImportErrors);
  const [importErrorsTotalCount, setImportErrorsTotalCount] = useState(initialImportErrorsTotalCount);
  const [importErrorsPage, setImportErrorsPage] = useState(1);
  const [excelImportInProgress, setExcelImportInProgress] = useState(false);
  const [exportInProgress, setExportInProgress] = useState(false);
  const [modal, setModal] = useState<ModalState | null>(null);
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [query, setQuery] = useState("");
  const [syncError, setSyncError] = useState("");
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [categorySyncInProgress, setCategorySyncInProgress] = useState(false);
  const latestYear = [...academicYears].sort((a, b) => b.start_date.localeCompare(a.start_date))[0];
  const [yearFilter, setYearFilter] = useState<string>(currentYear?.label ?? latestYear?.label ?? "");

  const selectedYearStatus = useMemo(
    () => academicYears.find((y) => y.label === yearFilter)?.status,
    [academicYears, yearFilter],
  );
  const isYearClosed = selectedYearStatus === "closed";
  const isYearLocked = selectedYearStatus !== undefined && selectedYearStatus !== "initialization";

  const [countryFilter, setCountryFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [universityFilter, setUniversityFilter] = useState<string>("all");
  const [activityFilter, setActivityFilter] = useState<string>("all");

  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Séparer les erreurs par type
  const agreementErrors = useMemo(
    () => importErrors.filter((e) => e.entity === "agreement"),
    [importErrors],
  );
  const categoryErrors = useMemo(
    () => importErrors.filter((e) => e.entity === "agreement_category"),
    [importErrors],
  );

  async function doFetchAgreements(search?: string, countryId?: number, activity?: string) {
    const isActive =
      activity === "active" ? true : activity === "inactive" ? false : undefined;
    const page = await fetchAgreements({
      search: search || undefined,
      country_id: countryId,
      is_active: isActive,
      page_size: 200,
    });
    setAgreements(page.results);
  }

  function handleQueryChange(value: string) {
    setQuery(value);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      void doFetchAgreements(value, countryFilter !== "all" ? Number(countryFilter) : undefined, activityFilter);
    }, 350);
  }

  function handleCountryFilterChange(value: string) {
    setCountryFilter(value);
    setUniversityFilter("all");
    void doFetchAgreements(query, value !== "all" ? Number(value) : undefined, activityFilter);
  }

  function handleActivityFilterChange(value: string) {
    setActivityFilter(value);
    void doFetchAgreements(query, countryFilter !== "all" ? Number(countryFilter) : undefined, value);
  }

  // Universités filtrées par pays (pour le select université)
  const filteredUniversities = useMemo(() => {
    const byCountry = countryFilter === "all"
      ? universities
      : universities.filter((u) => String(u.country_id) === countryFilter);
    return [...byCountry].sort((a, b) => (a.short_name || a.name).localeCompare(b.short_name || b.name));
  }, [universities, countryFilter]);

  // Client-side secondary filters (category, university, activity, year)
  const agreementsForDisplay = useMemo(() => {
    let base = agreements;
    if (categoryFilter !== "all") {
      base = base.filter((a) => a.category_id === Number(categoryFilter));
    }
    if (universityFilter !== "all") {
      base = base.filter((a) => a.partner_university_id === Number(universityFilter));
    }
    if (yearFilter) {
      const selectedYear = academicYears.find((y) => y.label === yearFilter);
      if (selectedYear?.status === "closed") {
        const idsWithYear = new Set(
          agreementYears
            .filter((yi) => yi.academic_year_label === yearFilter)
            .map((yi) => yi.agreement_id),
        );
        base = base.filter((a) => idsWithYear.has(a.id));
      }
    }
    return base;
  }, [academicYears, agreementYears, agreements, categoryFilter, universityFilter, yearFilter]);

  // "" (Toutes les années) n'a pas de snapshot "actif" unique et cohérent :
  // dans ce cas on retombe sur l'année en cours plutôt que de sommer toutes
  // les années (ce qui compterait plusieurs fois le même accord).
  const statsYearLabel = yearFilter || currentYear?.label;

  const activeYearInstances = useMemo(() => {
    if (!statsYearLabel) return [];
    // Un accord supprimé ne doit plus compter comme actif, même si son
    // instance (validée avant suppression, donc jamais retouchée) l'indique
    // encore — allAgreements porte deleted_at, agreementYears non.
    const deletedAgreementIds = new Set(
      allAgreements.filter((a) => a.deleted_at !== null).map((a) => a.id),
    );
    return agreementYears.filter(
      (yi) =>
        yi.academic_year_label === statsYearLabel &&
        yi.is_active &&
        !deletedAgreementIds.has(yi.agreement_id),
    );
  }, [agreementYears, allAgreements, statsYearLabel]);

  const statTotalN7 = useMemo(
    () => activeYearInstances.reduce((s, yi) => s + yi.n7_places, 0),
    [activeYearInstances],
  );

  // ── Agreements ─────────────────────────────────────────────────────────────

  async function submitAgreement(payload: Parameters<typeof createAgreement>[0]) {
    if (modal?.kind !== "agreement") return;
    if (modal.item) {
      const updated = await updateAgreement(modal.item.id, payload);
      setAgreements((items) => items.map((a) => (a.id === updated.id ? updated : a)));
      setAllAgreements((items) => items.map((a) => (a.id === updated.id ? updated : a)));
    } else {
      const created = await createAgreement(payload);
      setAgreements((items) => [...items, created]);
      setAllAgreements((items) => [...items, created]);
    }
    // Le backend crée/redistribue l'instance annuelle et ses quotas département
    // à la création/modification d'un accord : on rafraîchit ces deux listes
    // pour que la nouvelle instance soit visible sans recharger la page.
    const [newAgreementYears, newDeptQuotas] = await Promise.all([
      fetchAgreementYearsList(),
      fetchAgreementYearDepartments(),
    ]);
    setAgreementYears(newAgreementYears);
    setAgreementYearDepartments(newDeptQuotas);
    setModal(null);
  }

  async function removeAgreement(agreement: Agreement) {
    if (
      !(await confirm(
        `Supprimer l'accord "${agreement.name}" ? S'il a de l'historique (années passées ou validées), ` +
          `il sera conservé — consultable dans l'historique — mais retiré à partir de maintenant.`,
      ))
    )
      return;
    setSyncError("");
    try {
      const result = await deleteAgreement(agreement.id);
      if (result) {
        // Suppression douce : l'accord garde son historique mais n'est plus
        // actif à partir de maintenant — il disparaît de la vue "année en cours".
        setAgreements((items) => items.filter((a) => a.id !== agreement.id));
        setAllAgreements((items) => items.map((a) => (a.id === result.id ? result : a)));
      } else {
        setAgreements((items) => items.filter((a) => a.id !== agreement.id));
        setAllAgreements((items) => items.filter((a) => a.id !== agreement.id));
      }
      const [newAgreementYears, newDeptQuotas] = await Promise.all([
        fetchAgreementYearsList(),
        fetchAgreementYearDepartments(),
      ]);
      setAgreementYears(newAgreementYears);
      setAgreementYearDepartments(newDeptQuotas);
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de supprimer l'accord.");
    }
  }

  async function handleRestoreAgreement(agreement: Agreement) {
    setSyncError("");
    try {
      const restored = await restoreAgreement(agreement.id);
      setAllAgreements((items) => items.map((a) => (a.id === restored.id ? restored : a)));
      setAgreements((items) =>
        items.some((a) => a.id === restored.id) ? items : [...items, restored],
      );
      const [newAgreementYears, newDeptQuotas] = await Promise.all([
        fetchAgreementYearsList(),
        fetchAgreementYearDepartments(),
      ]);
      setAgreementYears(newAgreementYears);
      setAgreementYearDepartments(newDeptQuotas);
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de restaurer l'accord.");
    }
  }


  // ── AgreementYear ──────────────────────────────────────────────────────────

  async function handleToggleYearActive(yi: AgreementYear) {
    setSyncError("");
    try {
      const updated = await toggleAgreementYearActive(yi.id);
      setAgreementYears((items) => items.map((y) => (y.id === updated.id ? updated : y)));
      // Si vient d'être activé, le backend a pu créer des quotas dept → on rafraîchit
      if (updated.is_active) {
        const depts = await fetchAgreementYearDepartments();
        setAgreementYearDepartments(depts);
      }
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de modifier le statut.");
    }
  }

  async function handleEditYear(yi: AgreementYear, n7Places: number) {
    setSyncError("");
    const updated = await updateAgreementYear(yi.id, {
      agreement_id: yi.agreement_id,
      academic_year_id: yi.academic_year_id,
      is_active: yi.is_active,
      inp_total_places: yi.inp_total_places,
      n7_places: n7Places,
      duration_weeks: yi.duration_weeks,
    });
    setAgreementYears((items) => items.map((y) => (y.id === updated.id ? updated : y)));
    // Rafraîchir les quotas département recalculés par Hamilton
    const depts = await fetchAgreementYearDepartments();
    setAgreementYearDepartments(depts);
  }

  async function handleEditYearInp(yi: AgreementYear, inpPlaces: number) {
    setSyncError("");
    const updated = await adjustAgreementYearInp(yi.id, inpPlaces);
    setAgreementYears((items) => items.map((y) => (y.id === updated.id ? updated : y)));
    // Rafraîchir les quotas département recalculés par Hamilton
    const depts = await fetchAgreementYearDepartments();
    setAgreementYearDepartments(depts);
  }

  async function handleEditYearDuration(yi: AgreementYear, durationMonths: number | null) {
    setSyncError("");
    const updated = await updateAgreementYear(yi.id, {
      agreement_id: yi.agreement_id,
      academic_year_id: yi.academic_year_id,
      is_active: yi.is_active,
      inp_total_places: yi.inp_total_places,
      n7_places: yi.n7_places,
      duration_weeks: durationMonths,
    });
    setAgreementYears((items) => items.map((y) => (y.id === updated.id ? updated : y)));
  }

  async function handleValidateYear(yi: AgreementYear) {
    setSyncError("");
    const validated = await validateAgreementYear(yi.id);
    setAgreementYears((items) => items.map((y) => (y.id === validated.id ? validated : y)));
  }

  // ── DepartmentQuotas — édition inline ────────────────────────────────────

  async function handleSaveDeptQuota(dq: AgreementYearDepartment, places: number) {
    setSyncError("");
    const updated = await updateAgreementYearDepartment(dq.id, {
      agreement_year_id: dq.agreement_year_id,
      department_id: dq.department_id,
      estimated_places: places,
    });
    setAgreementYearDepartments((items) =>
      items.map((d) => (d.id === updated.id ? updated : d)),
    );
  }

  // ── Categories ─────────────────────────────────────────────────────────────

  async function submitFramework(payload: MobilityCategoryPayload) {
    if (modal?.kind !== "framework") return;
    if (modal.item) {
      const updated = await updateMobilityCategory(modal.item.id, payload);
      setMobilityCategories((items) => items.map((c) => (c.id === updated.id ? updated : c)));
    } else {
      const created = await createMobilityCategory(payload);
      setMobilityCategories((items) => [...items, created]);
    }
    setModal(null);
  }

  async function removeFramework(framework: MobilityCategory) {
    if (!(await confirm(`Supprimer le cadre "${framework.name}" ?`))) return;
    setSyncError("");
    try {
      await deleteMobilityCategory(framework.id);
      setMobilityCategories((items) => items.filter((c) => c.id !== framework.id));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de supprimer le cadre.");
    }
  }

  async function handleCategorySync() {
    setSyncError("");
    setCategorySyncInProgress(true);
    try {
      await syncMobilityCategoriesFromMoveon();
      await delay(3000);
      await refreshMobilityData();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "La synchronisation des cadres a échoué.");
    } finally {
      setCategorySyncInProgress(false);
    }
  }

  // ── Sync MoveON (accords) ──────────────────────────────────────────────────

  async function handleSync() {
    setSyncError("");
    setSyncInProgress(true);
    try {
      await syncMobilityFromMoveon();
      await delay(3000);
      await refreshMobilityData();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "La synchronisation a échoué.");
    } finally {
      setSyncInProgress(false);
    }
  }

  async function handleExport() {
    setSyncError("");
    setExportInProgress(true);
    try {
      await exportAgreementsExcel({
        yearLabel: yearFilter || undefined,
        country: countryFilter !== "all" ? countryFilter : undefined,
        category: categoryFilter !== "all" ? categoryFilter : undefined,
        activity: activityFilter !== "all" ? activityFilter : undefined,
      });
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Erreur export.");
    } finally {
      setExportInProgress(false);
    }
  }

  async function handleTemplateDownload() {
    setSyncError("");
    try {
      await downloadExcelTemplate();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Erreur téléchargement du modèle.");
    }
  }

  // ── Import Excel ───────────────────────────────────────────────────────────

  async function handleExcelImport(file: File) {
    setSyncError("");
    setExcelImportInProgress(true);
    try {
      await importAgreementsFromExcel(file);
      await delay(3000);
      await refreshMobilityData();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "L'import Excel a échoué.");
    } finally {
      setExcelImportInProgress(false);
    }
  }

  // ── Import errors ──────────────────────────────────────────────────────────

  async function loadMobilityErrors(page: number) {
    try {
      const errs = await getMoveonMobilityImportErrors({ page, page_size: MOBILITY_ERRORS_PAGE_SIZE });
      setImportErrors(errs.results);
      setImportErrorsTotalCount(errs.count);
      setImportErrorsPage(page);
    } catch {
      // silently ignore
    }
  }

  async function handleIgnoreImportError(error: RawImport) {
    await ignoreMobilityImport(error.id);
    await loadMobilityErrors(importErrorsPage);
  }

  async function handleForceImportError(error: RawImport) {
    await forceMobilityImport(error.id);
    await Promise.all([loadMobilityErrors(importErrorsPage), refreshMobilityData()]);
  }

  async function handleRetryImportError(error: RawImport, payload: MobilityImportRetryPayload) {
    try {
      await retryMobilityImport(error.id, payload);
      await Promise.all([loadMobilityErrors(importErrorsPage), refreshMobilityData()]);
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de relancer l'import.");
    }
  }

  async function refreshMobilityData() {
    const [agreementsPage, allAgreementsPage, agreementYears, agreementYearDepts, mobilityCategories, importErrorsPage] =
      await Promise.all([
        fetchAgreements({
          search: query || undefined,
          country_id: countryFilter !== "all" ? Number(countryFilter) : undefined,
          is_active: activityFilter === "active" ? true : activityFilter === "inactive" ? false : undefined,
          page_size: 200,
        }),
        fetchAgreements({ include_deleted: true, page_size: 200 }),
        fetchAgreementYearsList(),
        fetchAgreementYearDepartments(),
        fetchMobilityCategories(),
        fetchMobilityImportErrors(1, 25),
      ]);
    setAgreements(agreementsPage.results);
    setAllAgreements(allAgreementsPage.results);
    setAgreementYears(agreementYears);
    setAgreementYearDepartments(agreementYearDepts);
    setMobilityCategories(mobilityCategories);
    setImportErrors(importErrorsPage.results);
    setImportErrorsTotalCount(importErrorsPage.count);
    setImportErrorsPage(1);
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {confirmDialog}

      {/* Sélecteur d'année */}
      <div className="flex items-end gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Année universitaire</span>
          <select
            className="mt-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
          >
            <option value="">Toutes les années</option>
            {[...academicYears]
              .sort((a, b) => b.start_date.localeCompare(a.start_date))
              .map((y) => (
                <option key={y.id} value={y.label}>
                  {y.label}{y.status === "closed" ? " (clôturée)" : ""}</option>
              ))}
          </select>
        </label>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard icon={Landmark} label="Accords total" value={agreements.length} helper="" tone="blue" />
        <StatCard
          icon={Layers}
          label={statsYearLabel ? `Actifs en ${statsYearLabel}` : "Actifs cette année"}
          value={activeYearInstances.length}
          helper=""
          tone="emerald"
        />
        <StatCard
          icon={Gauge}
          label={statsYearLabel ? `Places N7 (${statsYearLabel})` : "Places N7"}
          value={statTotalN7}
          helper=""
          tone="blue"
        />
        <StatCard icon={FileText} label="Cadres" value={mobilityCategories.length} helper="" tone="amber" />
      </div>

      {/* Accords expirant bientôt */}
      <ExpiringAgreementsBanner agreements={expiringAgreements} universities={universities} nowMs={PAGE_LOAD_MS} />

      {/* Section tabs */}
      <PageTabBar
        tabs={[
          { label: "Accords", value: agreements.length, href: "#accords" },
          { label: "Cadres", value: mobilityCategories.length, href: "#cadres" },
        ]}
      />

      <ErrorBanner message={syncError} />

      {isYearClosed && (
        <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          <span className="font-semibold">Année clôturée</span> — consultation seule, toutes les modifications sont désactivées.
        </div>
      )}
      {isYearLocked && !isYearClosed && (
        <div className="flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-800">
          <span className="font-semibold">Campagne en cours</span> — les quotas et accords sont verrouillés. Export disponible en lecture seule.
        </div>
      )}

      {/* ── Section Accords ─────────────────────────────────────────────── */}
      <MobilitySection
        description={
          showHistory
            ? "Historique complet de tous les accords, toutes années confondues (y compris supprimés)."
            : "Accords de mobilité, quotas annuels et répartition par département."
        }
        id="accords"
        title="Accords de mobilité"
        toolbar={
          <div className="flex flex-wrap gap-2">
            <Btn onClick={() => setShowHistory((v) => !v)}>
              <History className="h-4 w-4" />
              {showHistory ? "Vue année en cours" : "Historique complet"}
            </Btn>
            <Btn disabled={syncInProgress || isYearClosed || isYearLocked} onClick={handleSync}>
              <RefreshCw className={`h-4 w-4 ${syncInProgress ? "animate-spin" : ""}`} />
              {syncInProgress ? "Synchronisation..." : "Sync MoveON"}
            </Btn>
            <Btn disabled={isYearClosed || isYearLocked} onClick={() => { void handleTemplateDownload(); }}>
              <Download className="h-4 w-4" />
              Template
            </Btn>
            <FileBtn disabled={excelImportInProgress || isYearClosed || isYearLocked} onFile={handleExcelImport}>
              {excelImportInProgress ? <Upload className="h-4 w-4 animate-bounce" /> : <FileSpreadsheet className="h-4 w-4" />}
              {excelImportInProgress ? "Import..." : "Importer Excel"}
            </FileBtn>
            <Btn disabled={exportInProgress} onClick={handleExport}>
              <FileDown className="h-4 w-4" />
              {exportInProgress ? "Export..." : "Exporter"}
            </Btn>
            <Btn variant="primary" disabled={isYearClosed || isYearLocked} onClick={() => setModal({ kind: "agreement" })}>
              <Plus className="h-4 w-4" /> Nouvel accord
            </Btn>
          </div>
        }
      >
        {showHistory ? (
          <AgreementsHistoryTable
            academicYears={academicYears}
            agreements={allAgreements}
            agreementYears={agreementYears}
            agreementYearDepartments={agreementYearDepartments}
            categories={mobilityCategories}
            departments={departments}
            levels={mobilityLevels}
            universities={universities}
            onEditYear={handleEditYear}
            onEditYearDuration={handleEditYearDuration}
            onEditYearInp={handleEditYearInp}
            onRestore={handleRestoreAgreement}
            onSaveDeptQuota={handleSaveDeptQuota}
            onToggleYearActive={handleToggleYearActive}
            onValidateYear={handleValidateYear}
          />
        ) : (
          <>
            {/* Filtres — une seule ligne */}
            <div className="mb-4 flex items-center gap-2">
              <SearchInput onChange={handleQueryChange} placeholder="Rechercher..." value={query} />
              <select
                className="w-32 rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700"
                onChange={(e) => handleCountryFilterChange(e.target.value)}
                value={countryFilter}
              >
                <option value="all">Tous pays</option>
                {[...countries]
                  .sort((a, b) => a.name_fr.localeCompare(b.name_fr))
                  .map((c) => (
                    <option key={c.id} value={c.id}>{c.name_fr}</option>
                  ))}
              </select>
              <select
                className="w-36 rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700"
                onChange={(e) => setUniversityFilter(e.target.value)}
                value={universityFilter}
              >
                <option value="all">Toutes universités</option>
                {filteredUniversities.map((u) => (
                  <option key={u.id} value={u.id}>{u.short_name || u.name}</option>
                ))}
              </select>
              <select
                className="w-32 rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700"
                onChange={(e) => setCategoryFilter(e.target.value)}
                value={categoryFilter}
              >
                <option value="all">Tous cadres</option>
                {mobilityCategories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              <select
                className="w-24 rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700"
                onChange={(e) => handleActivityFilterChange(e.target.value)}
                value={activityFilter}
              >
                <option value="all">Tous</option>
                <option value="active">Actifs</option>
                <option value="inactive">Inactifs</option>
              </select>
            </div>

            <AgreementsTable
              academicYears={academicYears}
              agreements={agreementsForDisplay}
              agreementYears={agreementYears}
              agreementYearDepartments={agreementYearDepartments}
              categories={mobilityCategories}
              departments={departments}
              levels={mobilityLevels}
              universities={universities}
              yearFilter={yearFilter}
              isYearClosed={isYearClosed}
              isYearLocked={isYearLocked}
              onToggleYearActive={handleToggleYearActive}
              onEditYear={handleEditYear}
              onEditYearInp={handleEditYearInp}
              onEditYearDuration={handleEditYearDuration}
              onValidateYear={handleValidateYear}
              onSaveDeptQuota={handleSaveDeptQuota}
              onRestore={handleRestoreAgreement}
              onEdit={(agreement) => setModal({ kind: "agreement", item: agreement })}
              onDelete={removeAgreement}
            />
          </>
        )}
      </MobilitySection>

      {/* Erreurs accords */}
      {agreementErrors.length > 0 && (
        <MobilityImportErrorsPanel
          errors={agreementErrors}
          isBusy={syncInProgress || excelImportInProgress || isYearLocked || isYearClosed}
          onIgnore={handleIgnoreImportError}
          onRetry={handleRetryImportError}
          onForce={handleForceImportError}
          universities={universities}
          totalCount={importErrorsTotalCount}
          page={importErrorsPage}
          pageSize={MOBILITY_ERRORS_PAGE_SIZE}
          onPageChange={loadMobilityErrors}
        />
      )}

      {/* ── Section Cadres ──────────────────────────────────────────────── */}
      <MobilitySection
        description="Cadres de mobilité (Erasmus, bilatéral, etc.) synchronisés depuis MoveON."
        id="cadres"
        title="Cadres de mobilité"
        toolbar={
          <div className="flex flex-wrap gap-2">
            <Btn disabled={categorySyncInProgress || isYearClosed || isYearLocked} onClick={handleCategorySync}>
              <RefreshCw className={`h-4 w-4 ${categorySyncInProgress ? "animate-spin" : ""}`} />
              {categorySyncInProgress ? "Synchronisation..." : "Sync MoveON"}
            </Btn>
            <Btn variant="primary" disabled={isYearClosed || isYearLocked} onClick={() => setModal({ kind: "framework" })}>
              <Plus className="h-4 w-4" /> Nouveau cadre
            </Btn>
          </div>
        }
      >
        <MobilityCategorysTable
          agreementFrameworks={mobilityCategories}
          isYearClosed={isYearClosed || isYearLocked}
          onDelete={removeFramework}
          onEdit={(c) => setModal({ kind: "framework", item: c })}
        />
      </MobilitySection>

      {/* Erreurs cadres */}
      {categoryErrors.length > 0 && (
        <MobilityImportErrorsPanel
          errors={categoryErrors}
          isBusy={categorySyncInProgress || isYearLocked || isYearClosed}
          onIgnore={handleIgnoreImportError}
          onRetry={handleRetryImportError}
          onForce={handleForceImportError}
          universities={universities}
          totalCount={importErrorsTotalCount}
          page={importErrorsPage}
          pageSize={MOBILITY_ERRORS_PAGE_SIZE}
          onPageChange={loadMobilityErrors}
        />
      )}

      {/* ── Modals ──────────────────────────────────────────────────────── */}
      {modal?.kind === "agreement" ? (
        <Modal
          description={modal.item ? "Modifier l'accord." : "Créer un nouvel accord de mobilité."}
          onClose={() => setModal(null)}
          title={modal.item ? "Modifier l'accord" : "Nouvel accord"}
        >
          <AgreementForm
            departments={departments}
            frameworks={mobilityCategories}
            item={modal.item}
            mobilityLevels={mobilityLevels}
            onCancel={() => setModal(null)}
            onSubmit={submitAgreement}
            universities={universities}
          />
        </Modal>
      ) : null}


      {modal?.kind === "framework" ? (
        <Modal
          description={modal.item ? "Modifier ce cadre." : "Créer un nouveau cadre de mobilité."}
          onClose={() => setModal(null)}
          title={modal.item ? "Modifier le cadre" : "Nouveau cadre"}
        >
          <MobilityCategoryForm
            item={modal.item}
            onCancel={() => setModal(null)}
            onSubmit={submitFramework}
          />
        </Modal>
      ) : null}
    </div>
  );
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ExpiringAgreementsBanner({
  agreements,
  universities,
  nowMs,
}: Readonly<{
  agreements: Agreement[];
  universities: PartnerUniversity[];
  nowMs: number;
}>) {
  const [open, setOpen] = useState(false);

  if (agreements.length === 0) return null;

  const univById = new Map(universities.map((u) => [u.id, u]));

  function daysUntil(dateStr: string | null): number {
    if (!dateStr) return Infinity;
    return Math.ceil(
      (new Date(dateStr).getTime() - nowMs) / (1000 * 60 * 60 * 24),
    );
  }

  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50">
      <button
        type="button"
        className="w-full flex items-center gap-3 px-4 py-3 text-left"
        onClick={() => setOpen((v) => !v)}
      >
        <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" aria-hidden="true" />
        <span className="flex-1 text-sm font-semibold text-amber-900">
          {agreements.length} accord{agreements.length > 1 ? "s expirent" : " expire"} dans les 4 prochains mois
        </span>
        {open
          ? <ChevronDown className="h-4 w-4 text-amber-600" />
          : <ChevronRight className="h-4 w-4 text-amber-600" />}
      </button>

      {open && (
        <div className="border-t border-amber-200 px-4 pb-4">
          <table className="mt-3 w-full text-xs">
            <thead>
              <tr className="text-left text-[10px] font-semibold uppercase tracking-wide text-amber-700">
                <th className="pb-1 pr-4">Accord</th>
                <th className="pb-1 pr-4">Université partenaire</th>
                <th className="pb-1 pr-4">Expire le</th>
                <th className="pb-1">Délai</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-amber-100">
              {agreements.map((a) => {
                const days = daysUntil(a.valid_until);
                const urgency = days <= 30 ? "text-red-700 font-semibold" : "text-amber-800";
                const univ = univById.get(a.partner_university_id);
                return (
                  <tr key={a.id} className="hover:bg-amber-100/50">
                    <td className="py-1.5 pr-4 text-gray-900 font-medium max-w-56 truncate">{a.name}</td>
                    <td className="py-1.5 pr-4 text-gray-600 max-w-48 truncate">
                      {univ?.short_name ?? univ?.name ?? "—"}
                    </td>
                    <td className="py-1.5 pr-4 text-gray-700 whitespace-nowrap">
                      {a.valid_until
                        ? new Date(a.valid_until).toLocaleDateString("fr-FR")
                        : "—"}
                    </td>
                    <td className={`py-1.5 whitespace-nowrap ${urgency}`}>
                      {Number.isFinite(days) ? `${days} j` : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
