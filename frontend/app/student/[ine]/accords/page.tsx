"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchStudentAgreements, fetchStudentProfile } from "@/lib/api/student";
import type { StudentAgreement, StudentProfile } from "@/lib/api/types";

const DIRECTION_LABELS: Record<string, string> = {
  outgoing: "Sortant",
  incoming: "Entrant",
  both: "Les deux",
};

export default function AccordsPage() {
  const { ine } = useParams<{ ine: string }>();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [selectedYearId, setSelectedYearId] = useState<number | undefined>(undefined);
  const [agreements, setAgreements] = useState<StudentAgreement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchStudentProfile(ine)
      .then((p) => {
        setProfile(p);
        if (p?.enrolled_years[0]) setSelectedYearId(p.enrolled_years[0].academic_year_id);
      })
      .catch(() => setError("Impossible de charger le profil."));
  }, [ine]);

  useEffect(() => {
    if (selectedYearId === undefined) return;
    setLoading(true);
    setError("");
    fetchStudentAgreements(ine, selectedYearId)
      .then(setAgreements)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ine, selectedYearId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Accords disponibles</h1>
          <p className="mt-0.5 text-sm text-gray-500">
            Accords actifs correspondant à votre niveau et département
          </p>
        </div>
        {profile && profile.enrolled_years.length > 0 && (
          <select
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            value={selectedYearId ?? ""}
            onChange={(e) => setSelectedYearId(e.target.value ? Number(e.target.value) : undefined)}
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

      {loading ? (
        <div className="py-16 text-center text-sm text-gray-400">Chargement…</div>
      ) : agreements.length === 0 ? (
        <div className="py-16 text-center text-sm text-gray-400">
          Aucun accord disponible pour cette année.
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-100">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Université</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Accord</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Direction</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-gray-500">Quota N7</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Quotas / Dept</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Validité</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {agreements.map((a) => (
                <tr key={a.agreement_year_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <p className="font-medium text-sm text-gray-900">{a.university_name}</p>
                    <p className="text-xs text-gray-400">{a.country_name}</p>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">{a.agreement_name}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700">
                      {DIRECTION_LABELS[a.direction] ?? a.direction}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-sm font-semibold text-[#1E3A8A]">{a.n7_places}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {a.dept_quotas.map((dq) => (
                        <span
                          key={dq.department_id}
                          className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] font-medium text-gray-600"
                        >
                          {dq.department_code} : {dq.effective_places}
                        </span>
                      ))}
                      {a.dept_quotas.length === 0 && (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {a.valid_from ? a.valid_from.slice(0, 7) : "—"}
                    {" → "}
                    {a.valid_until ? a.valid_until.slice(0, 7) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-gray-400">
        {agreements.length} accord{agreements.length !== 1 ? "s" : ""} correspondant à votre profil
      </p>
    </div>
  );
}
