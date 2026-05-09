"use client";

import { FormEvent, useState } from "react";

import type { Country, Department, PartnerUniversity } from "@/lib/api/types";
import type {
  CountryPayload,
  DepartmentPayload,
  PartnerUniversityPayload,
} from "@/lib/api/reference-mutations";

export type ReferenceFormKind = "country" | "department" | "university";

type ReferenceFormProps = {
  countries: Country[];
  kind: ReferenceFormKind;
  item?: Country | Department | PartnerUniversity;
  onCancel: () => void;
  onSubmit: (
    payload: CountryPayload | DepartmentPayload | PartnerUniversityPayload,
  ) => Promise<void>;
};

const ctiRegions = [
  { value: "france", label: "France" },
  { value: "europe_hors_france", label: "Europe hors France" },
  { value: "canada_usa", label: "Canada / Etats-Unis" },
  { value: "amerique", label: "Amerique" },
  { value: "asie_moyen_orient", label: "Asie / Moyen-Orient" },
  { value: "afrique", label: "Afrique" },
  { value: "oceanie", label: "Oceanie" },
];

function isCountry(item?: Country | Department | PartnerUniversity): item is Country {
  return Boolean(item && "iso2" in item);
}

function isDepartment(
  item?: Country | Department | PartnerUniversity,
): item is Department {
  return Boolean(item && "code" in item);
}

function isUniversity(
  item?: Country | Department | PartnerUniversity,
): item is PartnerUniversity {
  return Boolean(item && "country_id" in item);
}

export function ReferenceForm({
  countries,
  kind,
  item,
  onCancel,
  onSubmit,
}: ReferenceFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const formData = new FormData(event.currentTarget);

    try {
      if (kind === "country") {
        await onSubmit({
          iso2: String(formData.get("iso2") ?? ""),
          name_fr: String(formData.get("name_fr") ?? ""),
          name_en: String(formData.get("name_en") ?? ""),
          cti_region: String(formData.get("cti_region") ?? ""),
        });
      }

      if (kind === "department") {
        await onSubmit({
          code: String(formData.get("code") ?? ""),
          name: String(formData.get("name") ?? ""),
        });
      }

      if (kind === "university") {
        const moveonId = String(formData.get("moveon_id") ?? "").trim();

        await onSubmit({
          moveon_id: moveonId ? Number(moveonId) : null,
          name: String(formData.get("name") ?? ""),
          short_name: String(formData.get("short_name") ?? ""),
          translated_name: String(formData.get("translated_name") ?? ""),
          erasmus_code: String(formData.get("erasmus_code") ?? ""),
          city: String(formData.get("city") ?? ""),
          url: String(formData.get("url") ?? ""),
          email: String(formData.get("email") ?? ""),
          country_id: Number(formData.get("country_id")),
          last_sync_moveon: null,
        });
      }
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Impossible d'enregistrer la donnee.",
      );
      setIsSubmitting(false);
      return;
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      {kind === "country" ? <CountryFields item={isCountry(item) ? item : undefined} /> : null}
      {kind === "department" ? (
        <DepartmentFields item={isDepartment(item) ? item : undefined} />
      ) : null}
      {kind === "university" ? (
        <UniversityFields
          countries={countries}
          item={isUniversity(item) ? item : undefined}
        />
      ) : null}

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="flex justify-end gap-3 border-t border-gray-200 pt-5">
        <button
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          onClick={onCancel}
          type="button"
        >
          Annuler
        </button>
        <button
          className="rounded-md bg-[#1E3A8A] px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSubmitting}
          type="submit"
        >
          Enregistrer
        </button>
      </div>
    </form>
  );
}

function Field({
  defaultValue,
  label,
  name,
  required = false,
  type = "text",
}: {
  defaultValue?: string | number | null;
  label: string;
  name: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <input
        className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
        defaultValue={defaultValue ?? ""}
        name={name}
        required={required}
        type={type}
      />
    </label>
  );
}

function CountryFields({ item }: { item?: Country }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <Field defaultValue={item?.iso2} label="Code ISO2" name="iso2" required />
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Region CTI</span>
        <select
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
          defaultValue={item?.cti_region ?? "france"}
          name="cti_region"
          required
        >
          {ctiRegions.map((region) => (
            <option key={region.value} value={region.value}>
              {region.label}
            </option>
          ))}
        </select>
      </label>
      <Field defaultValue={item?.name_fr} label="Nom francais" name="name_fr" required />
      <Field defaultValue={item?.name_en} label="Nom anglais" name="name_en" required />
    </div>
  );
}

function DepartmentFields({ item }: { item?: Department }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <Field defaultValue={item?.code} label="Code departement" name="code" required />
      <Field defaultValue={item?.name} label="Intitule" name="name" required />
    </div>
  );
}

function UniversityFields({
  countries,
  item,
}: {
  countries: Country[];
  item?: PartnerUniversity;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <Field defaultValue={item?.moveon_id} label="MoveON ID" name="moveon_id" type="number" />
      <Field defaultValue={item?.name} label="Nom" name="name" required />
      <Field defaultValue={item?.short_name} label="Nom court" name="short_name" />
      <Field
        defaultValue={item?.translated_name}
        label="Nom traduit"
        name="translated_name"
      />
      <Field defaultValue={item?.erasmus_code} label="Code Erasmus" name="erasmus_code" />
      <Field defaultValue={item?.city} label="Ville" name="city" />
      <Field defaultValue={item?.url} label="Site web" name="url" type="url" />
      <Field defaultValue={item?.email} label="Email" name="email" type="email" />
      <label className="block sm:col-span-2">
        <span className="text-sm font-medium text-gray-700">Pays</span>
        <select
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
          defaultValue={item?.country_id ?? countries[0]?.id}
          name="country_id"
          required
        >
          {countries.map((country) => (
            <option key={country.id} value={country.id}>
              {country.name_fr} ({country.iso2})
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
