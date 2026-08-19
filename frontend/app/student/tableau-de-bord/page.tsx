"use client";

import { useEffect, useState } from "react";
import { getCurrentIne } from "@/lib/auth";
import { getCtiDuration, type MobilityDuration } from "@/lib/api/cti";

export default function TableauDeBordPage() {
  const ine = getCurrentIne();
  const [duration, setDuration] = useState<MobilityDuration | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getCtiDuration(ine)
      .then(setDuration)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ine]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="mt-1 text-sm text-gray-500">
          Durée cumulée sur l&apos;ensemble de votre scolarité à l&apos;ENSEEIHT.
        </p>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="py-16 text-center text-sm text-gray-400">Chargement…</div>
      )}

      {!loading && duration && (
        <div className="space-y-6">
          {/* Total */}
          <div className="rounded-lg border bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-base font-semibold text-gray-800">
              Durée totale de mobilité
            </h2>
            <div className="flex items-end gap-2">
              <span className="text-4xl font-bold text-[#1E3A8A]">
                {duration.total_weeks}
              </span>
              <span className="mb-1 text-lg text-gray-500">semaines</span>
            </div>
          </div>

          {/* Détail par type */}
          <div className="grid gap-4 sm:grid-cols-3">
            <DurationCard
              label="Mobilité sortante"
              weeks={duration.exchange_weeks}
              color="blue"
              description="Échange universitaire à l'étranger"
            />
            <DurationCard
              label="Stage international"
              weeks={duration.internship_weeks}
              color="purple"
              description="Stage effectué hors de France"
            />
            <DurationCard
              label="Mobilité complémentaire"
              weeks={duration.complementary_weeks}
              color="emerald"
              description="Summer school, séjour linguistique…"
            />
          </div>
        </div>
      )}
    </div>
  );
}

function DurationCard({
  label,
  weeks,
  color,
  description,
}: Readonly<{
  label: string;
  weeks: number;
  color: "blue" | "purple" | "emerald";
  description: string;
}>) {
  const palette = {
    blue:    { bg: "bg-blue-50",    text: "text-[#1E3A8A]",   border: "border-blue-100" },
    purple:  { bg: "bg-purple-50",  text: "text-purple-700",  border: "border-purple-100" },
    emerald: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-100" },
  } as const;
  const c = palette[color];

  return (
    <div className={`rounded-lg border ${c.border} ${c.bg} p-5`}>
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${c.text}`}>{weeks}</p>
      <p className="text-sm text-gray-400">semaines</p>
      <p className="mt-3 text-xs text-gray-500">{description}</p>
    </div>
  );
}
