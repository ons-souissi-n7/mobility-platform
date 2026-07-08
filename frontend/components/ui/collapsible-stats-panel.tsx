"use client";

import { type ReactNode } from "react";
import { BarChart2, ChevronDown, ChevronRight } from "lucide-react";

export type StatPanelRow = {
  dimension: string;
  department_code?: string | null;
  department_name?: string | null;
  academic_year_label?: string;
  count: number;
};

export type StatPanelTable = {
  heading: string;
  dimensionLabel: string;
  rows: StatPanelRow[];
  showYear?: boolean;
};

type Props =
  | {
      tables: StatPanelTable[];
      children?: never;
      isLoading?: boolean;
      isOpen: boolean;
      onToggle: () => void;
    }
  | {
      tables?: never;
      children: ReactNode;
      isLoading?: never;
      isOpen: boolean;
      onToggle: () => void;
    };

export function CollapsibleStatsPanel({ tables, children, isLoading = false, isOpen, onToggle }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <button
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-gray-800 hover:bg-gray-50"
        onClick={onToggle}
        type="button"
      >
        <span className="flex items-center gap-2">
          <BarChart2 className="h-4 w-4 text-gray-500" />
          Statistiques
        </span>
        {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>

      {isOpen && (
        <div className="border-t border-gray-100">
          {children ?? (
            <div className="p-4 space-y-6">
              {isLoading && (
                <p className="text-sm text-gray-400 text-center">Chargement…</p>
              )}

              {!isLoading &&
                tables!.map((table, ti) => (
                  <div key={ti}>
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                      {table.heading}
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
                          <tr>
                            <th className="px-3 py-2 text-left">{table.dimensionLabel}</th>
                            <th className="px-3 py-2 text-left">Département</th>
                            {table.showYear && <th className="px-3 py-2 text-left">Année</th>}
                            <th className="px-3 py-2 text-right">Nb étudiants</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {table.rows.length === 0 ? (
                            <tr>
                              <td
                                colSpan={table.showYear ? 4 : 3}
                                className="px-3 py-4 text-center text-gray-400"
                              >
                                Aucune donnée
                              </td>
                            </tr>
                          ) : (
                            table.rows.map((r, i) => (
                              <tr key={i} className="hover:bg-gray-50">
                                <td className="px-3 py-1.5 text-gray-800">{r.dimension}</td>
                                <td className="px-3 py-1.5 text-gray-600">
                                  {r.department_code ?? "—"}
                                </td>
                                {table.showYear && (
                                  <td className="px-3 py-1.5 text-gray-600">
                                    {r.academic_year_label ?? "—"}
                                  </td>
                                )}
                                <td className="px-3 py-1.5 text-right font-medium tabular-nums">
                                  {r.count}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
