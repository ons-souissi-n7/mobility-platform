type ReportItem = Record<string, unknown>;

export type ImportReportData = {
  created: number;
  updated: number;
  skipped?: number;
  unresolved: ReportItem[];
  errors?: string[];
};

export function ImportReportPanel({
  report,
  title = "Opération terminée",
  formatUnresolved,
  onClose,
}: {
  report: ImportReportData;
  title?: string;
  /** Format one unresolved item into a display string. Default uses `ine`/`individu` + `reason`. */
  formatUnresolved?: (item: ReportItem) => string;
  onClose: () => void;
}) {
  const errors = report.errors ?? [];
  const hasIssues = report.unresolved.length > 0 || errors.length > 0;

  const defaultFormat = (item: ReportItem) => {
    const prefix = item.ine
      ? `INE ${item.ine as string}`
      : item.individu
        ? String(item.individu) + (item.rank != null ? ` rang ${item.rank as number}` : "")
        : null;
    const reason = item.reason ? String(item.reason) : "";
    return prefix ? `${prefix} — ${reason}` : reason;
  };

  const fmt = formatUnresolved ?? defaultFormat;

  return (
    <div
      className={`rounded-lg border p-4 text-sm ${
        hasIssues ? "border-amber-200 bg-amber-50" : "border-emerald-200 bg-emerald-50"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className={`font-medium ${hasIssues ? "text-amber-800" : "text-emerald-800"}`}>
            {title}
          </p>
          <p className={hasIssues ? "text-amber-700" : "text-emerald-700"}>
            {report.created} créé{report.created !== 1 ? "s" : ""},{" "}
            {report.updated} mis à jour
            {(report.skipped ?? 0) > 0 && `, ${report.skipped} ignoré(s)`}
            {report.unresolved.length > 0 && `, ${report.unresolved.length} non résolu(s)`}
            {errors.length > 0 && `, ${errors.length} erreur(s)`}
          </p>

          {report.unresolved.length > 0 && (
            <ul className="mt-2 space-y-0.5 text-xs text-amber-700">
              {report.unresolved.slice(0, 5).map((item, i) => (
                <li key={i}>{fmt(item)}</li>
              ))}
              {report.unresolved.length > 5 && (
                <li>… et {report.unresolved.length - 5} autre(s)</li>
              )}
            </ul>
          )}

          {errors.length > 0 && (
            <ul className="mt-2 space-y-0.5 text-xs text-red-700">
              {errors.slice(0, 3).map((err, i) => (
                <li key={i}>{err}</li>
              ))}
              {errors.length > 3 && <li>… et {errors.length - 3} autre(s)</li>}
            </ul>
          )}
        </div>
        <button
          className="shrink-0 text-gray-400 hover:text-gray-600"
          onClick={onClose}
          type="button"
          aria-label="Fermer"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
