"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

import { apiBaseUrl } from "@/lib/config";
import type { AcademicYear, ImportErrorItem, ImportReportDetail, ImportReportList } from "@/lib/api/types";

const SOURCE_COLORS: Record<string, string> = {
  moveon_accords: "bg-blue-50 text-blue-700",
  moveon_categories: "bg-indigo-50 text-indigo-700",
  moveon_quotas: "bg-violet-50 text-violet-700",
  pegase: "bg-emerald-50 text-emerald-700",
  excel: "bg-amber-50 text-amber-700",
};

function SourceBadge({ source, label }: { source: string; label: string }) {
  const color = SOURCE_COLORS[source] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}

function StatusBar({ report }: { report: ImportReportList }) {
  const { total, success_count, error_count, duplicate_count } = report;
  if (total === 0) return <span className="text-xs text-gray-400">—</span>;

  return (
    <div className="flex items-center gap-3 text-xs">
      <span className="text-emerald-700 font-medium">{success_count} ok</span>
      {error_count > 0 && (
        <span className="text-red-600 font-medium">{error_count} erreur{error_count > 1 ? "s" : ""}</span>
      )}
      {duplicate_count > 0 && (
        <span className="text-amber-600">{duplicate_count} doublon{duplicate_count > 1 ? "s" : ""}</span>
      )}
      <span className="text-gray-400">/ {total}</span>
    </div>
  );
}

function ErrorsPanel({ errors }: { errors: ImportErrorItem[] }) {
  if (errors.length === 0) {
    return (
      <p className="text-sm text-emerald-700 italic">Aucune erreur — import complet.</p>
    );
  }
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
        {errors.length} enregistrement{errors.length > 1 ? "s" : ""} rejeté{errors.length > 1 ? "s" : ""}
      </p>
      <div className="max-h-48 overflow-y-auto rounded-md border border-red-100 bg-red-50">
        <table className="w-full text-xs">
          <thead className="border-b border-red-100 bg-red-100 text-red-700">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Identifiant</th>
              <th className="px-3 py-2 text-left font-medium">Motif de rejet</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-red-50">
            {errors.map((err, i) => (
              <tr key={i} className="hover:bg-red-100/50">
                <td className="px-3 py-1.5 font-mono text-gray-700">{err.external_id || "—"}</td>
                <td className="px-3 py-1.5 text-red-700">{err.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReportRow({ report }: { report: ImportReportList }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<ImportReportDetail | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleToggle() {
    if (!expanded && !detail) {
      setLoading(true);
      try {
        const res = await fetch(`${apiBaseUrl}/imports/${report.id}/`, {
          headers: { Accept: "application/json" },
        });
        if (res.ok) setDetail(await res.json());
      } finally {
        setLoading(false);
      }
    }
    setExpanded((v) => !v);
  }

  const date = new Date(report.created_at).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const hasErrors = report.error_count > 0;

  return (
    <>
      <tr className={`hover:bg-gray-50 ${hasErrors ? "bg-red-50/30" : ""}`}>
        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap" suppressHydrationWarning>{date}</td>
        <td className="px-4 py-3">
          <SourceBadge source={report.source} label={report.source_display} />
        </td>
        <td className="px-4 py-3 text-xs text-gray-600">
          {report.academic_year_label ?? <span className="text-gray-400">—</span>}
        </td>
        <td className="px-4 py-3">
          <StatusBar report={report} />
        </td>
        <td className="px-4 py-3 text-xs text-gray-500">{report.triggered_by || "—"}</td>
        <td className="px-4 py-3 text-right">
          <button
            onClick={handleToggle}
            className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50"
            type="button"
          >
            {loading ? (
              <span className="animate-spin">⟳</span>
            ) : expanded ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
            {expanded ? "Masquer" : "Détail"}
          </button>
        </td>
      </tr>
      {expanded && detail && (
        <tr>
          <td colSpan={6} className="bg-gray-50 px-6 py-4 border-t border-gray-100">
            <ErrorsPanel errors={detail.errors} />
          </td>
        </tr>
      )}
    </>
  );
}

export function ImportReportsWorkspace({
  reports,
  academicYears,
}: {
  reports: ImportReportList[];
  academicYears: AcademicYear[];
}) {
  const [sourceFilter, setSourceFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");

  const sources = Array.from(
    new Map(reports.map((r) => [r.source, r.source_display])).entries()
  ).sort((a, b) => a[1].localeCompare(b[1]));

  const filtered = reports.filter((r) => {
    if (sourceFilter && r.source !== sourceFilter) return false;
    if (yearFilter && r.academic_year_label !== yearFilter) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Filtres */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-3 overflow-x-auto">
          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="w-40 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
          >
            <option value="">Toutes les années</option>
            {[...academicYears]
              .sort((a, b) => b.start_date.localeCompare(a.start_date))
              .map((y) => (
                <option key={y.id} value={y.label}>{y.label}</option>
              ))}
          </select>

          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="w-48 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
          >
            <option value="">Toutes les sources</option>
            {sources.map(([src, label]) => (
              <option key={src} value={src}>{label}</option>
            ))}
          </select>

          {(sourceFilter || yearFilter) && (
            <button
              onClick={() => { setSourceFilter(""); setYearFilter(""); }}
              className="shrink-0 rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs text-gray-500 hover:bg-gray-50"
              type="button"
            >
              Réinitialiser
            </button>
          )}

          <span className="shrink-0 ml-auto text-xs text-gray-400">
            {filtered.length} rapport{filtered.length > 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        {filtered.length === 0 ? (
          <div className="px-6 py-12 text-center text-sm text-gray-500">
            Aucun rapport d&apos;import pour ces filtres.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Source</th>
                  <th className="px-4 py-3 font-medium">Année</th>
                  <th className="px-4 py-3 font-medium">Résultats</th>
                  <th className="px-4 py-3 font-medium">Déclenché par</th>
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((report) => (
                  <ReportRow key={report.id} report={report} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
