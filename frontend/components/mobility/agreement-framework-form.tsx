"use client";

import { FormEvent, useState } from "react";

import type { MobilityCategoryPayload } from "@/lib/api/mobility-mutations";
import type { MobilityCategory } from "@/lib/api/types";

type MobilityCategoryFormProps = {
  item?: MobilityCategory;
  onCancel: () => void;
  onSubmit: (payload: MobilityCategoryPayload) => Promise<void>;
};

export function MobilityCategoryForm({ item, onCancel, onSubmit }: MobilityCategoryFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const formData = new FormData(event.currentTarget);

    try {
      await onSubmit({
        name: String(formData.get("name") ?? "").trim(),
      });
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Impossible d'enregistrer le cadre.",
      );
      setIsSubmitting(false);
      return;
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field defaultValue={item?.name} label="Nom" name="name" required />
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
