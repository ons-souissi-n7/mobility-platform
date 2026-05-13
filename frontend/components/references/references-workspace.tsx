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
import { Modal } from "@/components/ui/modal";
import { SearchInput } from "@/components/ui/search-input";
import {
  createCountry,
  createDepartment,
  createUniversity,
  deleteCountry,
  deleteDepartment,
  deleteUniversity,
  getUniversities,
  getUniversityImportErrors,
  ignoreUniversityImport,
  retryUniversityImport,
  syncUniversitiesFromMoveon,
  updateCountry,
  updateDepartment,
  updateUniversity,
  type CountryPayload,
  type DepartmentPayload,
  type PartnerUniversityPayload,
} from "@/lib/api/reference-mutations";
import type {
  Country,
  Department,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

type ReferencesWorkspaceProps = {
  countries: Country[];
  setCountries: Dispatch<SetStateAction<Country[]>>;
  departments: Department[];
  setDepartments: Dispatch<SetStateAction<Department[]>>;
  universities: PartnerUniversity[];
  setUniversities: Dispatch<SetStateAction<PartnerUniversity[]>>;
  universityImportErrors: RawImport[];
  setUniversityImportErrors: Dispatch<SetStateAction<RawImport[]>>;
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
}: ReferencesWorkspaceProps) {
  const [query, setQuery] = useState("");
  const [modal, setModal] = useState<{
    kind: ReferenceFormKind;
    item?: Country | Department | PartnerUniversity;
  } | null>(null);
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [syncError, setSyncError] = useState("");
  const normalizedQuery = query.trim().toLowerCase();

  const filteredCountries = useMemo(() => {
    if (!normalizedQuery) {
      return countries;
    }

    return countries.filter((country) =>
      [country.iso2, country.name_fr, country.name_en, country.cti_region]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [countries, normalizedQuery]);

  const filteredDepartments = useMemo(() => {
    if (!normalizedQuery) {
      return departments;
    }

    return departments.filter((department) =>
      [department.code, department.name]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [departments, normalizedQuery]);

  const filteredUniversities = useMemo(() => {
    if (!normalizedQuery) {
      return universities;
    }

    const countriesById = new Map(countries.map((country) => [country.id, country]));

    return universities.filter((university) => {
      const country = countriesById.get(university.country_id);

      return [
        university.name,
        university.short_name,
        university.translated_name,
        university.erasmus_code,
        university.city,
        university.email,
        country?.iso2,
        country?.name_fr,
        country?.name_en,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [countries, normalizedQuery, universities]);

  async function submitReference(
    payload: CountryPayload | DepartmentPayload | PartnerUniversityPayload,
  ) {
    if (!modal) {
      return;
    }

    if (modal.kind === "country") {
      const countryPayload = payload as CountryPayload;
      if (modal.item && "iso2" in modal.item) {
        const updated = await updateCountry(modal.item.id, countryPayload);
        setCountries((items) =>
          items.map((item) => (item.id === updated.id ? updated : item)),
        );
      } else {
        const created = await createCountry(countryPayload);
        setCountries((items) => [...items, created]);
      }
    }

    if (modal.kind === "department") {
      const departmentPayload = payload as DepartmentPayload;
      if (modal.item && "code" in modal.item) {
        const updated = await updateDepartment(modal.item.id, departmentPayload);
        setDepartments((items) =>
          items.map((item) => (item.id === updated.id ? updated : item)),
        );
      } else {
        const created = await createDepartment(departmentPayload);
        setDepartments((items) => [...items, created]);
      }
    }

    if (modal.kind === "university") {
      const universityPayload = payload as PartnerUniversityPayload;
      if (modal.item && "country_id" in modal.item) {
        const updated = await updateUniversity(modal.item.id, universityPayload);
        setUniversities((items) =>
          items.map((item) => (item.id === updated.id ? updated : item)),
        );
      } else {
        const created = await createUniversity(universityPayload);
        setUniversities((items) => [...items, created]);
      }
    }

    setModal(null);
  }

  async function removeCountry(country: Country) {
    if (!window.confirm(`Supprimer le pays ${country.name_fr} ?`)) {
      return;
    }

    await deleteCountry(country.id);
    setCountries((items) => items.filter((item) => item.id !== country.id));
  }

  async function removeDepartment(department: Department) {
    if (!window.confirm(`Supprimer le departement ${department.code} ?`)) {
      return;
    }

    await deleteDepartment(department.id);
    setDepartments((items) => items.filter((item) => item.id !== department.id));
  }

  async function removeUniversity(university: PartnerUniversity) {
    if (!window.confirm(`Supprimer l'universite ${university.name} ?`)) {
      return;
    }

    await deleteUniversity(university.id);
    setUniversities((items) => items.filter((item) => item.id !== university.id));
  }

  async function handleSyncUniversities() {
    setSyncError("");
    setSyncInProgress(true);
    const previousFingerprint = getSyncFingerprint(
      universities,
      universityImportErrors,
    );

    try {
      await syncUniversitiesFromMoveon();
      await waitForUniversitySyncRefresh(previousFingerprint);
    } catch (error) {
      console.error(error);
      setSyncError("La synchronisation a échoué. Réessayez plus tard.");
    } finally {
      setSyncInProgress(false);
    }
  }

  async function refreshUniversityData() {
    const [refreshedUniversities, errors] = await Promise.all([
      getUniversities(),
      getUniversityImportErrors(),
    ]);
    setUniversities(refreshedUniversities);
    setUniversityImportErrors(errors);
    return {
      errors,
      universities: refreshedUniversities,
    };
  }

  async function waitForUniversitySyncRefresh(previousFingerprint: string) {
    for (let attempt = 0; attempt < 12; attempt += 1) {
      await delay(700);
      const refreshed = await refreshUniversityData();
      const currentFingerprint = getSyncFingerprint(
        refreshed.universities,
        refreshed.errors,
      );

      if (currentFingerprint !== previousFingerprint) {
        return;
      }
    }
  }

  async function retryImportError(error: RawImport, countryId: number) {
    await retryUniversityImport(error.id, countryId);
    const refreshedUniversities = await getUniversities();
    setUniversities(refreshedUniversities);
    setUniversityImportErrors((items) =>
      items.filter((item) => item.id !== error.id),
    );
  }

  async function ignoreImportError(error: RawImport) {
    await ignoreUniversityImport(error.id);
    setUniversityImportErrors((items) =>
      items.filter((item) => item.id !== error.id),
    );
  }

  return (
    <>
      <ReferenceTabs
        countriesCount={countries.length}
        departmentsCount={departments.length}
        universitiesCount={universities.length}
      />

      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <SearchInput
            onChange={setQuery}
            placeholder="Rechercher dans les referentiels..."
            value={query}
          />
          
        </div>
      </div>

      <div className="space-y-10">
        <div id="pays">
          <ReferenceSection
            title="Pays"
            description="Liste stable des pays et de leur region CTI."
            toolbar={
              <AddButton
                label="Ajouter un pays"
                onClick={() => setModal({ kind: "country" })}
              />
            }
          >
            <CountriesTable
              countries={filteredCountries}
              onDelete={removeCountry}
              onEdit={(country) => setModal({ kind: "country", item: country })}
            />
          </ReferenceSection>
        </div>

        <div id="departements">
          <ReferenceSection
            title="Departements"
            description="Departements pedagogiques utilises dans les parcours et mobilites."
            toolbar={
              <AddButton
                label="Ajouter un departement"
                onClick={() => setModal({ kind: "department" })}
              />
            }
          >
            <DepartmentsTable
              departments={filteredDepartments}
              onDelete={removeDepartment}
              onEdit={(department) =>
                setModal({ kind: "department", item: department })
              }
            />
          </ReferenceSection>
        </div>

        <div id="universites">
          <ReferenceSection
            title="Universites partenaires"
            description="Etablissements partenaires synchronises ou administres manuellement."
            toolbar={
              <div className="flex flex-wrap items-center gap-2">
                <AddButton
                  label="Ajouter une universite"
                  onClick={() => setModal({ kind: "university" })}
                />
                <SyncButton
                  isLoading={syncInProgress}
                  onClick={handleSyncUniversities}
                />
              </div>
            }
          >
            <UniversitiesTable
              countries={countries}
              onDelete={removeUniversity}
              onEdit={(university) =>
                setModal({ kind: "university", item: university })
              }
              universities={filteredUniversities}
            />
            <ImportErrorsPanel
              countries={countries}
              errors={universityImportErrors}
              isBusy={syncInProgress}
              onIgnore={ignoreImportError}
              onRetry={retryImportError}
            />
            {syncError ? (
              <p className="mt-3 text-sm text-red-600">{syncError}</p>
            ) : null}
          </ReferenceSection>
        </div>
      </div>

      {modal ? (
        <Modal
          description="Les modifications sont enregistrees dans les referentiels Django."
          onClose={() => setModal(null)}
          title={`${modal.item ? "Modifier" : "Ajouter"} ${getModalLabel(modal.kind)}`}
        >
          <ReferenceForm
            countries={countries}
            item={modal.item}
            kind={modal.kind}
            onCancel={() => setModal(null)}
            onSubmit={submitReference}
          />
        </Modal>
      ) : null}
    </>
  );
}

function AddButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      className="inline-flex items-center gap-2 rounded-md bg-[#1E3A8A] px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-900"
      onClick={onClick}
      type="button"
    >
      <Plus className="h-4 w-4" aria-hidden="true" />
      {label}
    </button>
  );
}

function SyncButton({
  isLoading,
  onClick,
}: {
  isLoading: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
      onClick={onClick}
      type="button"
      disabled={isLoading}
    >
      {isLoading ? "Synchronisation en cours..." : "Synchroniser MoveON"}
    </button>
  );
}

function getModalLabel(kind: ReferenceFormKind) {
  if (kind === "country") {
    return "un pays";
  }

  if (kind === "department") {
    return "un departement";
  }

  return "une universite";
}

function getSyncFingerprint(
  universities: PartnerUniversity[],
  errors: RawImport[],
) {
  return JSON.stringify({
    errors: errors.map((error) => ({
      id: error.id,
      status: error.status,
      updated_at: error.updated_at,
    })),
    universities: universities.map((university) => ({
      id: university.id,
      last_sync_moveon: university.last_sync_moveon,
      updated_at: university.updated_at,
    })),
  });
}

function delay(milliseconds: number) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}
