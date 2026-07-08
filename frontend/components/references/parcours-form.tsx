"use client";

import { type FormEvent, useState } from "react";

import type { ParcoursPayload } from "@/lib/api/reference-mutations";
import type { Department, Parcours } from "@/lib/api/types";

export function ParcoursForm({
  item,
  departments,
  onCancel,
  onSubmit,
}: {
  item?: Parcours;
  departments: Department[];
  onCancel: () => void;
  onSubmit: (payload: ParcoursPayload) => Promise<void>;
}) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const departmentId = Number(formData.get("department_id"));
    const code = String(formData.get("code") ?? "").trim();
    const label = String(formData.get("label") ?? "").trim();

    if (!departmentId) {
      setError("Le departement est obligatoire.");
      setIsSubmitting(false);
      return;
    }
    if (!code) {
      setError("Le code est obligatoire.");
      setIsSubmitting(false);
      return;
    }
    if (!label) {
      setError("L'intitule est obligatoire.");
      setIsSubmitting(false);
      return;
    }

    try {
      await onSubmit({ department_id: departmentId, code, label });
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Impossible d'enregistrer le parcours.",
      );
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Département *</span>
        <select
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
          defaultValue={item?.department_id ?? ""}
          name="department_id"
          required
        >
          <option value="">— Choisir un departement —</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.code} — {d.name}
            </option>
          ))}
        </select>
      </label>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Code *</span>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            defaultValue={item?.code ?? ""}
            name="code"
            placeholder="Ex: SN-IA, 3EA-EEA"
            required
            type="text"
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Intitule *</span>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            defaultValue={item?.label ?? ""}
            name="label"
            placeholder="Ex: Intelligence Artificielle"
            required
            type="text"
          />
        </label>
      </div>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="flex justify-end gap-3 border-t border-gray-200 pt-4">
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
