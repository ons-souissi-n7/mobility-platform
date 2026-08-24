"use client";

import { useCallback, useEffect, useState } from "react";
import { getCurrentIne } from "@/lib/auth";
import { fetchStudentProfile, fetchStudentRecommendations } from "@/lib/api/student";
import type { StudentProfile, StudentRecommendation } from "@/lib/api/types";

const STATUS_ORDER = [
  "initialization",
  "recommendation",
  "candidature",
  "import",
  "pre_assignment",
  "validation",
  "published",
  "finalization",
  "closed",
];

export default function RecommandationsPage() {
  const ine = getCurrentIne();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [selectedYearId, setSelectedYearId] = useState<number | undefined>(undefined);
  const [selectedYearStatus, setSelectedYearStatus] = useState<string>("");
  const [recommendations, setRecommendations] = useState<StudentRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchStudentProfile(ine)
      .then((p) => {
        setProfile(p);
        if (p?.enrolled_years[0]) {
          setSelectedYearId(p.enrolled_years[0].academic_year_id);
          setSelectedYearStatus(p.enrolled_years[0].academic_year_status);
        } else {
          setLoading(false);
        }
      })
      .catch(() => {
        setError("Impossible de charger le profil.");
        setLoading(false);
      });
  }, [ine]);

  const loadRecommendations = useCallback(
    (yearId: number) => {
      setLoading(true);
      setError("");
      fetchStudentRecommendations(ine, yearId)
        .then(setRecommendations)
        .catch((e: Error) => setError(e.message))
        .finally(() => setLoading(false));
    },
    [ine],
  );

  const recommendationIndex = STATUS_ORDER.indexOf("recommendation");
  const currentIndex = STATUS_ORDER.indexOf(selectedYearStatus);
  // Avant l'ouverture de la phase, il n'y a encore rien à recommander. À
  // partir de la phase "recommendation" et pour toutes les phases
  // suivantes (candidature, clôturée, etc.), le classement reste visible —
  // c'est une consultation en lecture seule, comme "Ma mobilité" reste
  // consultable pour les années passées.
  const isBeforePhase = currentIndex !== -1 && currentIndex < recommendationIndex;

  useEffect(() => {
    if (selectedYearId === undefined) return;
    if (isBeforePhase) {
      setRecommendations([]);
      setLoading(false);
    } else {
      loadRecommendations(selectedYearId);
    }
  }, [selectedYearId, isBeforePhase, loadRecommendations]);

  const modelBased = recommendations[0]?.model_based ?? true;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Recommandations</h1>
          <p className="mt-1 text-sm text-gray-500">
            Un classement des destinations les plus adaptées à votre profil, à consulter
            avant la saisie de vos vœux.
          </p>
        </div>
        {profile && profile.enrolled_years.length > 0 && (
          <select
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            value={selectedYearId ?? ""}
            onChange={(e) => {
              const yr = profile.enrolled_years.find(
                (y) => y.academic_year_id === Number(e.target.value),
              );
              setSelectedYearId(yr?.academic_year_id);
              setSelectedYearStatus(yr?.academic_year_status ?? "");
            }}
          >
            {profile.enrolled_years.map((y) => (
              <option key={y.academic_year_id} value={y.academic_year_id}>
                {y.academic_year_label}
              </option>
            ))}
          </select>
        )}
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && <div className="py-16 text-center text-sm text-gray-400">Chargement…</div>}

      {!loading && !error && isBeforePhase && (
        <div className="rounded-lg border border-gray-200 bg-gray-50 px-6 py-6 text-center">
          <p className="text-sm text-gray-500">Aucune recommandation fournie actuellement.</p>
          <p className="mt-1 text-xs text-gray-400">
            La phase de recommandation n&apos;est pas encore ouverte pour cette année.
          </p>
        </div>
      )}

      {!loading && !error && !isBeforePhase && selectedYearId !== undefined && (
        <section>
          {recommendations.length > 0 && !modelBased && (
            <div className="mb-4 rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
              Historique encore insuffisant pour affiner ce classement : il est basé sur
              votre profil (GPA, département) plutôt que sur le modèle statistique.
            </div>
          )}

          {recommendations.length === 0 ? (
            <div className="py-16 text-center text-sm text-gray-400">
              Aucune destination éligible pour votre profil cette année.
            </div>
          ) : (
            <ol className="space-y-2">
              {recommendations.map((r, idx) => (
                <li
                  key={r.agreement_year_id}
                  className="flex items-center gap-4 rounded-lg border bg-white px-5 py-3 shadow-sm"
                >
                  <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-[#1E3A8A] text-xs font-bold text-white">
                    {idx + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900">{r.university_name}</p>
                    <p className="text-xs text-gray-500">{r.agreement_name}</p>
                  </div>
                  <span className="flex-shrink-0 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">
                    {r.country_name}
                  </span>
                  {r.score !== null && (
                    <span className="flex-shrink-0 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
                      {Math.round(r.score * 100)}%
                    </span>
                  )}
                </li>
              ))}
            </ol>
          )}
        </section>
      )}
    </div>
  );
}
