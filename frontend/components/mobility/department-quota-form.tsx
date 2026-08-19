"use client";

import { SubmitEvent, useState } from "react";
import type { ReactNode } from "react";

import type { AgreementYearDepartmentPayload } from "@/lib/api/mobility-mutations";
import type { AgreementYear, AgreementYearDepartment, Department } from "@/lib/api/types";

export function DepartmentQuotaForm({
  agreementYear,
  constrainedDepartments,
  existingDeptCount,
  item,
  onCancel,
  onSubmit,
}: Readonly<{
  agreementYear: AgreementYear;
  constrainedDepartments: Department[];
  existingDeptCount: number;
  item?: AgreementYearDepartment;
  onCancel: () => void;
  onSubmit: (payload: AgreementYearDepartmentPayload) => Promise<void>;
}>) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const newTotal = existingDeptCount + 1;
  const autoPlaces = Math.round(agreementYear.n7_places / Math.max(1, newTotal));

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);

    const payload: AgreementYearDepartmentPayload = {
      agreement_year_id: agreementYear.id,
      department_id: Number(formData.get("department_id") || 0),
      estimated_places: item ? Number(formData.get("estimated_places") || 0) : autoPlaces,
    };

    try {
      await onSubmit(payload);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Impossible d'enregistrer le quota département.",
      );
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <Select defaultValue={item?.department_id} label="Département" name="department_id" required>
        <option value="">Choisir un département</option>
        {constrainedDepartments.map((department) => (
          <option key={department.id} value={department.id}>
            {department.code} — {department.name}
          </option>
        ))}
      </Select>

      {item ? (
        <Field
          defaultValue={String(item.estimated_places)}
          label="Places estimées"
          min="0"
          name="estimated_places"
          required
          type="number"
        />
      ) : (
        <div className="rounded-md border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800">
          Places attribuées automatiquement :{" "}
          <span className="font-semibold">{autoPlaces}</span>
          {" "}— répartition de {agreementYear.n7_places} place{agreementYear.n7_places > 1 ? "s" : ""} N7 sur{" "}
          {newTotal} département{newTotal > 1 ? "s" : ""}.
        </div>
      )}

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
}: Readonly<{
  defaultValue?: string | null;
  label: string;
  min?: string;
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
