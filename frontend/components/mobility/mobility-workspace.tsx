"use client";

import { useMemo, useState } from "react";
import { Download, Plus, RefreshCw } from "lucide-react";

import { AgreementForm } from "@/components/mobility/agreement-form";
import { MobilityCategoryForm } from "@/components/mobility/agreement-framework-form";
import { MobilityCategorysTable } from "@/components/mobility/agreement-frameworks-table";
import { AgreementsTable } from "@/components/mobility/agreements-table";
import { MobilityImportErrorsPanel } from "@/components/mobility/mobility-import-errors-panel";
import { MobilitySection } from "@/components/mobility/mobility-section";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { Modal } from "@/components/ui/modal";
import { PageTabBar } from "@/components/ui/page-tab-bar";
import { SearchInput } from "@/components/ui/search-input";
import { StatCard } from "@/components/ui/stat-card";
import { FileText, Gauge, Landmark, Layers } from "lucide-react";
import {
  createAgreement,
  createMobilityCategory,
  deleteMobilityCategory,
  downloadExcelTemplate,
  ignoreMobilityImport,
  importAgreementsFromExcel,
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
  initialAgreementYearDepartments,
  initialImportErrors,
  departments,
  mobilityLevels,
  universities,
}: {
  academicYears: AcademicYear[];
  mobilityCategories: MobilityCategory[];
  countries: Country[];
  currentYear: AcademicYear | null;
  initialAgreementYears: AgreementYear[];
  initialAgreements: Agreement[];
  initialAgreementYearDepartments: AgreementYearDepartment[];
  initialImportErrors: RawImport[];
  departments: Department[];
  mobilityLevels: Level[];
  universities: PartnerUniversity[];
}) {
  const [agreements, setAgreements] = useState(initialAgreements);
  const [mobilityCategories, setMobilityCategories] = useState(initialMobilityCategories);
  const [agreementYears, setAgreementYears] = useState(initialAgreementYears);
  const [agreementYearDepartments, setAgreementYearDepartments] = useState(initialAgreementYearDepartments);
  const [importErrors, setImportErrors] = useState(initialImportErrors);
  const [excelImportInProgress, setExcelImportInProgress] = useState(false);
  const [modal, setModal] = useState<ModalState | null>(null);
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [query, setQuery] = useState("");
  const [syncError, setSyncError] = useState("");
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [categorySyncInProgress, setCategorySyncInProgress] = useState(false);
  const [yearFilter, setYearFilter] = useState<string>(currentYear?.label ?? "");
  const [countryFilter, setCountryFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [universityFilter, setUniversityFilter] = useState<string>("all");
  const [activityFilter, setActivityFilter] = useState<string>("all");

  const universitiesById = useMemo(
    () => new Map(universities.map((u) => [u.id, u])),
    [universities],
  );

  // Séparer les erreurs par type
  const agreementErrors = useMemo(
    () => importErrors.filter((e) => e.entity === "agreement"),
    [importErrors],
  );
  const categoryErrors = useMemo(
    () => importErrors.filter((e) => e.entity === "agreement_category"),
    [importErrors],
  );

  const yearInstanceMap = useMemo(() => {
    const map = new Map<number, AgreementYear>();
    for (const yi of agreementYears) {
      if (!yearFilter || yi.academic_year_label === yearFilter) {
        map.set(yi.agreement_id, yi);
      }
    }
    return map;
  }, [agreementYears, yearFilter]);

  const normalizedQuery = query.trim().toLowerCase();
  const filteredAgreements = useMemo(() => {
    if (!normalizedQuery) return agreements;
    return agreements.filter((a) => {
      const u = universitiesById.get(a.partner_university_id);
      return [a.name, a.reference, a.moveon_id, u?.name, u?.city]
        .join(" ").toLowerCase().includes(normalizedQuery);
    });
  }, [agreements, normalizedQuery, universitiesById]);

  // Universités filtrées par pays (pour le select université)
  const filteredUniversities = useMemo(() => {
    const byCountry = countryFilter === "all"
      ? universities
      : universities.filter((u) => String(u.country_id) === countryFilter);
    return [...byCountry].sort((a, b) => (a.short_name || a.name).localeCompare(b.short_name || b.name));
  }, [universities, countryFilter]);

  const agreementsForDisplay = useMemo(() => {
    let base = filteredAgreements;
    if (countryFilter !== "all") {
      const uIds = new Set(
        universities.filter((u) => String(u.country_id) === countryFilter).map((u) => u.id),
      );
      base = base.filter((a) => uIds.has(a.partner_university_id));
    }
    if (categoryFilter !== "all") {
      base = base.filter((a) => a.category_id === Number(categoryFilter));
    }
    if (universityFilter !== "all") {
      base = base.filter((a) => a.partner_university_id === Number(universityFilter));
    }

    if (activityFilter === "active") {
      base = base.filter((a) => yearInstanceMap.get(a.id)?.is_active === true);
    } else if (activityFilter === "inactive") {
      base = base.filter((a) => {
        const yi = yearInstanceMap.get(a.id);
        return !yi || !yi.is_active;
      });
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
  }, [academicYears, activityFilter, agreementYears, filteredAgreements, categoryFilter, countryFilter, universityFilter, universities, yearFilter, yearInstanceMap]);

  const activeYearInstances = useMemo(() => {
    if (!currentYear) return [];
    return agreementYears.filter(
      (yi) => yi.academic_year_label === currentYear.label && yi.is_active,
    );
  }, [agreementYears, currentYear]);

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
    } else {
      const created = await createAgreement(payload);
      setAgreements((items) => [...items, created]);
    }
    setModal(null);
  }


  // ── AgreementYear ──────────────────────────────────────────────────────────

  async function handleToggleYearActive(yi: AgreementYear) {
    setSyncError("");
    try {
      const updated = await toggleAgreementYearActive(yi.id);
      setAgreementYears((items) => items.map((y) => (y.id === updated.id ? updated : y)));
      // Si vient d'être activé, le backend a pu créer des quotas dept → on rafraîchit
      if (updated.is_active) {
        const { getMobilityData } = await import("@/lib/api/mobility");
        const fresh = await getMobilityData();
        setAgreementYearDepartments(fresh.agreementYearDepartments);
      }
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de modifier le statut.");
    }
  }

  async function handleEditYear(yi: AgreementYear, n7Places: number) {
    setSyncError("");
    try {
      const updated = await updateAgreementYear(yi.id, {
        agreement_id: yi.agreement_id,
        academic_year_id: yi.academic_year_id,
        is_active: yi.is_active,
        n7_places: n7Places,
      });
      setAgreementYears((items) => items.map((y) => (y.id === updated.id ? updated : y)));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de modifier le quota N7.");
    }
  }

  async function handleValidateYear(yi: AgreementYear) {
    setSyncError("");
    try {
      const validated = await validateAgreementYear(yi.id);
      setAgreementYears((items) => items.map((y) => (y.id === validated.id ? validated : y)));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de valider l'instance.");
    }
  }

  // ── DepartmentQuotas — édition inline ────────────────────────────────────

  async function handleSaveDeptQuota(dq: AgreementYearDepartment, places: number) {
    setSyncError("");
    try {
      const updated = await updateAgreementYearDepartment(dq.id, {
        agreement_year_id: dq.agreement_year_id,
        department_id: dq.department_id,
        estimated_places: places,
      });
      setAgreementYearDepartments((items) =>
        items.map((d) => (d.id === updated.id ? updated : d)),
      );
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de modifier le quota département.");
    }
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

  async function handleIgnoreImportError(error: RawImport) {
    await ignoreMobilityImport(error.id);
    setImportErrors((items) => items.filter((e) => e.id !== error.id));
  }

  async function handleRetryImportError(error: RawImport, payload: MobilityImportRetryPayload) {
    try {
      await retryMobilityImport(error.id, payload);
      setImportErrors((items) => items.filter((e) => e.id !== error.id));
      await refreshMobilityData();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de relancer l'import.");
    }
  }

  async function refreshMobilityData() {
    const { getMobilityData } = await import("@/lib/api/mobility");
    const fresh = await getMobilityData();
    setAgreements(fresh.agreements);
    setAgreementYears(fresh.agreementYears);
    setAgreementYearDepartments(fresh.agreementYearDepartments);
    setMobilityCategories(fresh.mobilityCategories);
    setImportErrors(fresh.importErrors);
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {confirmDialog}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard icon={Landmark} label="Accords total" value={agreements.length} helper="" tone="blue" />
        <StatCard icon={Layers} label="Actifs cette année" value={activeYearInstances.length} helper="" tone="emerald" />
        <StatCard icon={Gauge} label="Places N7" value={statTotalN7} helper="" tone="blue" />
        <StatCard icon={FileText} label="Cadres" value={mobilityCategories.length} helper="" tone="amber" />
      </div>

      {/* Section tabs */}
      <PageTabBar
        tabs={[
          { label: "Accords", value: agreements.length, href: "#accords" },
          { label: "Cadres", value: mobilityCategories.length, href: "#cadres" },
        ]}
      />

      {syncError ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {syncError}
        </div>
      ) : null}

      {/* ── Section Accords ─────────────────────────────────────────────── */}
      <MobilitySection
        description="Accords de mobilité, quotas annuels et répartition par département."
        id="accords"
        title="Accords de mobilité"
        toolbar={
          <div className="flex flex-wrap gap-2">
            <button
              className="flex items-center gap-1 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              disabled={syncInProgress}
              onClick={handleSync}
              type="button"
            >
              <RefreshCw className={syncInProgress ? "animate-spin" : ""} size={12} />
              Sync MoveON
            </button>
            <button
              className="flex items-center gap-1 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
              onClick={downloadExcelTemplate}
              type="button"
            >
              <Download size={12} /> Template Excel
            </button>
            <label className="flex cursor-pointer items-center gap-1 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50">
              <input
                accept=".xlsx,.xls"
                className="hidden"
                disabled={excelImportInProgress}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleExcelImport(file);
                  e.target.value = "";
                }}
                type="file"
              />
              {excelImportInProgress ? "Import en cours..." : "Import Excel"}
            </label>
            <button
              className="flex items-center gap-1 rounded-md bg-[#1E3A8A] px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-900"
              onClick={() => setModal({ kind: "agreement" })}
              type="button"
            >
              <Plus size={12} /> Nouvel accord
            </button>
          </div>
        }
      >
        {/* Filtres — une seule ligne */}
        <div className="mb-4 flex items-center gap-2">
          <SearchInput onChange={setQuery} placeholder="Rechercher..." value={query} />
          <select
            className="w-32 rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700"
            onChange={(e) => setYearFilter(e.target.value)}
            value={yearFilter}
          >
            <option value="">Toutes années</option>
            {academicYears.map((y) => (
              <option key={y.id} value={y.label}>{y.label}</option>
            ))}
          </select>
          <select
            className="w-32 rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700"
            onChange={(e) => {
              setCountryFilter(e.target.value);
              setUniversityFilter("all");
            }}
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
            onChange={(e) => setActivityFilter(e.target.value)}
            value={activityFilter}
          >
            <option value="all">Tous</option>
            <option value="active">Actifs</option>
            <option value="inactive">Inactifs</option>
          </select>
        </div>

        <AgreementsTable
          agreements={agreementsForDisplay}
          agreementYears={agreementYears}
          agreementYearDepartments={agreementYearDepartments}
          categories={mobilityCategories}
          departments={departments}
          levels={mobilityLevels}
          universities={universities}
          yearFilter={yearFilter}
          onToggleYearActive={handleToggleYearActive}
          onEditYear={handleEditYear}
          onValidateYear={handleValidateYear}
          onSaveDeptQuota={handleSaveDeptQuota}
        />
      </MobilitySection>

      {/* Erreurs accords */}
      {agreementErrors.length > 0 && (
        <MobilityImportErrorsPanel
          errors={agreementErrors}
          isBusy={syncInProgress || excelImportInProgress}
          onIgnore={handleIgnoreImportError}
          onRetry={handleRetryImportError}
          universities={universities}
        />
      )}

      {/* ── Section Cadres ──────────────────────────────────────────────── */}
      <MobilitySection
        description="Cadres de mobilité (Erasmus, bilatéral, etc.) synchronisés depuis MoveON."
        id="cadres"
        title="Cadres de mobilité"
        toolbar={
          <div className="flex flex-wrap gap-2">
            <button
              className="flex items-center gap-1 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              disabled={categorySyncInProgress}
              onClick={handleCategorySync}
              type="button"
            >
              <RefreshCw className={categorySyncInProgress ? "animate-spin" : ""} size={12} />
              Sync MoveON
            </button>
            <button
              className="flex items-center gap-1 rounded-md bg-[#1E3A8A] px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-900"
              onClick={() => setModal({ kind: "framework" })}
              type="button"
            >
              <Plus size={12} /> Nouveau cadre
            </button>
          </div>
        }
      >
        <MobilityCategorysTable
          agreementFrameworks={mobilityCategories}
          onDelete={removeFramework}
          onEdit={(c) => setModal({ kind: "framework", item: c })}
        />
      </MobilitySection>

      {/* Erreurs cadres */}
      {categoryErrors.length > 0 && (
        <MobilityImportErrorsPanel
          errors={categoryErrors}
          isBusy={categorySyncInProgress}
          onIgnore={handleIgnoreImportError}
          onRetry={handleRetryImportError}
          universities={universities}
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
