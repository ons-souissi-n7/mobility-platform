"use client";

import { AlertTriangle, ChevronDown, ChevronUp, RotateCw } from "lucide-react";
import { useState } from "react";

import { Badge, type BadgeStyle } from "@/components/ui/badge";
import { Pagination } from "@/components/ui/pagination";
import { apiBaseUrl, DEFAULT_PAGE_SIZE } from "@/lib/config";
import type { AcademicYear, ImportErrorItem, ImportReportDetail, ImportReportList } from "@/lib/api/types";
import { formatDateTime, SELECT_CLS } from "@/lib/utils";

const SOURCE_STYLES: Record<string, BadgeStyle> = {
  moveon_accords:     { label: "MoveOn Accords",         className: "bg-blue-50 text-blue-700"      },
  moveon_categories:  { label: "MoveOn Catégories",      className: "bg-indigo-50 text-indigo-700"  },
  moveon_quotas:      { label: "MoveOn Quotas",          className: "bg-violet-50 text-violet-700"  },
  moveon_wishes:      { label: "MoveOn Vœux",            className: "bg-purple-50 text-purple-700"  },
  pegase:             { label: "Pégase",                  className: "bg-emerald-50 text-emerald-700" },
  excel:              { label: "Excel",                   className: "bg-amber-50 text-amber-700"    },
  excel_overrides:    { label: "Excel – Corrections",    className: "bg-orange-50 text-orange-700"  },
};

function SourceBadge({ source, label }: Readonly<{ source: string; label: string }>) {
  return <Badge value={source} map={SOURCE_STYLES} label={label} />;
}

function StatusBar({ report }: Readonly<{ report: ImportReportList }>) {
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

function ConflictRow({ err }: Readonly<{ err: ImportErrorItem }>) {
  const [forcing, setForcing] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  async function handleForce() {
    if (!err.raw_import_id) return;
    setForcing(true);
    setError("");
    try {
      const res = await fetch(`${apiBaseUrl}/imports/raw/${err.raw_import_id}/force-overwrite/`, {
        method: "POST",
        headers: { Accept: "application/json" },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail ?? "Erreur lors de la mise à jour forcée.");
      }
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue.");
    } finally {
      setForcing(false);
    }
  }

  return (
    <tr className={done ? "bg-emerald-50/60" : "bg-amber-50/60 hover:bg-amber-100/40"}>
      <td className="px-3 py-2 font-mono text-gray-700">{err.external_id || "—"}</td>
      <td className="px-3 py-2 text-amber-800">
        <div className="flex items-start gap-1">
          <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-amber-500" />
          <span>{err.reason}</span>
        </div>
        {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      </td>
      <td className="px-3 py-2 text-right">
        {done ? (
          <span className="text-xs text-emerald-700 font-medium">Mis à jour ✓</span>
        ) : err.raw_import_id ? (
          <button
            onClick={handleForce}
            disabled={forcing}
            type="button"
            className="inline-flex items-center gap-1 rounded-md bg-amber-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-amber-700 disabled:opacity-60"
          >
            <RotateCw className={`h-3 w-3 ${forcing ? "animate-spin" : ""}`} />
            Forcer
          </button>
        ) : null}
      </td>
    </tr>
  );
}

function ErrorsPanel({ errors }: Readonly<{ errors: ImportErrorItem[] }>) {
  if (errors.length === 0) {
    return (
      <p className="text-sm text-emerald-700 italic">Aucune erreur — import complet.</p>
    );
  }

  const conflicts = errors.filter((e) => e.is_conflict);
  const failures = errors.filter((e) => !e.is_conflict);

  return (
    <div className="space-y-3">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {errors.length} enregistrement{errors.length > 1 ? "s" : ""} rejeté{errors.length > 1 ? "s" : ""}
        {conflicts.length > 0 && (
          <span className="ml-2 text-amber-600">({conflicts.length} conflit{conflicts.length > 1 ? "s" : ""})</span>
        )}
      </p>

      {conflicts.length > 0 && (
        <div className="rounded-md border border-amber-200 bg-amber-50 overflow-hidden">
          <div className="px-3 py-2 text-xs font-semibold text-amber-800 border-b border-amber-200 bg-amber-100">
            Conflits — enregistrement modifié localement depuis la dernière sync
          </div>
          <table className="w-full text-xs">
            <thead className="border-b border-amber-100 text-amber-700">
              <tr>
                <th className="px-3 py-2 text-left font-medium">Identifiant</th>
                <th className="px-3 py-2 text-left font-medium">Détail</th>
                <th className="px-3 py-2 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-amber-50">
              {conflicts.map((err, i) => <ConflictRow key={i} err={err} />)}
            </tbody>
          </table>
        </div>
      )}

      {failures.length > 0 && (
        <div className="max-h-48 overflow-y-auto rounded-md border border-red-100 bg-red-50">
          <table className="w-full text-xs">
            <thead className="border-b border-red-100 bg-red-100 text-red-700">
              <tr>
                <th className="px-3 py-2 text-left font-medium">Identifiant</th>
                <th className="px-3 py-2 text-left font-medium">Motif de rejet</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-50">
              {failures.map((err, i) => (
                <tr key={i} className="hover:bg-red-100/50">
                  <td className="px-3 py-1.5 font-mono text-gray-700">{err.external_id || "—"}</td>
                  <td className="px-3 py-1.5 text-red-700">{err.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ReportRow({ report }: Readonly<{ report: ImportReportList }>) {
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

  const date = formatDateTime(report.created_at);

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
}: Readonly<{
  reports: ImportReportList[];
  academicYears: AcademicYear[];
}>) {
  const [sourceFilter, setSourceFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const sources = Array.from(
    new Map(reports.map((r) => [r.source, r.source_display])).entries()
  ).sort((a, b) => a[1].localeCompare(b[1]));

  const filtered = reports.filter((r) => {
    if (sourceFilter && r.source !== sourceFilter) return false;
    if (yearFilter && r.academic_year_label !== yearFilter) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / DEFAULT_PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const pageItems = filtered.slice((safePage - 1) * DEFAULT_PAGE_SIZE, safePage * DEFAULT_PAGE_SIZE);

  function handleSourceChange(value: string) {
    setSourceFilter(value);
    setCurrentPage(1);
  }

  function handleYearChange(value: string) {
    setYearFilter(value);
    setCurrentPage(1);
  }

  return (
    <div className="space-y-4">
      {/* Filtres */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-3 overflow-x-auto">
          <select
            value={yearFilter}
            onChange={(e) => handleYearChange(e.target.value)}
            className={`w-40 shrink-0 ${SELECT_CLS}`}
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
            onChange={(e) => handleSourceChange(e.target.value)}
            className={`w-48 shrink-0 ${SELECT_CLS}`}
          >
            <option value="">Toutes les sources</option>
            {sources.map(([src, label]) => (
              <option key={src} value={src}>{label}</option>
            ))}
          </select>

          {(sourceFilter || yearFilter) && (
            <button
              onClick={() => { setSourceFilter(""); setYearFilter(""); setCurrentPage(1); }}
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
                {pageItems.map((report) => (
                  <ReportRow key={report.id} report={report} />
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          page={safePage}
          totalPages={totalPages}
          totalItems={filtered.length}
          pageSize={DEFAULT_PAGE_SIZE}
          onPageChange={setCurrentPage}
          emptyLabel="Aucun rapport d'import"
        />
      </div>
    </div>
  );
}
