"use client";

import { useMemo, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { Plus, RefreshCw } from "lucide-react";

import { CountriesTable } from "@/components/references/countries-table";
import { DepartmentsTable } from "@/components/references/departments-table";
import { ImportErrorsPanel } from "@/components/references/import-errors-panel";
import { LevelForm } from "@/components/references/level-form";
import { LevelsTable } from "@/components/references/levels-table";
import { ParcoursForm } from "@/components/references/parcours-form";
import { ParcoursTable } from "@/components/references/parcours-table";
import {
  ReferenceForm,
  type ReferenceFormKind,
} from "@/components/references/reference-form";
import { ReferenceSection } from "@/components/references/reference-section";
import { ReferenceTabs } from "@/components/references/reference-tabs";
import { UniversitiesTable } from "@/components/references/universities-table";
import { ErrorBanner } from "@/components/ui/alert";
import { Btn } from "@/components/ui/btn";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { Modal } from "@/components/ui/modal";
import { SearchInput } from "@/components/ui/search-input";
import { DEFAULT_PAGE_SIZE } from "@/lib/config";
import {
  createCountry,
  createDepartment,
  createLevel,
  createParcours,
  createUniversity,
  deleteCountry,
  deleteDepartment,
  deleteLevel,
  deleteParcours,
  deleteUniversity,
  fetchUniversitiesPage,
  forceDepartmentImport,
  forceLevelImport,
  forceUniversityImport,
  getDepartmentImportErrors,
  getDepartments,
  getLevelImportErrors,
  getLevels,
  getUniversityImportErrors,
  ignoreDepartmentImport,
  ignoreLevelImport,
  ignoreUniversityImport,
  retryDepartmentImport,
  retryUniversityImport,
  syncDepartmentsFromPegase,
  syncLevelsFromPegase,
  syncUniversitiesFromMoveon,
  updateCountry,
  updateDepartment,
  updateLevel,
  updateParcours,
  updateUniversity,
  type CountryPayload,
  type DepartmentImportCorrection,
  type DepartmentPayload,
  type LevelPayload,
  type ParcoursPayload,
  type PartnerUniversityPayload,
  type UniversityImportCorrection,
} from "@/lib/api/reference-mutations";
import {
  revalidateDepartments,
  revalidateLevels,
  revalidateParcours,
  revalidateUniversities,
} from "@/lib/actions/cache-revalidation";
import type {
  AcademicYear,
  Country,
  Department,
  Level,
  PagedResponse,
  Parcours,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";
import { createIdMap } from "@/lib/utils";

type LevelModalState = { kind: "mobilityLevel"; item?: Level };
type ParcoursModalState = { kind: "parcours"; item?: Parcours };

const REF_ERRORS_PAGE_SIZE = 25;

type ReferencesWorkspaceProps = {
  countries: Country[];
  setCountries: Dispatch<SetStateAction<Country[]>>;
  departments: Department[];
  setDepartments: Dispatch<SetStateAction<Department[]>>;
  universities: PagedResponse<PartnerUniversity>;
  setUniversities: Dispatch<SetStateAction<PagedResponse<PartnerUniversity>>>;
  universityImportErrors: RawImport[];
  setUniversityImportErrors: Dispatch<SetStateAction<RawImport[]>>;
  universityImportErrorsCount: number;
  setUniversityImportErrorsCount: Dispatch<SetStateAction<number>>;
  departmentImportErrors: RawImport[];
  setDepartmentImportErrors: Dispatch<SetStateAction<RawImport[]>>;
  departmentImportErrorsCount: number;
  setDepartmentImportErrorsCount: Dispatch<SetStateAction<number>>;
  mobilityLevels: Level[];
  setMobilityLevels: Dispatch<SetStateAction<Level[]>>;
  levelImportErrors: RawImport[];
  setLevelImportErrors: Dispatch<SetStateAction<RawImport[]>>;
  levelImportErrorsCount: number;
  setLevelImportErrorsCount: Dispatch<SetStateAction<number>>;
  parcours: Parcours[];
  setParcours: Dispatch<SetStateAction<Parcours[]>>;
  currentYear: AcademicYear | null;
};

export function ReferencesWorkspace({
  countries,
  setCountries,
  departments,
  setDepartments,
  universities,
  setUniversities,
  universityImportErrors,
  setUniversityImportErrors,
  universityImportErrorsCount,
  setUniversityImportErrorsCount,
  departmentImportErrors,
  setDepartmentImportErrors,
  departmentImportErrorsCount,
  setDepartmentImportErrorsCount,
  mobilityLevels,
  setMobilityLevels,
  levelImportErrors,
  setLevelImportErrors,
  levelImportErrorsCount,
  setLevelImportErrorsCount,
  parcours,
  setParcours,
  currentYear,
}: ReferencesWorkspaceProps) {
  const refLocked = !!currentYear && currentYear.status !== "initialization";

  const [query, setQuery] = useState("");
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [modal, setModal] = useState<{
    kind: ReferenceFormKind;
    item?: Country | Department | PartnerUniversity;
  } | null>(null);
  const [levelModal, setLevelModal] = useState<LevelModalState | null>(null);
  const [parcoursModal, setParcoursModal] = useState<ParcoursModalState | null>(null);
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [syncError, setSyncError] = useState("");
  const [departmentSyncInProgress, setDepartmentSyncInProgress] = useState(false);
  const [departmentSyncError, setDepartmentSyncError] = useState("");
  const [levelSyncInProgress, setLevelSyncInProgress] = useState(false);
  const [levelSyncError, setLevelSyncError] = useState("");
  const [universityErrorsPage, setUniversityErrorsPage] = useState(1);
  const [departmentErrorsPage, setDepartmentErrorsPage] = useState(1);
  const [levelErrorsPage, setLevelErrorsPage] = useState(1);

  // University server-side pagination & filter state
  const [univPage, setUnivPage] = useState(universities.page);
  const [univCountryFilter, setUnivCountryFilter] = useState<string>("all");
  const univSearchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [univSearch, setUnivSearch] = useState("");

  const normalizedQuery = query.trim().toLowerCase();

  // Client-side filters for small reference lists
  const filteredCountries = useMemo(() => {
    if (!normalizedQuery) return countries;
    return countries.filter((c) =>
      [c.iso2, c.name_fr, c.name_en, c.cti_region].join(" ").toLowerCase().includes(normalizedQuery)
    );
  }, [countries, normalizedQuery]);

  const filteredDepartments = useMemo(() => {
    if (!normalizedQuery) return departments;
    return departments.filter((d) =>
      [d.code, d.name].join(" ").toLowerCase().includes(normalizedQuery)
    );
  }, [departments, normalizedQuery]);

  const filteredLevels = useMemo(() => {
    if (!normalizedQuery) return mobilityLevels;
    return mobilityLevels.filter((l) =>
      [l.code, l.name].join(" ").toLowerCase().includes(normalizedQuery)
    );
  }, [mobilityLevels, normalizedQuery]);

  const filteredParcours = useMemo(() => {
    if (!normalizedQuery) return parcours;
    const deptMap = createIdMap(departments);
    return parcours.filter((p) => {
      const d = deptMap.get(p.department_id);
      return [p.code, p.label, d?.code ?? ""].join(" ").toLowerCase().includes(normalizedQuery);
    });
  }, [parcours, departments, normalizedQuery]);

  // ---------------------------------------------------------------------------
  // University server-side fetch
  // ---------------------------------------------------------------------------

  async function doFetchUniversities(search: string, countryId: string, page: number) {
    const data = await fetchUniversitiesPage({
      search: search || undefined,
      country_id: countryId !== "all" ? Number(countryId) : undefined,
      page,
      page_size: DEFAULT_PAGE_SIZE,
    });
    setUniversities(data);
    setUnivPage(data.page);
  }

  function handleQueryChange(value: string) {
    setQuery(value);
    // Debounce university API call
    if (univSearchTimer.current) clearTimeout(univSearchTimer.current);
    univSearchTimer.current = setTimeout(() => {
      setUnivSearch(value);
      void doFetchUniversities(value, univCountryFilter, 1);
    }, 350);
  }

  function handleUnivCountryChange(value: string) {
    setUnivCountryFilter(value);
    void doFetchUniversities(univSearch, value, 1);
  }

  function handleUnivPageChange(page: number) {
    setUnivPage(page);
    void doFetchUniversities(univSearch, univCountryFilter, page);
  }

  // ---------------------------------------------------------------------------
  // Import error loaders (server-side pagination)
  // ---------------------------------------------------------------------------

  async function loadUniversityErrors(page: number) {
    try {
      const data = await getUniversityImportErrors({ page, page_size: REF_ERRORS_PAGE_SIZE });
      setUniversityImportErrors(data.results);
      setUniversityImportErrorsCount(data.count);
      setUniversityErrorsPage(page);
    } catch { /* silently ignore */ }
  }

  async function loadDepartmentErrors(page: number) {
    try {
      const data = await getDepartmentImportErrors({ page, page_size: REF_ERRORS_PAGE_SIZE });
      setDepartmentImportErrors(data.results);
      setDepartmentImportErrorsCount(data.count);
      setDepartmentErrorsPage(page);
    } catch { /* silently ignore */ }
  }

  async function loadLevelErrors(page: number) {
    try {
      const data = await getLevelImportErrors({ page, page_size: REF_ERRORS_PAGE_SIZE });
      setLevelImportErrors(data.results);
      setLevelImportErrorsCount(data.count);
      setLevelErrorsPage(page);
    } catch { /* silently ignore */ }
  }

  // ---------------------------------------------------------------------------
  // Mutations
  // ---------------------------------------------------------------------------

  async function submitReference(
    payload: CountryPayload | DepartmentPayload | PartnerUniversityPayload
  ) {
    if (!modal) return;
    if (modal.kind === "country") {
      const p = payload as CountryPayload;
      if (modal.item && "iso2" in modal.item) {
        const res = await updateCountry(modal.item.id, p);
        setCountries((prev) => prev.map((i) => (i.id === res.id ? res : i)));
      } else {
        const res = await createCountry(p);
        setCountries((prev) => [...prev, res]);
      }
    }
    if (modal.kind === "department") {
      const p = payload as DepartmentPayload;
      if (modal.item && "code" in modal.item) {
        const res = await updateDepartment(modal.item.id, p);
        setDepartments((prev) => prev.map((i) => (i.id === res.id ? res : i)));
      } else {
        const res = await createDepartment(p);
        setDepartments((prev) => [...prev, res]);
      }
      await revalidateDepartments();
    }
    if (modal.kind === "university") {
      const p = payload as PartnerUniversityPayload;
      if (modal.item && "country_id" in modal.item) {
        const res = await updateUniversity(modal.item.id, p);
        setUniversities((prev) => ({ ...prev, results: prev.results.map((i) => (i.id === res.id ? res : i)) }));
      } else {
        const res = await createUniversity(p);
        setUniversities((prev) => ({ ...prev, results: [...prev.results, res], count: prev.count + 1 }));
      }
      await revalidateUniversities();
    }
    setModal(null);
  }

  async function submitLevel(payload: LevelPayload) {
    if (!levelModal) return;
    if (levelModal.item) {
      const res = await updateLevel(levelModal.item.id, payload);
      setMobilityLevels((prev) => prev.map((i) => (i.id === res.id ? res : i)));
    } else {
      const res = await createLevel(payload);
      setMobilityLevels((prev) => [...prev, res]);
    }
    await revalidateLevels();
    setLevelModal(null);
  }

  async function submitParcours(payload: ParcoursPayload) {
    if (!parcoursModal) return;
    if (parcoursModal.item) {
      const res = await updateParcours(parcoursModal.item.id, payload);
      setParcours((prev) => prev.map((i) => (i.id === res.id ? res : i)));
    } else {
      const res = await createParcours(payload);
      setParcours((prev) => [...prev, res]);
    }
    await revalidateParcours();
    setParcoursModal(null);
  }

  async function removeCountry(country: Country) {
    if (!await confirm(`Supprimer le pays "${country.name_fr}" ?`)) return;
    await deleteCountry(country.id);
    setCountries((prev) => prev.filter((i) => i.id !== country.id));
  }

  async function removeDepartment(department: Department) {
    if (!await confirm(`Supprimer le departement "${department.code}" ?`)) return;
    await deleteDepartment(department.id);
    setDepartments((prev) => prev.filter((i) => i.id !== department.id));
    await revalidateDepartments();
  }

  async function removeUniversity(university: PartnerUniversity) {
    if (!await confirm(`Supprimer l'universite "${university.name}" ?`)) return;
    await deleteUniversity(university.id);
    setUniversities((prev) => ({
      ...prev,
      results: prev.results.filter((i) => i.id !== university.id),
      count: Math.max(0, prev.count - 1),
    }));
    await revalidateUniversities();
  }

  async function removeLevel(level: Level) {
    if (!await confirm(`Supprimer le niveau "${level.code}" ?`)) return;
    await deleteLevel(level.id);
    setMobilityLevels((prev) => prev.filter((i) => i.id !== level.id));
    await revalidateLevels();
  }

  async function removeParcours(p: Parcours) {
    if (!await confirm(`Supprimer le parcours "${p.code}" ?`)) return;
    await deleteParcours(p.id);
    setParcours((prev) => prev.filter((i) => i.id !== p.id));
    await revalidateParcours();
  }

  async function handleSyncUniversities() {
    setSyncError("");
    setSyncInProgress(true);
    const prev = getSyncFingerprint(universities, universityImportErrors);
    try {
      await syncUniversitiesFromMoveon();
      await waitForUniversitySyncRefresh(prev);
      await revalidateUniversities();
    } catch (error) {
      setSyncError(error instanceof Error ? error.message : "La synchronisation a echoue.");
    } finally {
      setSyncInProgress(false);
    }
  }

  async function handleSyncDepartments() {
    setDepartmentSyncError("");
    setDepartmentSyncInProgress(true);
    const prev = getDepartmentSyncFingerprint(departments, departmentImportErrors);
    try {
      await syncDepartmentsFromPegase();
      await waitForDepartmentSyncRefresh(prev);
      await revalidateDepartments();
    } catch (error) {
      setDepartmentSyncError(error instanceof Error ? error.message : "La synchronisation a echoue.");
    } finally {
      setDepartmentSyncInProgress(false);
    }
  }

  async function handleSyncLevels() {
    setLevelSyncError("");
    setLevelSyncInProgress(true);
    try {
      await syncLevelsFromPegase();
      await delay(3000);
      const [nextLevels, errPage] = await Promise.all([getLevels(), getLevelImportErrors({ page: 1, page_size: REF_ERRORS_PAGE_SIZE })]);
      setMobilityLevels(nextLevels);
      setLevelImportErrors(errPage.results);
      setLevelImportErrorsCount(errPage.count);
      setLevelErrorsPage(1);
      await revalidateLevels();
    } catch (error) {
      setLevelSyncError(error instanceof Error ? error.message : "La synchronisation a echoue.");
    } finally {
      setLevelSyncInProgress(false);
    }
  }

  async function refreshDepartmentData() {
    const [depts, errPage] = await Promise.all([getDepartments(), getDepartmentImportErrors({ page: 1, page_size: REF_ERRORS_PAGE_SIZE })]);
    setDepartments(depts);
    setDepartmentImportErrors(errPage.results);
    setDepartmentImportErrorsCount(errPage.count);
    setDepartmentErrorsPage(1);
    return { errors: errPage.results, departments: depts };
  }

  async function waitForDepartmentSyncRefresh(prev: string) {
    for (let i = 0; i < 30; i++) {
      await delay(1000);
      const res = await refreshDepartmentData();
      if (getDepartmentSyncFingerprint(res.departments, res.errors) !== prev) return;
    }
    await refreshDepartmentData();
  }

  async function refreshUniversityData() {
    const [univData, errPage] = await Promise.all([
      fetchUniversitiesPage({ search: univSearch || undefined, country_id: univCountryFilter !== "all" ? Number(univCountryFilter) : undefined, page: univPage, page_size: DEFAULT_PAGE_SIZE }),
      getUniversityImportErrors({ page: 1, page_size: REF_ERRORS_PAGE_SIZE }),
    ]);
    setUniversities(univData);
    setUniversityImportErrors(errPage.results);
    setUniversityImportErrorsCount(errPage.count);
    setUniversityErrorsPage(1);
    return { errors: errPage.results, universities: univData };
  }

  async function waitForUniversitySyncRefresh(prev: string) {
    for (let i = 0; i < 30; i++) {
      await delay(1000);
      const res = await refreshUniversityData();
      if (getSyncFingerprint(res.universities, res.errors) !== prev) return;
    }
    await refreshUniversityData();
  }

  async function retryImportError(error: RawImport, correction: UniversityImportCorrection) {
    await retryUniversityImport(error.id, correction);
    const univData = await fetchUniversitiesPage({ search: univSearch || undefined, country_id: univCountryFilter !== "all" ? Number(univCountryFilter) : undefined, page: univPage, page_size: DEFAULT_PAGE_SIZE });
    setUniversities(univData);
    await loadUniversityErrors(universityErrorsPage);
    await revalidateUniversities();
  }

  async function ignoreImportError(error: RawImport) {
    await ignoreUniversityImport(error.id);
    await loadUniversityErrors(universityErrorsPage);
  }

  async function forceUniversityImportError(error: RawImport) {
    await forceUniversityImport(error.id);
    const univData = await fetchUniversitiesPage({ search: univSearch || undefined, country_id: univCountryFilter !== "all" ? Number(univCountryFilter) : undefined, page: univPage, page_size: DEFAULT_PAGE_SIZE });
    setUniversities(univData);
    await loadUniversityErrors(universityErrorsPage);
    await revalidateUniversities();
  }

  async function retryDepartmentImportError(error: RawImport, correction: DepartmentImportCorrection) {
    await retryDepartmentImport(error.id, correction);
    const refreshed = await getDepartments();
    setDepartments(refreshed);
    await loadDepartmentErrors(departmentErrorsPage);
    await revalidateDepartments();
  }

  async function ignoreDepartmentImportError(error: RawImport) {
    await ignoreDepartmentImport(error.id);
    await loadDepartmentErrors(departmentErrorsPage);
  }

  async function forceDepartmentImportError(error: RawImport) {
    await forceDepartmentImport(error.id);
    const depts = await getDepartments();
    setDepartments(depts);
    await loadDepartmentErrors(departmentErrorsPage);
    await revalidateDepartments();
  }

  async function ignoreLevelImportError(error: RawImport) {
    await ignoreLevelImport(error.id);
    await loadLevelErrors(levelErrorsPage);
  }

  async function forceLevelImportError(error: RawImport) {
    await forceLevelImport(error.id);
    const levels = await getLevels();
    setMobilityLevels(levels);
    await loadLevelErrors(levelErrorsPage);
    await revalidateLevels();
  }

  const sortedCountries = useMemo(
    () => [...countries].sort((a, b) => a.name_fr.localeCompare(b.name_fr)),
    [countries],
  );

  return (
    <>
      <ReferenceTabs
        departmentsCount={departments.length}
        levelsCount={mobilityLevels.length}
        universitiesCount={universities.count}
        countriesCount={countries.length}
        parcoursCount={parcours.length}
      />

      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <SearchInput
          onChange={handleQueryChange}
          placeholder="Rechercher dans les referentiels..."
          value={query}
        />
      </div>

      <ErrorBanner message={syncError} />
      <ErrorBanner message={departmentSyncError} />
      <ErrorBanner message={levelSyncError} />

      {refLocked && (
        <div className="flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-800">
          Modifications des référentiels disponibles uniquement en <span className="font-semibold mx-1">phase Initialisation</span>.
        </div>
      )}

      <div className="space-y-10">
        <div id="departements">
          <ReferenceSection
            title="Departements"
            description="Departements pedagogiques."
            toolbar={
              <div className="flex gap-2">
                <AddButton label="Ajouter" disabled={refLocked} onClick={() => setModal({ kind: "department" })} />
                <SyncButton label="Sync Pegase" isLoading={departmentSyncInProgress} disabled={refLocked} onClick={handleSyncDepartments} />
              </div>
            }
          >
            <DepartmentsTable
              departments={filteredDepartments}
              readOnly={refLocked}
              onDelete={removeDepartment}
              onEdit={(d) => setModal({ kind: "department", item: d })}
            />
            <ImportErrorsPanel
              title="Erreurs Pegase"
              countries={countries}
              errors={departmentImportErrors}
              isBusy={departmentSyncInProgress}
              onIgnore={ignoreDepartmentImportError}
              onRetry={(e, c) => retryDepartmentImportError(e, c as DepartmentImportCorrection)}
              onForce={forceDepartmentImportError}
              totalCount={departmentImportErrorsCount}
              page={departmentErrorsPage}
              pageSize={REF_ERRORS_PAGE_SIZE}
              onPageChange={loadDepartmentErrors}
            />
          </ReferenceSection>
        </div>

        <div id="parcours">
          <ReferenceSection
            title="Parcours"
            description="Parcours pedagogiques par departement."
            toolbar={
              <AddButton
                label="Ajouter un parcours"
                disabled={refLocked}
                onClick={() => setParcoursModal({ kind: "parcours" })}
              />
            }
          >
            <ParcoursTable
              parcours={filteredParcours}
              departments={departments}
              readOnly={refLocked}
              onDelete={removeParcours}
              onEdit={(p) => setParcoursModal({ kind: "parcours", item: p })}
            />
          </ReferenceSection>
        </div>

        <div id="niveaux">
          <ReferenceSection
            title="Niveaux"
            description="Niveaux d'etude synchronises depuis Pegase."
            toolbar={
              <div className="flex gap-2">
                <AddButton label="Ajouter un niveau" disabled={refLocked} onClick={() => setLevelModal({ kind: "mobilityLevel" })} />
                <SyncButton label="Sync Pegase" isLoading={levelSyncInProgress} disabled={refLocked} onClick={handleSyncLevels} />
              </div>
            }
          >
            <LevelsTable
              levels={filteredLevels}
              readOnly={refLocked}
              onDelete={removeLevel}
              onEdit={(l) => setLevelModal({ kind: "mobilityLevel", item: l })}
            />
            {levelImportErrors.length > 0 && (
              <ImportErrorsPanel
                title="Erreurs Pegase (niveaux)"
                countries={countries}
                errors={levelImportErrors}
                isBusy={levelSyncInProgress}
                onIgnore={ignoreLevelImportError}
                onForce={forceLevelImportError}
                totalCount={levelImportErrorsCount}
                page={levelErrorsPage}
                pageSize={REF_ERRORS_PAGE_SIZE}
                onPageChange={loadLevelErrors}
              />
            )}
          </ReferenceSection>
        </div>

        <div id="universites">
          <ReferenceSection
            title="Universités"
            description="Établissements partenaires."
            toolbar={
              <div className="flex items-center gap-2">
                <select
                  className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700"
                  value={univCountryFilter}
                  onChange={(e) => handleUnivCountryChange(e.target.value)}
                >
                  <option value="all">Tous les pays</option>
                  {sortedCountries.map((c) => (
                    <option key={c.id} value={c.id}>{c.name_fr}</option>
                  ))}
                </select>
                <AddButton label="Ajouter" disabled={refLocked} onClick={() => setModal({ kind: "university" })} />
                <SyncButton label="Sync MoveON" isLoading={syncInProgress} disabled={refLocked} onClick={handleSyncUniversities} />
              </div>
            }
          >
            <UniversitiesTable
              onDelete={removeUniversity}
              onEdit={(u) => setModal({ kind: "university", item: u })}
              universities={universities.results}
              readOnly={refLocked}
              serverSidePagination={{
                totalItems: universities.count,
                page: univPage,
                pageSize: DEFAULT_PAGE_SIZE,
                onPageChange: handleUnivPageChange,
              }}
            />
            <ImportErrorsPanel
              title="Erreurs MoveON"
              countries={countries}
              errors={universityImportErrors}
              isBusy={syncInProgress}
              onIgnore={ignoreImportError}
              onRetry={(e, c) => retryImportError(e, c as UniversityImportCorrection)}
              onForce={forceUniversityImportError}
              totalCount={universityImportErrorsCount}
              page={universityErrorsPage}
              pageSize={REF_ERRORS_PAGE_SIZE}
              onPageChange={loadUniversityErrors}
            />
          </ReferenceSection>
        </div>

        <div id="pays">
          <ReferenceSection
            title="Pays"
            description="Liste stable des pays."
            toolbar={<AddButton label="Ajouter un pays" disabled={refLocked} onClick={() => setModal({ kind: "country" })} />}
          >
            <CountriesTable
              countries={filteredCountries}
              readOnly={refLocked}
              onDelete={removeCountry}
              onEdit={(c) => setModal({ kind: "country", item: c })}
            />
          </ReferenceSection>
        </div>
      </div>

      {modal && (
        <Modal
          onClose={() => setModal(null)}
          title={`${modal.item ? "Modifier" : "Ajouter"} ${getModalLabel(modal.kind)}`}
          description="Veuillez remplir les informations ci-dessous."
        >
          <ReferenceForm
            countries={countries}
            item={modal.item}
            kind={modal.kind}
            onCancel={() => setModal(null)}
            onSubmit={submitReference}
          />
        </Modal>
      )}

      {levelModal && (
        <Modal
          onClose={() => setLevelModal(null)}
          title={levelModal.item ? "Modifier le niveau" : "Ajouter un niveau"}
          description="Niveau d'etude pour les contraintes d'accords de mobilite."
        >
          <LevelForm
            item={levelModal.item}
            onCancel={() => setLevelModal(null)}
            onSubmit={submitLevel}
          />
        </Modal>
      )}

      {parcoursModal && (
        <Modal
          onClose={() => setParcoursModal(null)}
          title={parcoursModal.item ? "Modifier le parcours" : "Ajouter un parcours"}
          description="Parcours pedagogique rattache a un departement."
        >
          <ParcoursForm
            item={parcoursModal.item}
            departments={departments}
            onCancel={() => setParcoursModal(null)}
            onSubmit={submitParcours}
          />
        </Modal>
      )}

      {confirmDialog}
    </>
  );
}

function AddButton({ label, onClick, disabled }: { label: string; onClick: () => void; disabled?: boolean }) {
  return (
    <Btn variant="primary" disabled={disabled} onClick={onClick}>
      <Plus className="h-4 w-4" /> {label}
    </Btn>
  );
}

function SyncButton({ isLoading, label, onClick, disabled }: { isLoading: boolean; label: string; onClick: () => void; disabled?: boolean }) {
  return (
    <Btn disabled={isLoading || disabled} onClick={onClick}>
      <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
      {isLoading ? "Synchronisation..." : label}
    </Btn>
  );
}

function getModalLabel(kind: ReferenceFormKind) {
  if (kind === "country") return "un pays";
  if (kind === "department") return "un departement";
  return "une universite";
}

function getSyncFingerprint(univs: PagedResponse<PartnerUniversity>, errs: RawImport[]) {
  return JSON.stringify({
    errs: errs.map((e) => ({ id: e.id, status: e.status })),
    univs: univs.results.map((u) => ({ id: u.id, updated_at: u.updated_at })),
    count: univs.count,
  });
}

function getDepartmentSyncFingerprint(depts: Department[], errs: RawImport[]) {
  return JSON.stringify({
    errs: errs.map((e) => ({ id: e.id, status: e.status })),
    depts: depts.map((d) => ({ id: d.id, updated_at: d.updated_at })),
  });
}

function delay(ms: number) {
  return new Promise((res) => setTimeout(res, ms));
}
