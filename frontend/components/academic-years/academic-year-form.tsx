"use client";

import { FormEvent, useState } from "react";

import type { AcademicYearPayload } from "@/lib/api/academic-year-mutations";
import type { AcademicYear } from "@/lib/api/types";

type AcademicYearFormProps = {
  item?: AcademicYear;
  onCancel: () => void;
  onSubmit: (payload: AcademicYearPayload) => Promise<void>;
};

export function AcademicYearForm({
  item,
  onCancel,
  onSubmit,
}: AcademicYearFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const payload: AcademicYearPayload = {
      label: String(formData.get("label") ?? ""),
      start_date: String(formData.get("start_date") ?? ""),
      end_date: String(formData.get("end_date") ?? ""),
      wishes_open_date: getOptionalDate(formData, "wishes_open_date"),
      wishes_close_date: getOptionalDate(formData, "wishes_close_date"),
      gpa_freeze_date: getOptionalDate(formData, "gpa_freeze_date"),
      results_publication_date: getOptionalDate(
        formData,
        "results_publication_date",
      ),
    };

    try {
      await onSubmit(payload);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Impossible d'enregistrer l'annee universitaire.",
      );
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field defaultValue={item?.label} label="Libelle" name="label" required />
        <Field
          defaultValue={item?.start_date}
          label="Date de debut"
          name="start_date"
          required
          type="date"
        />
        <Field
          defaultValue={item?.end_date}
          label="Date de fin"
          name="end_date"
          required
          type="date"
        />
        <Field
          defaultValue={item?.wishes_open_date}
          label="Ouverture des voeux"
          name="wishes_open_date"
          type="date"
        />
        <Field
          defaultValue={item?.wishes_close_date}
          label="Fermeture des voeux"
          name="wishes_close_date"
          type="date"
        />
        <Field
          defaultValue={item?.gpa_freeze_date}
          label="Gel des moyennes"
          name="gpa_freeze_date"
          type="date"
        />
        <Field
          defaultValue={item?.results_publication_date}
          label="Publication des resultats"
          name="results_publication_date"
          type="date"
        />
      </div>

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
  defaultValue?: string | null;
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

function getOptionalDate(formData: FormData, name: string) {
  const value = String(formData.get(name) ?? "").trim();
  return value || null;
}
