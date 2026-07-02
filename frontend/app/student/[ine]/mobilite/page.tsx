"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchStudentAssignment, fetchStudentProfile, fetchStudentWishes } from "@/lib/api/student";
import type { StudentAssignment, StudentProfile, StudentWishItem } from "@/lib/api/types";

export default function MobilitePage() {
  const { ine } = useParams<{ ine: string }>();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [selectedYearId, setSelectedYearId] = useState<number | undefined>(undefined);
  const [selectedYearStatus, setSelectedYearStatus] = useState<string>("");
  const [wishes, setWishes] = useState<StudentWishItem[]>([]);
  const [result, setResult] = useState<StudentAssignment | null | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchStudentProfile(ine)
      .then((p) => {
        setProfile(p);
        if (p?.enrolled_years[0]) {
          setSelectedYearId(p.enrolled_years[0].academic_year_id);
          setSelectedYearStatus(p.enrolled_years[0].academic_year_status);
        }
      })
      .catch(() => setError("Impossible de charger le profil."));
  }, [ine]);

  const loadMobilite = useCallback((yearId: number) => {
    setLoading(true);
    setError("");
    setResult(undefined);
    Promise.all([
      fetchStudentWishes(ine, yearId),
      fetchStudentAssignment(ine, yearId),
    ])
      .then(([w, r]) => { setWishes(w); setResult(r); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ine]);

  useEffect(() => {
    if (selectedYearId === undefined) return;
    loadMobilite(selectedYearId);
  }, [selectedYearId, loadMobilite]);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-xl font-bold text-gray-900">Ma mobilité</h1>
        {profile && profile.enrolled_years.length > 0 && (
          <select
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            value={selectedYearId ?? ""}
            onChange={(e) => {
              const yr = profile.enrolled_years.find((y) => y.academic_year_id === Number(e.target.value));
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

      {!loading && (
        <>
          {/* ── Section Vœux ───────────────────────────────────── */}
          <section>
            <h2 className="mb-3 text-base font-semibold text-gray-800">Mes vœux</h2>
            {wishes.length === 0 ? (
              <p className="text-sm text-gray-400">Aucun vœu enregistré pour cette année.</p>
            ) : (
              <ol className="space-y-2">
                {wishes.map((w) => (
                  <li key={w.rank} className="flex items-center gap-4 rounded-lg border bg-white px-5 py-3 shadow-sm">
                    <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-[#1E3A8A] text-xs font-bold text-white">
                      {w.rank}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900">{w.university_name}</p>
                      <p className="text-xs text-gray-500">{w.agreement_name}</p>
                    </div>
                    <span className="flex-shrink-0 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">
                      {w.country_name}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </section>

          {/* ── Section Résultat ───────────────────────────────── */}
          <section>
            <h2 className="mb-3 text-base font-semibold text-gray-800">Mon résultat</h2>

            {result === null && selectedYearStatus !== "closed" && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-6 py-6 text-center">
                <p className="text-sm font-medium text-amber-800">
                  Les résultats ne sont pas encore publiés pour cette année.
                </p>
                <p className="mt-1 text-xs text-amber-600">
                  Vous serez notifié(e) lorsque les résultats seront disponibles.
                </p>
              </div>
            )}

            {result === null && selectedYearStatus === "closed" && (
              <div className="rounded-lg border border-gray-200 bg-gray-50 px-6 py-6 text-center">
                <p className="text-sm text-gray-500">
                  Aucun résultat d&apos;affectation pour cette année universitaire.
                </p>
              </div>
            )}

            {result && (
              <div className="rounded-lg border bg-white p-6 shadow-sm">
                {result.is_assigned ? (
                  <>
                    <div className="mb-4 flex items-center gap-2">
                      <span className="inline-flex items-center rounded-full bg-green-100 px-4 py-1.5 text-sm font-semibold text-green-800">
                        Affecté(e) en mobilité internationale
                      </span>
                    </div>
                    <dl className="grid gap-3 sm:grid-cols-2">
                      {result.university_name && (
                        <div className="rounded-md bg-gray-50 p-4">
                          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Université d&apos;accueil</dt>
                          <dd className="mt-1 text-sm font-semibold text-gray-900">{result.university_name}</dd>
                        </div>
                      )}
                      {result.country_name && (
                        <div className="rounded-md bg-gray-50 p-4">
                          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Pays</dt>
                          <dd className="mt-1 text-sm font-semibold text-gray-900">{result.country_name}</dd>
                        </div>
                      )}
                      {result.agreement_name && (
                        <div className="rounded-md bg-gray-50 p-4 sm:col-span-2">
                          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Convention</dt>
                          <dd className="mt-1 text-sm font-semibold text-gray-900">{result.agreement_name}</dd>
                        </div>
                      )}
                    </dl>
                  </>
                ) : (
                  <div className="py-2 text-center">
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-4 py-1.5 text-sm font-medium text-gray-700">
                      Non affecté(e)
                    </span>
                    <p className="mt-3 text-sm text-gray-500">
                      Aucune place disponible ne correspondait à votre dossier pour cette année.
                    </p>
                  </div>
                )}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
