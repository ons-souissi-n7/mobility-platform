"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getDepartmentBreakdown,
  getDepartmentOptions,
  getCountryBreakdown,
  getCountryOptions,
  getMobilityTrends,
  getUniversityBreakdown,
  getUniversityOptions,
  exportAnalytics,
  type BreakdownResponse,
  type MobilityTrendPoint,
  type SelectOption,
} from "@/lib/api/analytics";
import { MobilityTrendsChart } from "@/components/analytics/mobility-trends-chart";
import { BreakdownChart } from "@/components/analytics/breakdown-chart";
import { BreakdownFilter } from "@/components/analytics/breakdown-filter";

const TABS = [
  { id: "global", label: "Flux globaux" },
  { id: "department", label: "Par département" },
  { id: "country", label: "Par pays" },
  { id: "university", label: "Par université" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const CHART_LABELS = [
  { key: "outgoing" as const, title: "Mobilités sortantes", color: "border-l-blue-500" },
  { key: "incoming" as const, title: "Mobilités entrantes", color: "border-l-green-500" },
  { key: "internships" as const, title: "Stages internationaux", color: "border-l-orange-500" },
];

function SectionCard({ title, accent, children }: Readonly<{ title: string; accent: string; children: React.ReactNode }>) {
  return (
    <div className={`rounded-xl border-l-4 ${accent} border border-border bg-card p-5 shadow-sm`}>
      <h3 className="text-sm font-semibold mb-4">{title}</h3>
      {children}
    </div>
  );
}

function LoadingCard() {
  return (
    <div className="rounded-xl border bg-card p-6 shadow-sm flex items-center justify-center h-56 text-muted-foreground text-sm">
      Chargement…
    </div>
  );
}

function ErrorCard({ message }: Readonly<{ message: string }>) {
  return (
    <div className="rounded-xl border bg-card p-6 shadow-sm flex items-center justify-center h-56 text-destructive text-sm">
      {message}
    </div>
  );
}

function ThreeChartsLayout({
  data,
  chartKeys = ["outgoing", "incoming", "internships"],
}: Readonly<{
  data: BreakdownResponse;
  chartKeys?: Array<"outgoing" | "incoming" | "internships">;
}>) {
  const visibleCharts = CHART_LABELS.filter(({ key }) => chartKeys.includes(key));
  return (
    <div className="space-y-4">
      {visibleCharts.map(({ key, title, color }) => (
        <SectionCard key={key} title={title} accent={color}>
          <BreakdownChart data={data[key]} height={260} />
        </SectionCard>
      ))}
    </div>
  );
}

function BreakdownTab({
  options,
  optionsPlaceholder,
  fetchData,
  filterKey,
  subtitle,
  chartKeys = ["outgoing", "incoming", "internships"],
}: Readonly<{
  options: SelectOption[];
  optionsPlaceholder: string;
  fetchData: (selected: (string | number)[]) => Promise<BreakdownResponse>;
  filterKey: string;
  subtitle: string;
  chartKeys?: Array<"outgoing" | "incoming" | "internships">;
}>) {
  const [selected, setSelected] = useState<(string | number)[]>([]);
  const [data, setData] = useState<BreakdownResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const load = useCallback(
    (sel: (string | number)[]) => {
      setLoading(true);
      setError(null);
      fetchData(sel)
        .then(setData)
        .catch(() => setError("Impossible de charger les données."))
        .finally(() => setLoading(false));
    },
    [fetchData]
  );

  useEffect(() => {
    load([]);
  }, [load]);

  function handleChange(sel: (string | number)[]) {
    setSelected(sel);
    load(sel);
  }

  return (
    <div className="space-y-4">
      {/* Barre de filtre horizontale */}
      <div className="rounded-xl border bg-card p-4 shadow-sm">
        <div className="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors shrink-0"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5 opacity-70">
              <path d="M14 2H2l5 6.5V13l2 1V8.5L14 2z" />
            </svg>
            Filtrer
            {selected.length > 0 && (
              <span className="ml-0.5 rounded-full bg-primary text-primary-foreground text-xs px-1.5 py-0.5 leading-none">
                {selected.length}
              </span>
            )}
          </button>

          {/* Pills des sélections */}
          <div className="flex gap-1.5 flex-wrap flex-1">
            {selected.length === 0 ? (
              <span className="text-xs text-muted-foreground italic py-1">
                {subtitle}
              </span>
            ) : (
              options
                .filter((o) => selected.map(String).includes(String(o.id)))
                .map((o) => (
                  <span
                    key={o.id}
                    className="inline-flex items-center gap-1 rounded-full bg-primary/10 text-primary text-xs px-2.5 py-1"
                  >
                    {o.label}
                    <button
                      type="button"
                      onClick={() =>
                        handleChange(selected.filter((s) => String(s) !== String(o.id)))
                      }
                      className="hover:opacity-70"
                      aria-label={`Retirer ${o.label}`}
                    >
                      ×
                    </button>
                  </span>
                ))
            )}
          </div>

          {selected.length > 0 && (
            <button
              type="button"
              onClick={() => handleChange([])}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors shrink-0"
            >
              Tout effacer
            </button>
          )}
        </div>

        {/* Panneau déroulant */}
        {open && (
          <div className="mt-3 pt-3 border-t">
            {options.length === 0 ? (
              <p className="text-xs text-muted-foreground">Chargement des options…</p>
            ) : (
              <BreakdownFilter
                key={filterKey}
                options={options}
                selected={selected}
                onChange={handleChange}
                placeholder={optionsPlaceholder}
              />
            )}
          </div>
        )}
      </div>

      {/* 3 graphes pleine largeur */}
      {loading && <LoadingCard />}
      {error && <ErrorCard message={error} />}
      {!loading && !error && data && (
        <ThreeChartsLayout data={data} chartKeys={chartKeys} />
      )}
    </div>
  );
}

export function AnalyticsDashboard() {
  const [activeTab, setActiveTab] = useState<TabId>("global");

  const [trends, setTrends] = useState<MobilityTrendPoint[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(true);
  const [trendsError, setTrendsError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  async function handleExport() {
    setExporting(true);
    setExportError(null);
    try {
      await exportAnalytics(5);
    } catch {
      setExportError("Impossible de générer l'export.");
    } finally {
      setExporting(false);
    }
  }

  const [deptOptions, setDeptOptions] = useState<SelectOption[]>([]);
  const [countryOptions, setCountryOptions] = useState<SelectOption[]>([]);
  const [univOptions, setUnivOptions] = useState<SelectOption[]>([]);

  useEffect(() => {
    getMobilityTrends(5)
      .then((res) => setTrends(res.data))
      .catch(() => setTrendsError("Impossible de charger les données globales."))
      .finally(() => setTrendsLoading(false));
  }, []);

  useEffect(() => {
    if (activeTab === "department" && deptOptions.length === 0)
      getDepartmentOptions().then(setDeptOptions).catch(() => {});
    if (activeTab === "country" && countryOptions.length === 0)
      getCountryOptions().then(setCountryOptions).catch(() => {});
    if (activeTab === "university" && univOptions.length === 0)
      getUniversityOptions().then(setUnivOptions).catch(() => {});
  }, [activeTab, deptOptions.length, countryOptions.length, univOptions.length]);

  const fetchDept = useCallback(
    (sel: (string | number)[]) =>
      getDepartmentBreakdown(5, sel.length ? sel.map(Number) : undefined),
    []
  );
  const fetchCountry = useCallback(
    (sel: (string | number)[]) =>
      getCountryBreakdown(5, sel.length ? sel.map(Number) : undefined),
    []
  );
  const fetchUniv = useCallback(
    (sel: (string | number)[]) =>
      getUniversityBreakdown(5, sel.length ? sel.map(Number) : undefined),
    []
  );

  return (
    <div className="space-y-6">
      {/* Barre d'actions */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Statistiques calculées sur les 5 dernières années académiques.
        </p>
        <div className="flex items-center gap-2">
          {exportError && (
            <span className="text-xs text-destructive">{exportError}</span>
          )}
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting}
            className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {exporting ? (
              <>
                <svg className="w-3.5 h-3.5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Export…
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5 opacity-70">
                  <path d="M8 1a.75.75 0 0 1 .75.75v6.69l1.97-1.97a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L4.22 7.53a.75.75 0 0 1 1.06-1.06L7.25 8.44V1.75A.75.75 0 0 1 8 1ZM1.5 13.25a.75.75 0 0 1 .75-.75h11.5a.75.75 0 0 1 0 1.5H2.25a.75.75 0 0 1-.75-.75Z" />
                </svg>
                Exporter Excel
              </>
            )}
          </button>
        </div>
      </div>

      {/* Onglets */}
      <div className="flex gap-1 border-b">
        {TABS.map((tab) => (
          <button
            type="button"
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={[
              "px-4 py-2 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground",
            ].join(" ")}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Flux globaux */}
      {activeTab === "global" && (
        <div className="space-y-6">
          {trendsLoading && <LoadingCard />}
          {trendsError && <ErrorCard message={trendsError} />}
          {!trendsLoading && !trendsError && (
            <div className="rounded-xl border bg-card p-6 shadow-sm">
              <h2 className="text-base font-semibold mb-1">Évolution des flux de mobilité</h2>
              <p className="text-sm text-muted-foreground mb-6">5 dernières années académiques</p>
              <MobilityTrendsChart data={trends} />
            </div>
          )}
        </div>
      )}

      {activeTab === "department" && (
        <BreakdownTab
          key="dept"
          options={deptOptions}
          optionsPlaceholder="Filtrer les départements…"
          fetchData={fetchDept}
          filterKey="dept"
          subtitle="5 dernières années académiques — aucun filtre = tous les départements"
        />
      )}

      {activeTab === "country" && (
        <BreakdownTab
          key="country"
          options={countryOptions}
          optionsPlaceholder="Rechercher un pays…"
          fetchData={fetchCountry}
          filterKey="country"
          subtitle="5 dernières années académiques — aucun filtre = top 10 pays"
        />
      )}

      {activeTab === "university" && (
        <BreakdownTab
          key="univ"
          options={univOptions}
          optionsPlaceholder="Rechercher une université…"
          fetchData={fetchUniv}
          filterKey="univ"
          subtitle="5 dernières années académiques — aucun filtre = top 10 universités"
          chartKeys={["outgoing", "incoming"]}
        />
      )}
    </div>
  );
}
