"use client";

import { SubmitEvent, useState } from "react";

import type { LevelPayload } from "@/lib/api/reference-mutations";
import type { Level } from "@/lib/api/types";

export function LevelForm({
  item,
  onCancel,
  onSubmit,
}: Readonly<{
  item?: Level;
  onCancel: () => void;
  onSubmit: (payload: LevelPayload) => Promise<void>;
}>) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const payload: LevelPayload = {
      code: String(formData.get("code") ?? "").trim().toUpperCase(),
      name: String(formData.get("name") ?? "").trim(),
      pegase_id: item?.pegase_id ?? null,
      last_sync_pegase: item?.last_sync_pegase ?? null,
      is_terminal: formData.get("is_terminal") === "on",
    };

    if (!payload.code) {
      setError("Le code est obligatoire.");
      setIsSubmitting(false);
      return;
    }

    try {
      await onSubmit(payload);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Impossible d'enregistrer le niveau.",
      );
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Code *</span>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            defaultValue={item?.code ?? ""}
            name="code"
            placeholder="Ex: M2, L3, ING"
            required
            type="text"
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Intitule</span>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
            defaultValue={item?.name ?? ""}
            name="name"
            placeholder="Ex: Master 2 (Bac+5)"
            type="text"
          />
        </label>
      </div>

      <div className="flex items-start gap-3 rounded-md border border-amber-200 bg-amber-50 p-3">
        <input
          className="mt-0.5 h-4 w-4 rounded accent-[#1E3A8A]"
          defaultChecked={item?.is_terminal ?? false}
          id="is_terminal"
          name="is_terminal"
          type="checkbox"
        />
        <label className="text-sm text-gray-700" htmlFor="is_terminal">
          <span className="font-medium">Niveau terminal (diplômant)</span>
          <span className="mt-0.5 block text-xs text-gray-500">
            Cocher si c&apos;est le dernier niveau du cursus.
            Les étudiants inscrits à ce niveau servent de cohorte pour le rapport CTI.
          </span>
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
