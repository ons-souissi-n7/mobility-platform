"use client";

import { useState } from "react";
import { AlertTriangle } from "lucide-react";

type ConfirmState = {
  message: string;
  action?: string;
  resolve: (value: boolean) => void;
};

export function useConfirm() {
  const [state, setState] = useState<ConfirmState | null>(null);

  function confirm(message: string, action?: string): Promise<boolean> {
    return new Promise((resolve) => {
      setState({ message, action, resolve });
    });
  }

  function handleConfirm() {
    state?.resolve(true);
    setState(null);
  }

  function handleCancel() {
    state?.resolve(false);
    setState(null);
  }

  const dialog = state ? (
    <ConfirmDialog
      action={state.action}
      message={state.message}
      onCancel={handleCancel}
      onConfirm={handleConfirm}
    />
  ) : null;

  return { confirm, dialog };
}

function ConfirmDialog({
  action = "Supprimer",
  message,
  onCancel,
  onConfirm,
}: {
  action?: string;
  message: string;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 px-4">
      <div className="w-full max-w-sm rounded-lg bg-white shadow-xl">
        <div className="flex items-start gap-4 px-6 pt-6">
          <div className="flex h-10 w-10 flex-none items-center justify-center rounded-full bg-red-50">
            <AlertTriangle className="h-5 w-5 text-red-500" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-gray-900">Confirmer : {action}</h2>
            <p className="mt-1 text-sm text-gray-500">{message}</p>
          </div>
        </div>
        <div className="flex justify-end gap-3 px-6 pb-6 pt-5">
          <button
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            onClick={onCancel}
            type="button"
          >
            Annuler
          </button>
          <button
            className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            onClick={onConfirm}
            type="button"
          >
            {action}
          </button>
        </div>
      </div>
    </div>
  );
}
