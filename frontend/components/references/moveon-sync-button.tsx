"use client";

import { useState } from "react";
import { RefreshCcw } from "lucide-react";

import { syncUniversitiesFromMoveon } from "@/lib/api/reference-mutations";

export function MoveOnSyncButton() {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    if (!window.confirm("Lancer la synchronisation des universites depuis MoveON ?")) {
      return;
    }

    setLoading(true);

    try {
      const result = await syncUniversitiesFromMoveon();
      window.alert(result.message ?? "Synchronisation demandée en arrière-plan.");
    } catch (error) {
      window.alert(
        error instanceof Error
          ? `Erreur: ${error.message}`
          : "Erreur inconnue lors de la synchronisation.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
      type="button"
      onClick={handleClick}
      disabled={loading}
    >
      <RefreshCcw className="h-4 w-4" aria-hidden="true" />
      {loading ? "Synchronisation..." : "Synchroniser MoveON"}
    </button>
  );
}
