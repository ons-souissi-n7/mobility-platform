"use client";

import { useState } from "react";
import type { ReactNode, SubmitEvent } from "react";

import type { IncomingStudentPayload } from "@/lib/api/incoming-mutations";
import type {
  AcademicYear,
  Country,
  Department,
  IncomingStudent,
  Level,
  MobilityCategory,
  Parcours,
  SelectOption,
} from "@/lib/api/types";

export function IncomingStudentForm({
  academicYears,
  countries,
  departments,
  item,
  levels,
  mobilityCategories,
  onCancel,
  onSubmit,
  parcours,
  universities,
}: Readonly<{
  academicYears: AcademicYear[];
  countries: Country[];
  departments: Department[];
  item?: IncomingStudent;
  levels: Level[];
  mobilityCategories: MobilityCategory[];
  onCancel: () => void;
  onSubmit: (payload: IncomingStudentPayload) => Promise<void>;
  parcours: Parcours[];
  universities: SelectOption[];
}>) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [selectedUnivId, setSelectedUnivId] = useState<number | null>(
    item?.origin_university_id ?? null,
  );
  const [univName, setUnivName] = useState(item?.origin_university_name ?? "");
  const [doctoralContinuation, setDoctoralContinuation] = useState(
    item?.doctoral_continuation ?? false,
  );

  function handleUnivSelect(e: React.ChangeEvent<HTMLSelectElement>) {
    const id = e.target.value ? Number(e.target.value) : null;
    setSelectedUnivId(id);
    if (id) {
      const found = universities.find((u) => u.id === id);
      if (found) setUnivName(found.label);
    }
  }

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const fd = new FormData(event.currentTarget);
    const get = (name: string) => String(fd.get(name) ?? "").trim();
    const getNum = (name: string) => {
      const v = get(name);
      return v ? Number(v) : null;
    };

    const payload: IncomingStudentPayload = {
      academic_year_id: Number(get("academic_year_id")),
      department_id: getNum("department_id"),
      civility: get("civility"),
      last_name: get("last_name"),
      first_name: get("first_name"),
      country_id: getNum("country_id"),
      origin_university_id: selectedUnivId,
      origin_university_name: univName,
      birth_date: get("birth_date") || null,
      mobility_category_id: getNum("mobility_category_id"),
      personal_email: get("personal_email"),
      n7_email: get("n7_email"),
      duration: get("duration"),
      level_id: getNum("level_id"),
      parcours_id: getNum("parcours_id"),
      remarks: get("remarks"),
      internship_info: get("internship_info"),
      diploma_info: get("diploma_info"),
      doctoral_continuation: doctoralContinuation,
    };

    try {
      await onSubmit(payload);
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Impossible d'enregistrer l'étudiant.",
      );
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      {/* Identité */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Select defaultValue={item?.academic_year_id} label="Année universitaire" name="academic_year_id" required>
          <option value="">Choisir une année</option>
          {academicYears.map((y) => (
            <option key={y.id} value={y.id}>{y.label}</option>
          ))}
        </Select>
        <Select defaultValue={item?.civility ?? ""} label="Civilité" name="civility">
          <option value="">—</option>
          <option value="M.">M.</option>
          <option value="Mme">Mme</option>
        </Select>
        <Select defaultValue={item?.department_id ?? ""} label="Département N7" name="department_id">
          <option value="">—</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>{d.code} – {d.name}</option>
          ))}
        </Select>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field defaultValue={item?.last_name} label="Nom" name="last_name" required />
        <Field defaultValue={item?.first_name} label="Prénom" name="first_name" required />
      </div>

      {/* Origine */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Origine</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select defaultValue={item?.country_id ?? ""} label="Pays" name="country_id">
            <option value="">—</option>
            {countries.map((c) => (
              <option key={c.id} value={c.id}>{c.name_fr}</option>
            ))}
          </Select>
          <label className="block">
            <span className="text-sm font-medium text-gray-700">Université partenaire (liste)</span>
            <select
              className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
              onChange={handleUnivSelect}
              value={selectedUnivId ?? ""}
            >
              <option value="">— université hors liste —</option>
              {universities.map((u) => (
                <option key={u.id} value={u.id}>{u.label}</option>
              ))}
            </select>
          </label>
          <label className="block sm:col-span-2">
            <span className="text-sm font-medium text-gray-700">Nom université d&apos;origine</span>
            <input
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
              onChange={(e) => { setSelectedUnivId(null); setUnivName(e.target.value); }}
              placeholder="Saisir manuellement si absente de la liste"
              type="text"
              value={univName}
            />
          </label>
        </div>
      </div>

      {/* Mobilité */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Mobilité</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select defaultValue={item?.mobility_category_id ?? ""} label="Cadre de mobilité" name="mobility_category_id">
            <option value="">—</option>
            {mobilityCategories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </Select>
          <Field defaultValue={item?.duration} label="Durée" name="duration" />
          <Select defaultValue={item?.level_id ?? ""} label="Niveau" name="level_id">
            <option value="">—</option>
            {levels.map((l) => (
              <option key={l.id} value={l.id}>{l.code} – {l.name}</option>
            ))}
          </Select>
          <Select defaultValue={item?.parcours_id ?? ""} label="Parcours" name="parcours_id">
            <option value="">—</option>
            {parcours.map((p) => (
              <option key={p.id} value={p.id}>{p.code} – {p.label}</option>
            ))}
          </Select>
        </div>
      </div>

      {/* Contact */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Contact</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field defaultValue={item?.birth_date ?? ""} label="Date de naissance" name="birth_date" type="date" />
          <Field defaultValue={item?.personal_email} label="Email personnel" name="personal_email" type="email" />
          <Field defaultValue={item?.n7_email} label="Email ENSEEIHT" name="n7_email" type="email" />
        </div>
      </div>

      {/* Informations complémentaires */}
      <div className="border-t border-gray-100 pt-4">
        <p className="mb-3 text-sm font-semibold text-gray-700">Informations complémentaires</p>
        <div className="space-y-4">
          <TextArea defaultValue={item?.remarks} label="Remarques" name="remarks" />
          <TextArea defaultValue={item?.internship_info} label="Stage" name="internship_info" />
          <TextArea defaultValue={item?.diploma_info} label="Diplôme" name="diploma_info" />
          <label className="flex cursor-pointer items-center gap-2">
            <input
              checked={doctoralContinuation}
              className="h-4 w-4 rounded border-gray-300 text-[#1E3A8A] focus:ring-[#1E3A8A]"
              onChange={(e) => setDoctoralContinuation(e.target.checked)}
              type="checkbox"
            />
            <span className="text-sm font-medium text-gray-700">Poursuite en doctorat</span>
          </label>
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
  name,
  required = false,
  type = "text",
}: Readonly<{
  defaultValue?: string | null;
  label: string;
  name: string;
  required?: boolean;
  type?: string;
}>) {
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

function Select({
  children,
  defaultValue,
  label,
  name,
  required = false,
}: Readonly<{
  children: ReactNode;
  defaultValue?: number | string | null;
  label: string;
  name: string;
  required?: boolean;
}>) {
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
