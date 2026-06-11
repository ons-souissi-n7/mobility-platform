"use client";

import { ChevronDown, ChevronUp, Search } from "lucide-react";
import { useMemo, useState } from "react";

import type { AuditLog } from "@/lib/api/types";

const ACTION_STYLES: Record<string, { label: string; className: string }> = {
  create: { label: "Création", className: "bg-emerald-50 text-emerald-700" },
  update: { label: "Modification", className: "bg-blue-50 text-blue-700" },
  delete: { label: "Suppression", className: "bg-red-50 text-red-700" },
  access: { label: "Accès", className: "bg-gray-100 text-gray-600" },
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
  const style = ACTION_STYLES[action] ?? { label: action, className: "bg-gray-100 text-gray-600" };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${style.className}`}>
      {style.label}
    </span>
  );
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

  const date = new Date(log.timestamp).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const entityLabel = ENTITY_LABELS[log.entity_type] ?? log.entity_type;
  const hasChanges = log.changes != null && Object.keys(log.changes).length > 0;

  return (
    <>
      <tr className="hover:bg-gray-50">
        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{date}</td>
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

export function AuditLogsWorkspace({ initialLogs }: { initialLogs: AuditLog[] }) {
  const [actionFilter, setActionFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState("");
  const [actorFilter, setActorFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const hasFilters = actionFilter || entityFilter || actorFilter || dateFrom || dateTo;

  const filtered = useMemo(() => {
    return initialLogs.filter((log) => {
      if (actionFilter && log.action !== actionFilter) return false;
      if (entityFilter && log.entity_type !== entityFilter) return false;
      if (actorFilter && !(log.actor_username ?? "").toLowerCase().includes(actorFilter.toLowerCase())) return false;
      if (dateFrom && log.timestamp < dateFrom) return false;
      if (dateTo && log.timestamp > `${dateTo}T23:59:59`) return false;
      return true;
    });
  }, [initialLogs, actionFilter, entityFilter, actorFilter, dateFrom, dateTo]);

  const entityTypes = useMemo(
    () => Array.from(new Set(initialLogs.map((l) => l.entity_type))).sort(),
    [initialLogs],
  );

  function reset() {
    setActionFilter("");
    setEntityFilter("");
    setActorFilter("");
    setDateFrom("");
    setDateTo("");
  }

  return (
    <div className="space-y-4">
      {/* Filtres */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2 overflow-x-auto">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="w-40 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
          >
            <option value="">Toutes les actions</option>
            <option value="create">Création</option>
            <option value="update">Modification</option>
            <option value="delete">Suppression</option>
            <option value="access">Accès</option>
          </select>

          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="w-48 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
          >
            <option value="">Tous les types</option>
            {entityTypes.map((t) => (
              <option key={t} value={t}>{ENTITY_LABELS[t] ?? t}</option>
            ))}
          </select>

          <div className="relative shrink-0">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
            <input
              type="text"
              value={actorFilter}
              onChange={(e) => setActorFilter(e.target.value)}
              placeholder="Utilisateur…"
              className="w-36 rounded-md border border-gray-300 bg-white pl-7 pr-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            />
          </div>

          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-36 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
          />
          <span className="text-xs text-gray-400 shrink-0">→</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-36 shrink-0 rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
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
            {filtered.length} entrée{filtered.length > 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        {filtered.length === 0 ? (
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
                {filtered.map((log) => (
                  <LogRow key={log.id} log={log} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
