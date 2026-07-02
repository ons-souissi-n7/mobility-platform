"use client";

import { AlertTriangle, ChevronDown, ChevronUp, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { acknowledgeAlert, fetchUnreadAlerts } from "@/lib/api/alerts";
import type { SystemAlert } from "@/lib/api/types";

export function AlertBanner() {
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [collapsed, setCollapsed] = useState(false);

  const load = useCallback(() => {
    fetchUnreadAlerts()
      .then(setAlerts)
      .catch(() => {});
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 60_000);
    return () => clearInterval(id);
  }, [load]);

  // Ferme pour cette session uniquement (réapparaît au reload)
  const closeSession = useCallback((id: number) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }, []);

  // Acquittement permanent pour cet utilisateur (ne réapparaît plus)
  const acknowledge = useCallback(async (id: number) => {
    try {
      await acknowledgeAlert(id);
    } catch {}
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }, []);

  if (alerts.length === 0) return null;

  const hasError = alerts.some((a) => a.level === "error");

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 max-w-[calc(100vw-2rem)] rounded-lg shadow-xl">
      {/* Header */}
      <button
        type="button"
        onClick={() => setCollapsed((v) => !v)}
        className={`flex w-full items-center justify-between gap-2 rounded-t-lg px-3 py-2 text-white ${
          hasError ? "bg-red-600 hover:bg-red-700" : "bg-amber-500 hover:bg-amber-600"
        } transition-colors`}
      >
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span className="text-sm font-semibold">
            {alerts.length} alerte{alerts.length > 1 ? "s" : ""} système
          </span>
        </div>
        {collapsed ? (
          <ChevronUp className="h-4 w-4 flex-shrink-0" />
        ) : (
          <ChevronDown className="h-4 w-4 flex-shrink-0" />
        )}
      </button>

      {/* Alerts list */}
      {!collapsed && (
        <div
          className={`max-h-[28rem] overflow-y-auto rounded-b-lg border bg-white divide-y ${
            hasError ? "border-red-200" : "border-amber-200"
          }`}
        >
          {alerts.map((alert) => {
            const isError = alert.level === "error";
            return (
              <div key={alert.id} className="p-3 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <span
                    className={`text-sm font-semibold leading-snug ${
                      isError ? "text-red-700" : "text-amber-700"
                    }`}
                  >
                    {alert.title}
                  </span>
                  <button
                    type="button"
                    onClick={() => closeSession(alert.id)}
                    className="flex-shrink-0 rounded p-0.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                    aria-label="Masquer pour cette session"
                    title="Masquer jusqu'au prochain rechargement"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">{alert.message}</p>
                <button
                  type="button"
                  onClick={() => acknowledge(alert.id)}
                  className={`text-xs font-medium px-2 py-1 rounded transition-colors ${
                    isError
                      ? "bg-red-50 text-red-700 hover:bg-red-100"
                      : "bg-amber-50 text-amber-700 hover:bg-amber-100"
                  }`}
                >
                  J&apos;ai pris note
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
