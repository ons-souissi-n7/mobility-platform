"use client";

import { Download, Info, Loader2, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { Btn } from "@/components/ui/btn";
import { downloadCtiExport, getCtiStats } from "@/lib/api/cti";
import type { AcademicYear, CtiRegionRow, CtiStats } from "@/lib/api/types";

// ─── Tables VII.D3 ────────────────────────────────────────────────────────────

function SectionTitle({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#1E3A8A]">
      {children}
    </h3>
  );
}

function StatsTable({ head, rows }: Readonly<{ head: string[]; rows: (string | number)[][] }>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            {head.map((h, i) => (
              <th
                key={i}
                className={`border border-gray-200 bg-[#BDD7EE] px-2 py-1.5 text-center font-semibold text-gray-800 ${i === 0 ? "text-left" : ""}`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => {
            const isTotal = row[0] === "Total";
            return (
              <tr key={ri} className={isTotal ? "bg-gray-100 font-semibold" : "odd:bg-white even:bg-gray-50"}>
                {row.map((cell, ci) => (
                  <td
                    key={ci}
                    className={`border border-gray-200 px-2 py-1.5 tabular-nums ${ci === 0 ? "text-left text-gray-700" : "text-center text-gray-900"}`}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RegionTable({ rows = [] }: Readonly<{ rows?: CtiRegionRow[] }>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            {["Pays / Région", "Hommes", "Femmes", "Total"].map((h, i) => (
              <th
                key={i}
                className={`border border-gray-200 bg-[#BDD7EE] px-2 py-1.5 font-semibold text-gray-800 ${i === 0 ? "text-left" : "text-center"}`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.region} className="odd:bg-white even:bg-gray-50">
              <td className="border border-gray-200 px-2 py-1.5 text-left text-gray-700">{r.region}</td>
              <td className="border border-gray-200 px-2 py-1.5 text-center tabular-nums text-gray-900">{r.hommes}</td>
              <td className="border border-gray-200 px-2 py-1.5 text-center tabular-nums text-gray-900">{r.femmes}</td>
              <td className="border border-gray-200 px-2 py-1.5 text-center tabular-nums font-semibold text-gray-900">{r.total}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CtiKpiCard({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <div className="rounded-md border border-gray-200 bg-[#EFF6FF] px-4 py-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-0.5 text-lg font-bold text-[#1E3A8A]">{value}</p>
    </div>
  );
}

// ─── Visualisation VII.D3 ────────────────────────────────────────────────────

function CtiStatsView({ stats }: Readonly<{ stats: CtiStats }>) {
  const excHead = ["", "< 1 sem. FISE", "< 1 sem. FISA", "1 semestre FISE", "1 semestre FISA", "> 1 sem. FISE", "> 1 sem. FISA"];
  const excRows = stats.exchanges.map((r) => [r.label, r.lt_fise, r.lt_fisa, r.eq_fise, r.eq_fisa, r.gt_fise, r.gt_fisa]);

  const intHead = ["", "< 3 mois FISE", "< 3 mois FISA", "3–6 mois FISE", "3–6 mois FISA", "> 6 mois FISE", "> 6 mois FISA"];
  const intRows = stats.internships.map((r) => [r.label, r.lt_fise, r.lt_fisa, r.mid_fise, r.mid_fisa, r.gt_fise, r.gt_fisa]);

  const incHead = ["", "< 1 semestre", "1 semestre", "> 1 semestre"];
  const incRows = stats.incoming.map((r) => [r.label, r.lt, r.eq, r.gt]);

  return (
    <div className="mt-6 space-y-6">
      {/* Effectifs cohorte */}
      <div className="flex flex-wrap gap-3">
        <CtiKpiCard label="Inscrits FISE (niveau terminal)" value={String(stats.enrolled_fise)} />
        <CtiKpiCard label="Inscrits FISA (niveau terminal)" value={String(stats.enrolled_fisa)} />
        <CtiKpiCard label="Total cohorte" value={String(stats.enrolled_fise + stats.enrolled_fisa)} />
      </div>

      {/* 1.a Échanges */}
      <div>
        <SectionTitle>VII-D3-1.a — Mobilité académique sortante (échanges) — toute la scolarité</SectionTitle>
        <StatsTable head={excHead} rows={excRows} />
      </div>

      {/* 1.b Stages */}
      <div>
        <SectionTitle>VII-D3-1.b — Stages internationaux — toute la scolarité</SectionTitle>
        <StatsTable head={intHead} rows={intRows} />
      </div>

      {/* 2 DD sortants */}
      <div>
        <SectionTitle>VII-D3-2 — Doubles diplômés ingénieurs sortants (FISE seulement)</SectionTitle>
        <RegionTable rows={stats.dd_outgoing} />
      </div>

      {/* 3.a et 3.b */}
      <div>
        <SectionTitle>VII-D3-3 — Taux et durée de mobilité sortante (FISE seulement)</SectionTitle>
        <div className="flex flex-wrap gap-3">
          <CtiKpiCard label="% diplômés avec mobilité — FISE" value={`${stats.pct_fise.toFixed(1)} %`} />
          <CtiKpiCard label="% diplômés avec mobilité — FISA" value={`${stats.pct_fisa.toFixed(1)} %`} />
          <CtiKpiCard label="Durée moyenne — FISE" value={`${stats.avg_months_fise} mois`} />
          <CtiKpiCard label="Durée moyenne — FISA" value={`${stats.avg_months_fisa} mois`} />
        </div>
      </div>

      {/* 4 Entrants */}
      <div>
        <SectionTitle>VII-D3-4 — Mobilité académique entrante (année en cours)</SectionTitle>
        <StatsTable head={incHead} rows={incRows} />
      </div>

      {/* 5 DD entrants */}
      <div>
        <SectionTitle>VII-D3-5 — Doubles diplômés ingénieurs entrants</SectionTitle>
        <RegionTable rows={stats.dd_incoming} />
      </div>
    </div>
  );
}

// ─── Panneau principal ────────────────────────────────────────────────────────

export function CtiExportPanel({ years }: Readonly<{ years: AcademicYear[] }>) {
  const [selectedYearId, setSelectedYearId] = useState<number>(years[0]?.id ?? 0);
  const [stats, setStats]               = useState<CtiStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingExport, setLoadingExport] = useState(false);
  const [error, setError]               = useState<string | null>(null);

  async function loadStats(yearId: number) {
    setLoadingStats(true);
    setError(null);
    setStats(null);
    try {
      setStats(await getCtiStats(yearId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur lors du chargement des statistiques.");
    } finally {
      setLoadingStats(false);
    }
  }

  useEffect(() => {
    if (selectedYearId) loadStats(selectedYearId);
  }, [selectedYearId]);

  async function handleExport() {
    if (!selectedYearId) return;
    setLoadingExport(true);
    setError(null);
    try {
      await downloadCtiExport(selectedYearId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur lors de l'export.");
    } finally {
      setLoadingExport(false);
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      {/* En-tête */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">Rapport CTI — VII.D3</h2>
          <p className="mt-0.5 text-xs text-gray-500">
            Indicateurs de mobilité pour la cohorte diplômante (niveaux terminaux configurés dans les Références).
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-700" htmlFor="cti-year-select">
              Année académique
            </label>
            <select
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
              disabled={loadingStats || loadingExport}
              id="cti-year-select"
              onChange={(e) => setSelectedYearId(Number(e.target.value))}
              value={selectedYearId}
            >
              {years.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.label}
                </option>
              ))}
            </select>
          </div>

          <Btn disabled={loadingStats} onClick={() => loadStats(selectedYearId)} variant="ghost">
            {loadingStats ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Actualiser
          </Btn>

          <Btn disabled={loadingExport || loadingStats} onClick={handleExport} variant="primary">
            {loadingExport ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {loadingExport ? "Génération…" : "Exporter Excel"}
          </Btn>
        </div>
      </div>

      {/* Info cohorte */}
      <div className="mt-4 flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span>
          La cohorte est constituée des étudiants inscrits cette année aux niveaux marqués{" "}
          <strong>Terminal</strong>{" "}dans les Références. La mobilité est calculée sur
          l&apos;ensemble de leur historique (toutes années confondues).
        </span>
      </div>

      {error && <p className="mt-3 text-xs text-red-600">{error}</p>}

      {/* Statistiques */}
      {loadingStats && !stats && (
        <div className="mt-8 flex items-center justify-center gap-2 text-sm text-gray-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          Chargement des statistiques…
        </div>
      )}

      {stats && <CtiStatsView stats={stats} />}
    </div>
  );
}
