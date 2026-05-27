"use client";

import { useMemo, useState, type Dispatch, type SetStateAction } from "react";
import { Plus } from "lucide-react";

import { CountriesTable } from "@/components/references/countries-table";
import { DepartmentsTable } from "@/components/references/departments-table";
import { ImportErrorsPanel } from "@/components/references/import-errors-panel";
import {
  ReferenceForm,
  type ReferenceFormKind,
} from "@/components/references/reference-form";
import { ReferenceSection } from "@/components/references/reference-section";
import { ReferenceTabs } from "@/components/references/reference-tabs";
import { UniversitiesTable } from "@/components/references/universities-table";
import { LevelForm } from "@/components/references/level-form";
import { LevelsTable } from "@/components/references/levels-table";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { Modal } from "@/components/ui/modal";
import { SearchInput } from "@/components/ui/search-input";
import {
  createCountry,
  createDepartment,
  createUniversity,
  deleteCountry,
  deleteDepartment,
  deleteUniversity,
  getDepartments,
  getUniversities,
  getDepartmentImportErrors,
  getUniversityImportErrors,
  ignoreDepartmentImport,
  ignoreUniversityImport,
  retryDepartmentImport,
  retryUniversityImport,
  syncDepartmentsFromPegase,
  syncUniversitiesFromMoveon,
  updateCountry,
  updateDepartment,
  updateUniversity,
  type CountryPayload,
  type DepartmentPayload,
  type PartnerUniversityPayload,
} from "@/lib/api/reference-mutations";
import {
  createLevel,
  deleteLevel,
  getLevelImportErrors,
  getLevels,
  ignoreLevelImport,
  syncLevelsFromPegase,
  updateLevel,
  type LevelPayload,
} from "@/lib/api/reference-mutations";
import type {
  Country,
  Department,
  Level,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

type LevelModalState = { kind: "mobilityLevel"; item?: Level };

type ReferencesWorkspaceProps = {
  countries: Country[];
  setCountries: Dispatch<SetStateAction<Country[]>>;
  departments: Department[];
  setDepartments: Dispatch<SetStateAction<Department[]>>;
  universities: PartnerUniversity[];
  setUniversities: Dispatch<SetStateAction<PartnerUniversity[]>>;
  universityImportErrors: RawImport[];
  setUniversityImportErrors: Dispatch<SetStateAction<RawImport[]>>;
  departmentImportErrors: RawImport[];
  setDepartmentImportErrors: Dispatch<SetStateAction<RawImport[]>>;
  mobilityLevels: Level[];
  setMobilityLevels: Dispatch<SetStateAction<Level[]>>;
  levelImportErrors: RawImport[];
  setLevelImportErrors: Dispatch<SetStateAction<RawImport[]>>;
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
  departmentImportErrors,
  setDepartmentImportErrors,
  mobilityLevels,
  setMobilityLevels,
  levelImportErrors,
  setLevelImportErrors,
}: ReferencesWorkspaceProps) {
  const [query, setQuery] = useState("");
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [modal, setModal] = useState<{
    kind: ReferenceFormKind;
    item?: Country | Department | PartnerUniversity;
  } | null>(null);
  const [levelModal, setLevelModal] = useState<LevelModalState | null>(null);
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [syncError, setSyncError] = useState("");
  const [departmentSyncInProgress, setDepartmentSyncInProgress] = useState(false);
  const [departmentSyncError, setDepartmentSyncError] = useState("");
  const [levelSyncInProgress, setLevelSyncInProgress] = useState(false);
  const [levelSyncError, setLevelSyncError] = useState("");
  const normalizedQuery = query.trim().toLowerCase();

  const filteredCountries = useMemo(() => {
    if (!normalizedQuery) return countries;
    return countries.filter((c) =>
      [c.iso2, c.name_fr, c.name_en, c.cti_region]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery)
    );
  }, [countries, normalizedQuery]);

  const filteredDepartments = useMemo(() => {
    if (!normalizedQuery) return departments;
    return departments.filter((d) =>
      [d.code, d.name].join(" ").toLowerCase().includes(normalizedQuery)
    );
  }, [departments, normalizedQuery]);

  const filteredUniversities = useMemo(() => {
    if (!normalizedQuery) return universities;
    const countriesById = new Map(countries.map((c) => [c.id, c]));
    return universities.filter((u) => {
      const c = countriesById.get(u.country_id);
      return [
        u.name,
        u.short_name,
        u.translated_name,
        u.erasmus_code,
        u.city,
        u.email,
        c?.iso2,
        c?.name_fr,
        c?.name_en,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [countries, normalizedQuery, universities]);

  const filteredLevels = useMemo(() => {
    if (!normalizedQuery) return mobilityLevels;
    return mobilityLevels.filter((l) =>
      [l.code, l.name].join(" ").toLowerCase().includes(normalizedQuery)
    );
  }, [mobilityLevels, normalizedQuery]);

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
    }
    if (modal.kind === "university") {
      const p = payload as PartnerUniversityPayload;
      if (modal.item && "country_id" in modal.item) {
        const res = await updateUniversity(modal.item.id, p);
        setUniversities((prev) => prev.map((i) => (i.id === res.id ? res : i)));
      } else {
        const res = await createUniversity(p);
        setUniversities((prev) => [...prev, res]);
      }
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
    setLevelModal(null);
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
  }

  async function removeUniversity(university: PartnerUniversity) {
    if (!await confirm(`Supprimer l'universite "${university.name}" ?`)) return;
    await deleteUniversity(university.id);
    setUniversities((prev) => prev.filter((i) => i.id !== university.id));
  }

  async function removeLevel(level: Level) {
    if (!await confirm(`Supprimer le niveau "${level.code}" ?`)) return;
    await deleteLevel(level.id);
    setMobilityLevels((prev) => prev.filter((i) => i.id !== level.id));
  }

  async function handleSyncUniversities() {
    setSyncError("");
    setSyncInProgress(true);
    const prev = getSyncFingerprint(universities, universityImportErrors);
    try {
      await syncUniversitiesFromMoveon();
      await waitForUniversitySyncRefresh(prev);
    } catch (error) {
      setSyncError(
        error instanceof Error ? error.message : "La synchronisation a echoue.",
      );
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
    } catch (error) {
      setDepartmentSyncError(
        error instanceof Error ? error.message : "La synchronisation a echoue.",
      );
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
      const [nextLevels, nextErrors] = await Promise.all([
        getLevels(),
        getLevelImportErrors(),
      ]);
      setMobilityLevels(nextLevels);
      setLevelImportErrors(nextErrors);
    } catch (error) {
      setLevelSyncError(
        error instanceof Error ? error.message : "La synchronisation a echoue.",
      );
    } finally {
      setLevelSyncInProgress(false);
    }
  }

  async function refreshDepartmentData() {
    const [depts, errs] = await Promise.all([getDepartments(), getDepartmentImportErrors()]);
    setDepartments(depts);
    setDepartmentImportErrors(errs);
    return { errors: errs, departments: depts };
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
    const [univs, errs] = await Promise.all([getUniversities(), getUniversityImportErrors()]);
    setUniversities(univs);
    setUniversityImportErrors(errs);
    return { errors: errs, universities: univs };
  }

  async function waitForUniversitySyncRefresh(prev: string) {
    for (let i = 0; i < 30; i++) {
      await delay(1000);
      const res = await refreshUniversityData();
      if (getSyncFingerprint(res.universities, res.errors) !== prev) return;
    }
    await refreshUniversityData();
  }

  async function retryImportError(error: RawImport, correction?: number | string) {
    if (typeof correction !== "number") return;
    await retryUniversityImport(error.id, correction);
    const refreshed = await getUniversities();
    setUniversities(refreshed);
    setUniversityImportErrors((prev) => prev.filter((i) => i.id !== error.id));
  }

  async function ignoreImportError(error: RawImport) {
    await ignoreUniversityImport(error.id);
    setUniversityImportErrors((prev) => prev.filter((i) => i.id !== error.id));
  }

  async function retryDepartmentImportError(error: RawImport, correction?: number | string) {
    if (typeof correction !== "string" || !correction.trim()) return;
    await retryDepartmentImport(error.id, correction);
    const refreshed = await getDepartments();
    setDepartments(refreshed);
    setDepartmentImportErrors((prev) => prev.filter((i) => i.id !== error.id));
  }

  async function ignoreDepartmentImportError(error: RawImport) {
    await ignoreDepartmentImport(error.id);
    setDepartmentImportErrors((prev) => prev.filter((i) => i.id !== error.id));
  }

  async function ignoreLevelImportError(error: RawImport) {
    await ignoreLevelImport(error.id);
    setLevelImportErrors((prev) => prev.filter((i) => i.id !== error.id));
  }

  return (
    <>
      <ReferenceTabs
        departmentsCount={departments.length}
        levelsCount={mobilityLevels.length}
        universitiesCount={universities.length}
        countriesCount={countries.length}

      />

      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <SearchInput
          onChange={setQuery}
          placeholder="Rechercher dans les referentiels..."
          value={query}
        />
      </div>

      {syncError ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {syncError}
        </div>
      ) : null}

      {departmentSyncError ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {departmentSyncError}
        </div>
      ) : null}

      {levelSyncError ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {levelSyncError}
        </div>
      ) : null}

      <div className="space-y-10">
        

        <div id="departements">
          <ReferenceSection
            title="Departements"
            description="Departements pedagogiques."
            toolbar={
              <div className="flex gap-2">
                <AddButton label="Ajouter" onClick={() => setModal({ kind: "department" })} />
                <SyncButton label="Sync Pegase" isLoading={departmentSyncInProgress} onClick={handleSyncDepartments} />
              </div>
            }
          >
            <DepartmentsTable
              departments={filteredDepartments}
              onDelete={removeDepartment}
              onEdit={(d) => setModal({ kind: "department", item: d })}
            />
            <ImportErrorsPanel
              title="Erreurs Pegase"
              retryField="code"
              countries={countries}
              errors={departmentImportErrors}
              isBusy={departmentSyncInProgress}
              onIgnore={ignoreDepartmentImportError}
              onRetry={retryDepartmentImportError}
            />
          </ReferenceSection>
        </div>

        <div id="niveaux">
          <ReferenceSection
            title="Niveaux"
            description="Niveaux d'etude synchronises depuis Pegase."
            toolbar={
              <div className="flex gap-2">
                <AddButton label="Ajouter un niveau" onClick={() => setLevelModal({ kind: "mobilityLevel" })} />
                <SyncButton label="Sync Pegase" isLoading={levelSyncInProgress} onClick={handleSyncLevels} />
              </div>
            }
          >
            <LevelsTable
              levels={filteredLevels}
              onDelete={removeLevel}
              onEdit={(l) => setLevelModal({ kind: "mobilityLevel", item: l })}
            />
            {levelImportErrors.length > 0 ? (
              <ImportErrorsPanel
                title="Erreurs Pegase (niveaux)"
                retryField="code"
                countries={countries}
                errors={levelImportErrors}
                isBusy={levelSyncInProgress}
                onIgnore={ignoreLevelImportError}
                onRetry={async () => {}}
              />
            ) : null}
          </ReferenceSection>
        </div>

        <div id="universites">
          <ReferenceSection
            title="Universites"
            description="Etablissements partenaires."
            toolbar={
              <div className="flex gap-2">
                <AddButton label="Ajouter" onClick={() => setModal({ kind: "university" })} />
                <SyncButton label="Sync MoveON" isLoading={syncInProgress} onClick={handleSyncUniversities} />
              </div>
            }
          >
            <UniversitiesTable
              countries={countries}
              onDelete={removeUniversity}
              onEdit={(u) => setModal({ kind: "university", item: u })}
              universities={filteredUniversities}
            />
            <ImportErrorsPanel
              title="Erreurs MoveON"
              retryField="country"
              countries={countries}
              errors={universityImportErrors}
              isBusy={syncInProgress}
              onIgnore={ignoreImportError}
              onRetry={retryImportError}
            />
          </ReferenceSection>
        </div>

        <div id="pays">
          <ReferenceSection
            title="Pays"
            description="Liste stable des pays."
            toolbar={<AddButton label="Ajouter un pays" onClick={() => setModal({ kind: "country" })} />}
          >
            <CountriesTable
              countries={filteredCountries}
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
      {confirmDialog}
    </>
  );
}

function AddButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button className="bg-[#1E3A8A] text-white px-4 py-2 rounded-md text-sm font-medium" onClick={onClick}>
      <Plus className="inline h-4 w-4 mr-1" /> {label}
    </button>
  );
}

function SyncButton({ isLoading, label, onClick }: { isLoading: boolean; label: string; onClick: () => void }) {
  return (
    <button
      className="border border-gray-300 px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
      onClick={onClick}
      disabled={isLoading}
    >
      {isLoading ? "En cours..." : label}
    </button>
  );
}

function getModalLabel(kind: ReferenceFormKind) {
  if (kind === "country") return "un pays";
  if (kind === "department") return "un departement";
  return "une universite";
}

function getSyncFingerprint(univs: PartnerUniversity[], errs: RawImport[]) {
  return JSON.stringify({
    errs: errs.map((e) => ({ id: e.id, status: e.status })),
    univs: univs.map((u) => ({ id: u.id, updated_at: u.updated_at })),
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
