"use client";

import { useState } from "react";
import { RefreshCcw } from "lucide-react";

import { useConfirm } from "@/components/ui/confirm-dialog";
import { syncUniversitiesFromMoveon } from "@/lib/api/reference-mutations";

export function MoveOnSyncButton() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const { confirm, dialog: confirmDialog } = useConfirm();

  async function handleClick() {
    if (!await confirm("Lancer la synchronisation des universites depuis MoveON ?", "Synchroniser")) {
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const result = await syncUniversitiesFromMoveon();
      setMessage(result.message ?? "Synchronisation demandee en arriere-plan.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? `Erreur : ${error.message}`
          : "Erreur inconnue lors de la synchronisation.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="flex items-center gap-3">
        <button
          className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={loading}
          onClick={handleClick}
          type="button"
        >
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          {loading ? "Synchronisation..." : "Synchroniser MoveON"}
        </button>
        {message ? (
          <span className="text-sm text-gray-600">{message}</span>
        ) : null}
      </div>
      {confirmDialog}
    </>
  );
}
