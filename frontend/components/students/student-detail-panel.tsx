"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { Globe, X } from "lucide-react";

import { getStudentDetail } from "@/lib/api/student-mutations";
import { getCtiHistory, type MobilityHistory } from "@/lib/api/cti";
import type { StudentDetail, StudentWithEnrollment } from "@/lib/api/types";

// ---------------------------------------------------------------------------
// Panel principal
// ---------------------------------------------------------------------------

type Tab = "profile" | "mobilities";

export function StudentDetailPanel({
  student,
  onClose,
}: {
  student: StudentWithEnrollment;
  onClose: () => void;
}) {
  const [activeTab, setActiveTab] = useState<Tab>("profile");

  const [detail, setDetail] = useState<StudentDetail | null>(null);
  const [loadedId, setLoadedId] = useState<number | null>(null);
  const [loadError, setLoadError] = useState("");
  const profileLoading = loadedId !== student.student_id && !loadError;

  const [history, setHistory] = useState<MobilityHistory | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  // Ref pour éviter de re-déclencher le fetch à chaque re-render lié aux états de chargement
  const historyFetchedRef = useRef(false);

  // Chargement du profil dès l'ouverture
  useEffect(() => {
    let cancelled = false;
    setLoadError("");

    getStudentDetail(student.student_id)
      .then((data) => { if (!cancelled) { setDetail(data); setLoadedId(student.student_id); } })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : "Impossible de charger le détail.");
      });

    return () => { cancelled = true; };
  }, [student.student_id]);

  // Chargement paresseux de l'historique — déclenché une seule fois quand l'onglet est ouvert
  useEffect(() => {
    if (activeTab !== "mobilities" || historyFetchedRef.current) return;
    historyFetchedRef.current = true;
    setHistoryLoading(true);

    getCtiHistory(student.ine)
      .then(setHistory)
      .catch((err: unknown) => {
        setHistoryError(err instanceof Error ? err.message : "Impossible de charger l'historique.");
      })
      .finally(() => setHistoryLoading(false));
  }, [activeTab, student.ine]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 px-4">
      <div className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-lg bg-white shadow-xl">

        {/* Header */}
        <div className="flex shrink-0 items-start justify-between border-b border-gray-200 px-6 py-5">
          <div>
            <h2 className="text-lg font-bold text-gray-900">
              {student.last_name.toUpperCase()} {student.first_name}
            </h2>
            <p className="mt-1 font-mono text-sm text-gray-500">{student.ine}</p>
          </div>
          <button
            className="rounded-md p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700"
            onClick={onClose}
            title="Fermer"
            type="button"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Onglets */}
        <div className="flex shrink-0 border-b border-gray-200 px-6">
          <TabButton active={activeTab === "profile"} onClick={() => setActiveTab("profile")}>
            Profil
          </TabButton>
          <TabButton active={activeTab === "mobilities"} onClick={() => setActiveTab("mobilities")}>
            Mobilités & Durées
          </TabButton>
        </div>

        {/* Contenu scrollable */}
        <div className="flex-1 space-y-6 overflow-y-auto px-6 py-5">
          {activeTab === "profile" && (
            <ProfileTab
              student={student}
              detail={detail}
              loading={profileLoading}
              error={loadError}
            />
          )}
          {activeTab === "mobilities" && (
            <MobilitiesTab
              history={history}
              loading={historyLoading}
              error={historyError}
            />
          )}
        </div>

      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Onglet Profil (contenu existant)
// ---------------------------------------------------------------------------

function ProfileTab({
  student,
  detail,
  loading,
  error,
}: {
  student: StudentWithEnrollment;
  detail: StudentDetail | null;
  loading: boolean;
  error: string;
}) {
  return (
    <>
      <DetailSection title="Informations personnelles">
        <div className="space-y-2">
          <InfoRow label="Email" value={student.email || "—"} />
          <InfoRow
            label="Genre"
            value={student.gender === "M" ? "Homme" : student.gender === "F" ? "Femme" : "—"}
          />
          <InfoRow label="Nationalité" value={student.nationality_name_fr ?? "—"} />
        </div>
      </DetailSection>

      <DetailSection title="Inscription (année en cours)">
        <div className="space-y-2">
          <InfoRow label="Département" value={student.department_code} />
          <InfoRow label="Niveau" value={student.level_code} />
          <InfoRow label="Parcours" value={student.parcours_code ?? "—"} />
          <InfoRow
            label="GPA"
            value={student.gpa != null ? <span className="font-mono">{student.gpa}</span> : "—"}
          />
        </div>
      </DetailSection>

      <DetailSection title="Historique des inscriptions">
        {error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : loading ? (
          <div className="space-y-2">
            {[1, 2].map((i) => <div key={i} className="h-12 animate-pulse rounded-md bg-gray-100" />)}
          </div>
        ) : detail?.enrollments.length ? (
          <div className="space-y-3">
            {detail.enrollments.map((e) => (
              <div key={e.id} className="rounded-md border border-gray-100 bg-gray-50 px-4 py-3">
                <p className="mb-2 text-sm font-semibold text-gray-800">{e.academic_year_label}</p>
                <div className="space-y-1.5">
                  <InfoRow
                    label="Département"
                    value={<span className="rounded bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-700">{e.department_code}</span>}
                  />
                  <InfoRow
                    label="Niveau"
                    value={<span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">{e.level_code}</span>}
                  />
                  <InfoRow label="Parcours" value={e.parcours_code ?? "—"} />
                  <InfoRow
                    label="GPA"
                    value={e.gpa != null ? <span className="font-mono">{parseFloat(e.gpa).toFixed(2)}</span> : "—"}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm italic text-gray-400">Aucune inscription enregistrée.</p>
        )}
      </DetailSection>
    </>
  );
}

// ---------------------------------------------------------------------------
// Onglet Mobilités & Durées
// ---------------------------------------------------------------------------

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  validated: "Validée",
  rejected: "Rejetée",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-50 text-amber-700",
  validated: "bg-green-50 text-green-700",
  rejected: "bg-red-50 text-red-700",
};

function MobilitiesTab({
  history,
  loading,
  error,
}: {
  history: MobilityHistory | null;
  loading: boolean;
  error: string;
}) {
  if (error) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (loading || !history) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-100" />)}
      </div>
    );
  }

  const { totals, exchanges, internships, complementary_mobilities } = history;

  return (
    <>
      {/* Résumé des durées */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
          Durées comptabilisées
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <DurationChip label="Échanges" weeks={totals.exchange_weeks} color="blue" />
          <DurationChip label="Stages intl." weeks={totals.internship_weeks} color="purple" />
          <DurationChip label="Complémentaires" weeks={totals.complementary_weeks} color="emerald" />
          <DurationChip label="Total" weeks={totals.total_weeks} color="slate" bold />
        </div>
        <p className="mt-2 text-xs text-gray-400">
          Seules les mobilités validées / stages hors France sont comptabilisés dans le total.
        </p>
      </div>

      {/* Échanges universitaires */}
      <DetailSection title={`Échanges universitaires (${exchanges.length})`}>
        {exchanges.length === 0 ? (
          <Empty />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100 text-sm">
              <thead>
                <tr className="text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                  <Th>Année</Th>
                  <Th>Établissement</Th>
                  <Th>Pays</Th>
                  <Th>Durée</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {exchanges.map((e, idx) => (
                  <tr key={idx} className="hover:bg-gray-50/50">
                    <Td><span className="font-mono text-xs text-gray-600">{e.academic_year}</span></Td>
                    <Td><span className="font-medium text-gray-800">{e.institution_name}</span></Td>
                    <Td>
                      <span className="flex items-center gap-1 text-gray-600">
                        <Globe className="h-3 w-3 shrink-0 text-gray-400" />
                        {e.country_name}
                      </span>
                    </Td>
                    <Td>
                      {e.duration_weeks != null
                        ? <WeeksBadge weeks={e.duration_weeks} />
                        : <span className="text-xs italic text-gray-300">—</span>}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </DetailSection>

      {/* Stages */}
      <DetailSection title={`Stages (${internships.length})`}>
        {internships.length === 0 ? (
          <Empty />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100 text-sm">
              <thead>
                <tr className="text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                  <Th>Année</Th>
                  <Th>Entreprise</Th>
                  <Th>Pays</Th>
                  <Th>Durée</Th>
                  <Th>Type</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {internships.map((i, idx) => (
                  <tr key={idx} className="hover:bg-gray-50/50">
                    <Td><span className="font-mono text-xs text-gray-600">{i.academic_year ?? "—"}</span></Td>
                    <Td><span className="font-medium text-gray-800">{i.company_name}</span></Td>
                    <Td>
                      {i.country_name
                        ? <span className="flex items-center gap-1 text-gray-600"><Globe className="h-3 w-3 shrink-0 text-gray-400" />{i.country_name}</span>
                        : <span className="text-xs italic text-gray-300">—</span>}
                    </Td>
                    <Td>
                      {i.weeks_in_company != null
                        ? <WeeksBadge weeks={i.weeks_in_company} />
                        : <span className="text-xs italic text-gray-300">—</span>}
                    </Td>
                    <Td>
                      {i.is_international
                        ? <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">International</span>
                        : <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">France</span>}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </DetailSection>

      {/* Mobilités complémentaires */}
      <DetailSection title={`Mobilités complémentaires (${complementary_mobilities.length})`}>
        {complementary_mobilities.length === 0 ? (
          <Empty />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100 text-sm">
              <thead>
                <tr className="text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                  <Th>Année</Th>
                  <Th>Type</Th>
                  <Th>Pays / Institution</Th>
                  <Th>Période</Th>
                  <Th>Durée</Th>
                  <Th>Statut</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {complementary_mobilities.map((m) => (
                  <tr key={m.id} className="hover:bg-gray-50/50">
                    <Td><span className="font-mono text-xs text-gray-600">{m.academic_year}</span></Td>
                    <Td><span className="text-gray-800">{m.experience_type}</span></Td>
                    <Td>
                      <div className="flex flex-col">
                        <span className="flex items-center gap-1 text-gray-600">
                          <Globe className="h-3 w-3 shrink-0 text-gray-400" />
                          {m.destination_country}
                        </span>
                        {m.destination_institution && (
                          <span className="text-xs text-gray-400">{m.destination_institution}</span>
                        )}
                      </div>
                    </Td>
                    <Td>
                      <span className="text-xs text-gray-600">
                        {formatDate(m.start_date)} → {formatDate(m.end_date)}
                      </span>
                    </Td>
                    <Td><WeeksBadge weeks={m.duration_weeks} /></Td>
                    <Td>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[m.status] ?? "bg-gray-100 text-gray-600"}`}>
                        {STATUS_LABELS[m.status] ?? m.status}
                      </span>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </DetailSection>
    </>
  );
}

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      className={`mr-6 border-b-2 py-3 text-sm font-medium transition-colors ${
        active
          ? "border-[#1E3A8A] text-[#1E3A8A]"
          : "border-transparent text-gray-500 hover:text-gray-700"
      }`}
      onClick={onClick}
      type="button"
    >
      {children}
    </button>
  );
}

function DetailSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</h3>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex gap-3">
      <span className="w-28 shrink-0 text-xs text-gray-500">{label}</span>
      <span className="text-sm text-gray-900">{value ?? "—"}</span>
    </div>
  );
}

function DurationChip({
  label,
  weeks,
  color,
  bold,
}: {
  label: string;
  weeks: number;
  color: "blue" | "purple" | "emerald" | "slate";
  bold?: boolean;
}) {
  const colors = {
    blue:    "bg-blue-50 text-[#1E3A8A]",
    purple:  "bg-purple-50 text-purple-700",
    emerald: "bg-emerald-50 text-emerald-700",
    slate:   "bg-white border border-gray-200 text-gray-800",
  } as const;

  return (
    <div className={`rounded-lg p-3 ${colors[color]}`}>
      <p className="text-xs text-current/70">{label}</p>
      <p className={`mt-1 font-mono text-lg ${bold ? "font-bold" : "font-semibold"}`}>
        {weeks} <span className="text-xs font-normal">sem.</span>
      </p>
    </div>
  );
}

function WeeksBadge({ weeks }: { weeks: number }) {
  return (
    <span className="rounded-full bg-blue-50 px-2 py-0.5 font-mono text-xs font-medium text-blue-700">
      {weeks} sem.
    </span>
  );
}

function Empty() {
  return <p className="text-sm italic text-gray-400">Aucune donnée enregistrée.</p>;
}

function Th({ children }: { children: ReactNode }) {
  return (
    <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
      {children}
    </th>
  );
}

function Td({ children }: { children: ReactNode }) {
  return <td className="px-3 py-2.5">{children}</td>;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" });
}
