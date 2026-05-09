"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import { CountriesTable } from "@/components/references/countries-table";
import { DepartmentsTable } from "@/components/references/departments-table";
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
  updateCountry,
  updateDepartment,
  updateUniversity,
  type CountryPayload,
  type DepartmentPayload,
  type PartnerUniversityPayload,
} from "@/lib/api/reference-mutations";
import type { Country, Department, PartnerUniversity } from "@/lib/api/types";

type ReferencesWorkspaceProps = {
  countries: Country[];
  departments: Department[];
  universities: PartnerUniversity[];
};

export function ReferencesWorkspace({
  countries: initialCountries,
  departments: initialDepartments,
  universities: initialUniversities,
}: ReferencesWorkspaceProps) {
  const [countries, setCountries] = useState(initialCountries);
  const [departments, setDepartments] = useState(initialDepartments);
  const [universities, setUniversities] = useState(initialUniversities);
  const [query, setQuery] = useState("");
  const [modal, setModal] = useState<{
    kind: ReferenceFormKind;
    item?: Country | Department | PartnerUniversity;
  } | null>(null);
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
              <AddButton
                label="Ajouter une universite"
                onClick={() => setModal({ kind: "university" })}
              />
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

function getModalLabel(kind: ReferenceFormKind) {
  if (kind === "country") {
    return "un pays";
  }

  if (kind === "department") {
    return "un departement";
  }

  return "une universite";
}
