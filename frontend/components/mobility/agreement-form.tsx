"use client";

import { useState } from "react";
import type { FormEvent, ReactNode } from "react";

import type { AgreementPayload } from "@/lib/api/mobility-mutations";
import type { Agreement, MobilityCategory, Department, Level, PartnerUniversity } from "@/lib/api/types";

export type AgreementFullPayload = AgreementPayload & {
  department_ids: number[];
  level_ids: number[];
  n7_places: number | null;
  source_total_places: number | null;
  source_institutions: string;
};

export function AgreementForm({
  departments,
  frameworks,
  item,
  mobilityLevels,
  onCancel,
  onSubmit,
  universities,
}: {
  departments: Department[];
  frameworks: MobilityCategory[];
  item?: Agreement;
  mobilityLevels: Level[];
  onCancel: () => void;
  onSubmit: (payload: AgreementFullPayload) => Promise<void>;
  universities: PartnerUniversity[];
}) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedDeptIds, setSelectedDeptIds] = useState<number[]>([]);
  const [selectedLevelIds, setSelectedLevelIds] = useState<number[]>([]);

  const isCreateMode = !item;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const n7PlacesRaw = getString(formData, "n7_places");
    const inpPlacesRaw = getString(formData, "source_total_places");
    const frameworkRefRaw = formData.get("framework_ref_id");
    const n7Places = n7PlacesRaw ? Number(n7PlacesRaw) : null;
    const inpPlaces = inpPlacesRaw ? Number(inpPlacesRaw) : null;

    if (n7Places !== null && inpPlaces !== null && n7Places > inpPlaces) {
      setError("Le quota N7 ne peut pas etre superieur au quota INP.");
      setIsSubmitting(false);
      return;
    }

    const payload: AgreementFullPayload = {
      name: getString(formData, "name"),
      partner_university_id: Number(formData.get("partner_university_id") || 0),
      framework_ref_id: frameworkRefRaw ? Number(frameworkRefRaw) : null,
      is_active: formData.get("is_active") === "on",
      remarks: getString(formData, "remarks"),
      department_ids: isCreateMode ? selectedDeptIds : [],
      level_ids: isCreateMode ? selectedLevelIds : [],
      n7_places: n7Places,
      source_total_places: inpPlaces,
      source_institutions: isCreateMode ? getString(formData, "source_institutions") : "",
    };

    try {
      await onSubmit(payload);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Impossible d'enregistrer l'accord.",
      );
      setIsSubmitting(false);
    }
  }

  function toggleDept(id: number) {
    setSelectedDeptIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id],
    );
  }

  function toggleLevel(id: number) {
    setSelectedLevelIds((prev) =>
      prev.includes(id) ? prev.filter((l) => l !== id) : [...prev, id],
    );
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field defaultValue={item?.name} label="Nom de l'accord" name="name" required />
        <Select
          defaultValue={item?.partner_university_id}
          label="Universite partenaire"
          name="partner_university_id"
          required
        >
          <option value="">Choisir un partenaire</option>
          {universities.map((university) => (
            <option key={university.id} value={university.id}>
              {university.name}
            </option>
          ))}
        </Select>
        <Select
          defaultValue={item?.framework_ref_id ?? ""}
          label="Cadre de mobilite"
          name="framework_ref_id"
        >
          <option value="">Aucun cadre</option>
          {frameworks.filter((fw) => fw.is_active).map((fw) => (
            <option key={fw.id} value={fw.id}>
              {fw.name}
            </option>
          ))}
        </Select>
      </div>

      {isCreateMode ? (
        <>
          <div className="border-t border-gray-100 pt-4">
            <p className="mb-3 text-sm font-semibold text-gray-700">
              Departements concernes
              <span className="ml-1 font-normal text-gray-400">(optionnel — vide = tous)</span>
            </p>
            <div className="flex flex-wrap gap-2">
              {departments.map((dept) => (
                <button
                  key={dept.id}
                  className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                    selectedDeptIds.includes(dept.id)
                      ? "border-[#1E3A8A] bg-[#1E3A8A] text-white"
                      : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                  }`}
                  onClick={() => toggleDept(dept.id)}
                  type="button"
                >
                  {dept.code}
                </button>
              ))}
              {departments.length === 0 ? (
                <p className="text-xs italic text-gray-400">Aucun departement disponible</p>
              ) : null}
            </div>
          </div>

          <div className="border-t border-gray-100 pt-4">
            <p className="mb-3 text-sm font-semibold text-gray-700">
              Niveaux concernes
              <span className="ml-1 font-normal text-gray-400">(optionnel — vide = tous)</span>
            </p>
            <div className="flex flex-wrap gap-2">
              {mobilityLevels
                .filter((l) => l.is_active)
                .map((level) => (
                  <button
                    key={level.id}
                    className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                      selectedLevelIds.includes(level.id)
                        ? "border-purple-600 bg-purple-600 text-white"
                        : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                    }`}
                    onClick={() => toggleLevel(level.id)}
                    type="button"
                  >
                    {level.code}
                  </button>
                ))}
              {mobilityLevels.filter((l) => l.is_active).length === 0 ? (
                <p className="text-xs italic text-gray-400">Aucun niveau disponible</p>
              ) : null}
            </div>
          </div>

          <div className="border-t border-gray-100 pt-4">
            <p className="mb-3 text-sm font-semibold text-gray-700">
              Quota de places
              <span className="ml-1 font-normal text-gray-400">(optionnel — pour l&apos;annee courante)</span>
            </p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Field label="Places N7" min="0" name="n7_places" type="number" />
              <Field label="Places INP total" min="0" name="source_total_places" type="number" />
              <Field
                label="Etablissements internes"
                name="source_institutions"
              />
            </div>
          </div>
        </>
      ) : null}

      <label className="inline-flex items-center gap-2 text-sm font-medium text-gray-700">
        <input
          className="h-4 w-4 rounded border-gray-300 text-[#1E3A8A]"
          defaultChecked={item?.is_active ?? true}
          name="is_active"
          type="checkbox"
        />
        Accord actif
      </label>

      <TextArea defaultValue={item?.remarks} label="Remarques" name="remarks" />

      {error ? <ErrorBox message={error} /> : null}

      <FormActions isSubmitting={isSubmitting} onCancel={onCancel} />
    </form>
  );
}

function Field({
  defaultValue,
  label,
  min,
  name,
  required = false,
  type = "text",
}: {
  defaultValue?: string | null;
  label: string;
  min?: string;
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
        min={min}
        name={name}
        required={required}
        type={type}
      />
    </label>
  );
}

function Select({
  children,
  defaultValue,
  label,
  name,
  required = false,
}: {
  children: ReactNode;
  defaultValue?: number | string | null;
  label: string;
  name: string;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <select
        className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
        defaultValue={defaultValue ?? ""}
        name={name}
        required={required}
      >
        {children}
      </select>
    </label>
  );
}

function TextArea({
  defaultValue,
  label,
  name,
}: {
  defaultValue?: string | null;
  label: string;
  name: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <textarea
        className="mt-1 min-h-20 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
        defaultValue={defaultValue ?? ""}
        name={name}
      />
    </label>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {message}
    </div>
  );
}

function FormActions({
  isSubmitting,
  onCancel,
}: {
  isSubmitting: boolean;
  onCancel: () => void;
}) {
  return (
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
  );
}

function getString(formData: FormData, name: string) {
  return String(formData.get(name) ?? "").trim();
}
