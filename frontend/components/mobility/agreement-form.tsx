"use client";

import { useState } from "react";
import type { FormEvent, ReactNode } from "react";

import type { AgreementPayload } from "@/lib/api/mobility-mutations";
import type { Agreement, Department, Level, MobilityCategory, PartnerUniversity } from "@/lib/api/types";

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
  onSubmit: (payload: AgreementPayload) => Promise<void>;
  universities: PartnerUniversity[];
}) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedDeptIds, setSelectedDeptIds] = useState<number[]>(() => item?.department_ids ?? []);
  const [selectedLevelIds, setSelectedLevelIds] = useState<number[]>(() => item?.level_ids ?? []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const inpPlaces = Number(getString(formData, "inp_total_places") || "0");

    const payload: AgreementPayload = {
      name: getString(formData, "name"),
      partner_university_id: Number(formData.get("partner_university_id") || 0),
      category_id: formData.get("category_id") ? Number(formData.get("category_id")) : null,
      direction: getString(formData, "direction") || "unknown",
      valid_from: getString(formData, "valid_from") || null,
      valid_until: getString(formData, "valid_until") || null,
      inp_total_places: inpPlaces,
      inp_institutions: getString(formData, "inp_institutions"),
      remarks: getString(formData, "remarks"),
      level_ids: selectedLevelIds,
      department_ids: selectedDeptIds,
    };

    try {
      await onSubmit(payload);
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Impossible d'enregistrer l'accord.",
      );
      setIsSubmitting(false);
    }
  }

  function toggleDept(id: number) {
    setSelectedDeptIds((prev) => prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]);
  }

  function toggleLevel(id: number) {
    setSelectedLevelIds((prev) => prev.includes(id) ? prev.filter((l) => l !== id) : [...prev, id]);
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      {/* Informations générales */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field defaultValue={item?.name} label="Nom de l'accord" name="name" required />
        <Select defaultValue={item?.partner_university_id} label="Université partenaire" name="partner_university_id" required>
          <option value="">Choisir un partenaire</option>
          {universities.map((u) => (
            <option key={u.id} value={u.id}>{u.name}</option>
          ))}
        </Select>
        <Select defaultValue={item?.category_id ?? ""} label="Cadre de mobilité" name="category_id">
          <option value="">Aucun cadre</option>
          {frameworks.map((fw) => (
            <option key={fw.id} value={fw.id}>{fw.name}</option>
          ))}
        </Select>
        <Select defaultValue={item?.direction ?? "unknown"} label="Direction" name="direction" required>
          <option value="unknown">Non précisé</option>
          <option value="outgoing">Sortant (N7 → Partenaire)</option>
          <option value="incoming">Entrant (Partenaire → N7)</option>
          <option value="both">Les deux</option>
        </Select>
      </div>

      {/* Validité */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Période de validité</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Field defaultValue={item?.valid_from ?? ""} label="Date de début" name="valid_from" type="date" />
          <Field defaultValue={item?.valid_until ?? ""} label="Date de fin" name="valid_until" type="date" />
        </div>
      </div>

      {/* Quota INP */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Quota INP global</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field
            defaultValue={String(item?.inp_total_places ?? 0)}
            label="Places INP total"
            min="0"
            name="inp_total_places"
            type="number"
          />
          <Field
            defaultValue={item?.inp_institutions ?? ""}
            label="Établissements partageant l'accord"
            name="inp_institutions"
          />
        </div>
      </div>

      {/* Contraintes niveaux */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">
          Niveaux autorisés
          <span className="ml-1 font-normal text-gray-400">(vide = tous)</span>
        </p>
        <div className="flex flex-wrap gap-2">
          {mobilityLevels.map((level) => (
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
          {mobilityLevels.length === 0 && (
            <p className="text-xs italic text-gray-400">Aucun niveau disponible</p>
          )}
        </div>
      </div>

      {/* Contraintes départements */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">
          Départements éligibles
          <span className="ml-1 font-normal text-gray-400">(vide = tous)</span>
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
          {departments.length === 0 && (
            <p className="text-xs italic text-gray-400">Aucun département disponible</p>
          )}
        </div>
      </div>

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

function TextArea({ defaultValue, label, name }: { defaultValue?: string | null; label: string; name: string }) {
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

function FormActions({ isSubmitting, onCancel }: { isSubmitting: boolean; onCancel: () => void }) {
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
