"use client";

import { useState } from "react";
import type { FormEvent, ReactNode } from "react";

import type { InternshipPayload } from "@/lib/api/internship-mutations";
import type { AcademicYear, Country, Internship } from "@/lib/api/types";

const INTERNSHIP_TYPES = ["Stage", "Stage 1A", "Stage 2A", "Stage 3A"];

export function InternshipForm({
  item,
  countries,
  academicYears,
  onCancel,
  onSubmit,
}: {
  item?: Internship;
  countries: Country[];
  academicYears: AcademicYear[];
  onCancel: () => void;
  onSubmit: (payload: InternshipPayload) => Promise<void>;
}) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Student search: user types INE – Nom; we track student_id manually
  // For simplicity: store raw student_id as text for now (user enters numeric ID)
  // The field shows "student_id - student_name" for existing items
  const [studentSearch, setStudentSearch] = useState(
    item ? `${item.student_ine} – ${item.student_name}` : "",
  );
  const [studentId, setStudentId] = useState<number | null>(item?.student_id ?? null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!studentId) {
      setError("Veuillez renseigner un étudiant (ID).");
      return;
    }

    setIsSubmitting(true);
    const formData = new FormData(event.currentTarget);

    const payload: InternshipPayload = {
      student_id: studentId,
      company_name: getString(formData, "company_name"),
      country_id: formData.get("country_id") ? Number(formData.get("country_id")) : null,
      city: getString(formData, "city"),
      title: getString(formData, "title"),
      internship_type: getString(formData, "internship_type"),
      status_code: getString(formData, "status_code"),
      status_label: getString(formData, "status_label"),
      start_date: getString(formData, "start_date") || null,
      end_date: getString(formData, "end_date") || null,
      weeks_in_company: formData.get("weeks_in_company")
        ? Number(formData.get("weeks_in_company"))
        : null,
      school_tutor: getString(formData, "school_tutor"),
      company_tutor: getString(formData, "company_tutor"),
      academic_year_id: formData.get("academic_year_id")
        ? Number(formData.get("academic_year_id"))
        : null,
    };

    try {
      await onSubmit(payload);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Impossible d'enregistrer le stage.",
      );
      setIsSubmitting(false);
    }
  }

  // When user edits student field: try to parse "ID" or "ID – Nom"
  function handleStudentChange(raw: string) {
    setStudentSearch(raw);
    const trimmed = raw.trim();
    const match = /^(\d+)/.exec(trimmed);
    if (match) {
      setStudentId(Number(match[1]));
    } else {
      setStudentId(null);
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      {/* Étudiant */}
      <div className="border-b border-gray-100 pb-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Étudiant</p>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">
            INE – Nom{" "}
            <span className="font-normal text-gray-400">(saisir l&apos;ID numérique ou INE – Nom)</span>
          </span>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            placeholder="ex: 12345 ou INE – Nom Prénom"
            value={studentSearch}
            onChange={(e) => handleStudentChange(e.target.value)}
          />
          {studentId ? (
            <p className="mt-0.5 text-xs text-emerald-600">ID étudiant : {studentId}</p>
          ) : (
            <p className="mt-0.5 text-xs text-gray-400">Entrez l&apos;ID numérique de l&apos;étudiant</p>
          )}
        </label>
      </div>

      {/* Informations générales */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field
          defaultValue={item?.company_name}
          label="Raison sociale"
          name="company_name"
          required
        />
        <Select defaultValue={item?.country_id ?? ""} label="Pays" name="country_id">
          <option value="">Aucun pays</option>
          {[...countries]
            .sort((a, b) => a.name_fr.localeCompare(b.name_fr))
            .map((c) => (
              <option key={c.id} value={c.id}>
                {c.name_fr}
              </option>
            ))}
        </Select>
        <Field defaultValue={item?.city} label="Ville" name="city" />
        <Select
          defaultValue={item?.internship_type ?? ""}
          label="Type de stage"
          name="internship_type"
        >
          <option value="">Choisir un type</option>
          {INTERNSHIP_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </Select>
        <Field defaultValue={item?.title} label="Titre du stage" name="title" />
        <Select
          defaultValue={item?.academic_year_id ?? ""}
          label="Année académique"
          name="academic_year_id"
        >
          <option value="">Aucune année</option>
          {[...academicYears]
            .sort((a, b) => b.start_date.localeCompare(a.start_date))
            .map((y) => (
              <option key={y.id} value={y.id}>
                {y.label}
              </option>
            ))}
        </Select>
      </div>

      {/* Statut */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Statut</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field defaultValue={item?.status_code} label="Code statut" name="status_code" />
          <Field defaultValue={item?.status_label} label="Libellé statut" name="status_label" />
        </div>
      </div>

      {/* Dates */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Période</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Field
            defaultValue={item?.start_date ?? ""}
            label="Date de début"
            name="start_date"
            type="date"
          />
          <Field
            defaultValue={item?.end_date ?? ""}
            label="Date de fin"
            name="end_date"
            type="date"
          />
          <Field
            defaultValue={item?.weeks_in_company != null ? String(item.weeks_in_company) : ""}
            label="Nb semaines"
            min="0"
            name="weeks_in_company"
            type="number"
          />
        </div>
      </div>

      {/* Tuteurs */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Tuteurs</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field
            defaultValue={item?.school_tutor}
            label="Tuteur pédagogique"
            name="school_tutor"
          />
          <Field
            defaultValue={item?.company_tutor}
            label="Tuteur entreprise"
            name="company_tutor"
          />
        </div>
      </div>

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
