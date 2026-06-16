"use client";

import { ChevronDown, ChevronUp, Search } from "lucide-react";
import { useState } from "react";

import { getAuditLogs, type AuditFilters } from "@/lib/api/audit";
import type { AuditLog, PagedResponse } from "@/lib/api/types";
import { DEFAULT_PAGE_SIZE } from "@/lib/config";
import { Badge, type BadgeStyle } from "@/components/ui/badge";
import { Pagination } from "@/components/ui/pagination";
import { formatDateTime, SELECT_CLS } from "@/lib/utils";

const ACTION_STYLES: Record<string, BadgeStyle> = {
  create: { label: "Création",    className: "bg-emerald-50 text-emerald-700" },
  update: { label: "Modification", className: "bg-blue-50 text-blue-700"     },
  delete: { label: "Suppression", className: "bg-red-50 text-red-700"        },
  access: { label: "Accès",       className: "bg-gray-100 text-gray-600"     },
};

const ENTITY_LABELS: Record<string, string> = {
  agreement: "Accord",
  agreementquota: "Quota accord",
  agreementyear: "Accord (année)",
  agreementyeardepartment: "Quota département",
  academicyear: "Année universitaire",
  mobilitycategory: "Cadre mobilité",
  partneruniversity: "Université partenaire",
  student: "Étudiant",
  annualenrollment: "Inscription",
  studentwish: "Vœu étudiant",
  level: "Niveau",
  department: "Département",
  country: "Pays",
};

function ActionBadge({ action }: { action: string }) {
  return <Badge value={action} map={ACTION_STYLES} />;
}

function ChangesPanel({ changes }: { changes: Record<string, [unknown, unknown]> | null }) {
  if (!changes || Object.keys(changes).length === 0) {
    return <p className="text-xs text-gray-400 italic">Aucun champ modifié enregistré.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-md border border-gray-200">
      <table className="w-full text-xs">
        <thead className="border-b border-gray-200 bg-gray-50 text-gray-500">
          <tr>
            <th className="px-3 py-2 text-left font-medium">Champ</th>
            <th className="px-3 py-2 text-left font-medium">Avant</th>
            <th className="px-3 py-2 text-left font-medium">Après</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {Object.entries(changes).map(([field, [before, after]]) => (
            <tr key={field} className="hover:bg-gray-50">
              <td className="px-3 py-1.5 font-mono text-gray-700">{field}</td>
              <td className="px-3 py-1.5 text-red-600">
                {before == null ? <span className="text-gray-400 italic">—</span> : String(before)}
              </td>
              <td className="px-3 py-1.5 text-emerald-700">
                {after == null ? <span className="text-gray-400 italic">—</span> : String(after)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LogRow({ log }: { log: AuditLog }) {
  const [expanded, setExpanded] = useState(false);

  const date = formatDateTime(log.timestamp, true);

  const entityLabel = ENTITY_LABELS[log.entity_type] ?? log.entity_type;
  const hasChanges = log.changes != null && Object.keys(log.changes).length > 0;

  return (
    <>
      <tr className="hover:bg-gray-50">
        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap" suppressHydrationWarning>{date}</td>
        <td className="px-4 py-3 text-xs font-medium text-gray-700">
          {log.actor_username ?? <span className="text-gray-400 italic">système</span>}
        </td>
        <td className="px-4 py-3">
          <ActionBadge action={log.action} />
        </td>
        <td className="px-4 py-3 text-xs text-gray-600">{entityLabel}</td>
        <td className="px-4 py-3 text-xs text-gray-700 max-w-xs truncate" title={log.entity_repr}>
          {log.entity_repr || <span className="text-gray-400">#{log.entity_id}</span>}
        </td>
        <td className="px-4 py-3 text-right">
          {hasChanges && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50"
              type="button"
            >
              {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              {expanded ? "Masquer" : "Diff"}
            </button>
          )}
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={6} className="bg-gray-50 px-6 py-3 border-t border-gray-100">
            <ChangesPanel changes={log.changes} />
          </td>
        </tr>
      )}
    </>
  );
}

export function AuditLogsWorkspace({ initialData }: { initialData: PagedResponse<AuditLog> }) {
  const [data, setData] = useState<PagedResponse<AuditLog>>(initialData);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState("");
  const [actorFilter, setActorFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const totalPages = Math.max(1, Math.ceil(data.count / DEFAULT_PAGE_SIZE));
  const hasFilters = actionFilter || entityFilter || actorFilter || dateFrom || dateTo;

  async function doFetch(p: number, filters: AuditFilters) {
    setLoading(true);
    try {
      const result = await getAuditLogs({ ...filters, page: p, page_size: DEFAULT_PAGE_SIZE });
      setData(result);
      setPage(p);
    } finally {
      setLoading(false);
    }
  }

  function currentFilters(): AuditFilters {
    return {
      action: actionFilter || undefined,
      entity_type: entityFilter || undefined,
      actor_username: actorFilter || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    };
  }

  function handleActionChange(value: string) {
    setActionFilter(value);
    doFetch(1, { ...currentFilters(), action: value || undefined });
  }

  function handleEntityChange(value: string) {
    setEntityFilter(value);
    doFetch(1, { ...currentFilters(), entity_type: value || undefined });
  }

  function handleActorChange(value: string) {
    setActorFilter(value);
    doFetch(1, { ...currentFilters(), actor_username: value || undefined });
  }

  function handleDateFromChange(value: string) {
    setDateFrom(value);
    doFetch(1, { ...currentFilters(), date_from: value || undefined });
  }

  function handleDateToChange(value: string) {
    setDateTo(value);
    doFetch(1, { ...currentFilters(), date_to: value || undefined });
  }

  function reset() {
    setActionFilter("");
    setEntityFilter("");
    setActorFilter("");
    setDateFrom("");
    setDateTo("");
    doFetch(1, {});
  }

  return (
    <div className="space-y-4">
      {/* Filtres */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2 overflow-x-auto">
          <select
            value={actionFilter}
            onChange={(e) => handleActionChange(e.target.value)}
            className={`w-40 shrink-0 ${SELECT_CLS}`}
          >
            <option value="">Toutes les actions</option>
            <option value="create">Création</option>
            <option value="update">Modification</option>
            <option value="delete">Suppression</option>
            <option value="access">Accès</option>
          </select>

          <select
            value={entityFilter}
            onChange={(e) => handleEntityChange(e.target.value)}
            className={`w-48 shrink-0 ${SELECT_CLS}`}
          >
            <option value="">Tous les types</option>
            {Object.keys(ENTITY_LABELS).sort().map((t) => (
              <option key={t} value={t}>{ENTITY_LABELS[t]}</option>
            ))}
          </select>

          <div className="relative shrink-0">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
            <input
              type="text"
              value={actorFilter}
              onChange={(e) => handleActorChange(e.target.value)}
              placeholder="Utilisateur…"
              className="w-36 rounded-md border border-gray-300 bg-white pl-7 pr-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            />
          </div>

          <input
            type="date"
            value={dateFrom}
            onChange={(e) => handleDateFromChange(e.target.value)}
            className={`w-36 shrink-0 ${SELECT_CLS}`}
          />
          <span className="text-xs text-gray-400 shrink-0">→</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => handleDateToChange(e.target.value)}
            className={`w-36 shrink-0 ${SELECT_CLS}`}
          />

          {hasFilters && (
            <button
              onClick={reset}
              className="shrink-0 rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs text-gray-500 hover:bg-gray-50"
              type="button"
            >
              Réinitialiser
            </button>
          )}

          <span className="shrink-0 ml-auto text-xs text-gray-400">
            {data.count} entrée{data.count > 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Table */}
      <div className={`overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-opacity ${loading ? "opacity-60" : ""}`}>
        {data.results.length === 0 ? (
          <div className="px-6 py-12 text-center text-sm text-gray-500">
            Aucune entrée dans le journal pour ces critères.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Utilisateur</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Entité</th>
                  <th className="px-4 py-3 font-medium">Objet</th>
                  <th className="px-4 py-3 font-medium text-right">Détail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.results.map((log) => (
                  <LogRow key={log.id} log={log} />
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          page={page}
          totalPages={totalPages}
          totalItems={data.count}
          pageSize={DEFAULT_PAGE_SIZE}
          onPageChange={(p) => doFetch(p, currentFilters())}
          emptyLabel="Aucune entrée dans le journal"
        />
      </div>
    </div>
  );
}
