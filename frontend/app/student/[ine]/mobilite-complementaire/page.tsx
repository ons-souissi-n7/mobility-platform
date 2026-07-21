"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import {
  declareComplementaryMobility,
  fetchComplementaryCountries,
  fetchComplementaryMobilities,
  fetchStudentProfile,
} from "@/lib/api/student";
import type { ComplementaryMobility, Country, StudentProfile } from "@/lib/api/types";

const STATUS_STYLES: Record<
  ComplementaryMobility["status"],
  { bg: string; text: string; label: string }
> = {
  pending: { bg: "bg-amber-100", text: "text-amber-800", label: "En attente" },
  validated: { bg: "bg-green-100", text: "text-green-800", label: "Validée" },
  rejected: { bg: "bg-red-100", text: "text-red-800", label: "Rejetée" },
};

function StatusBadge({ status }: { status: ComplementaryMobility["status"] }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.pending;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${s.bg} ${s.text}`}
    >
      {s.label}
    </span>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

const EMPTY_FORM = {
  experience_type: "",
  country_id: "",
  destination_institution: "",
  start_date: "",
  end_date: "",
};

export default function MobiliteComplementairePage() {
  const { ine } = useParams<{ ine: string }>();

  // Profile + enrolled years (for the top year selector)
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [selectedYearId, setSelectedYearId] = useState<number | undefined>(undefined);
  // current year (for form submission) = first enrolled year
  const [currentYearId, setCurrentYearId] = useState<number | undefined>(undefined);

  const [countries, setCountries] = useState<Country[]>([]);
  const [mobilities, setMobilities] = useState<ComplementaryMobility[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [formSuccess, setFormSuccess] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  // Load profile + countries once
  useEffect(() => {
    fetchStudentProfile(ine)
      .then((p) => {
        setProfile(p);
        if (p?.enrolled_years[0]) {
          const firstId = p.enrolled_years[0].academic_year_id;
          setSelectedYearId(firstId);
          setCurrentYearId(firstId);
        }
      })
      .catch(() => {});
    fetchComplementaryCountries().then(setCountries).catch(() => {});
  }, [ine]);

  // Reload list whenever the selected year changes
  const loadList = useCallback(
    (yearId: number | undefined) => {
      setLoadingList(true);
      setListError("");
      fetchComplementaryMobilities(ine, yearId)
        .then(setMobilities)
        .catch(() => setListError("Impossible de charger les déclarations."))
        .finally(() => setLoadingList(false));
    },
    [ine],
  );

  useEffect(() => {
    if (selectedYearId === undefined) return;
    loadList(selectedYearId);
  }, [selectedYearId, loadList]);

  function handleFieldChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    setFormSuccess("");

    if (!currentYearId) {
      setFormError("Impossible de déterminer l'année universitaire en cours.");
      return;
    }
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setFormError("Veuillez sélectionner un fichier justificatif.");
      return;
    }
    if (!form.country_id) {
      setFormError("Veuillez sélectionner un pays de destination.");
      return;
    }

    setSubmitting(true);
    try {
      await declareComplementaryMobility(
        ine,
        {
          academic_year_id: currentYearId,
          experience_type: form.experience_type,
          country_id: Number(form.country_id),
          destination_institution: form.destination_institution,
          start_date: form.start_date,
          end_date: form.end_date,
        },
        file,
      );
      setFormSuccess(
        "Votre déclaration a été soumise avec succès. Elle sera examinée par l'administration.",
      );
      setForm(EMPTY_FORM);
      if (fileRef.current) fileRef.current.value = "";
      // Refresh list on the current year (not necessarily the selected year)
      if (selectedYearId === currentYearId) loadList(currentYearId);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  const currentYearLabel =
    profile?.enrolled_years.find((y) => y.academic_year_id === currentYearId)
      ?.academic_year_label ?? "";

  return (
    <div className="space-y-8">
      {/* ── Header with year selector (consultation only) ── */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-xl font-bold text-gray-900">Mobilité complémentaire</h1>
        {profile && profile.enrolled_years.length > 0 && (
          <select
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            value={selectedYearId ?? ""}
            onChange={(e) => {
              const yr = profile.enrolled_years.find(
                (y) => y.academic_year_id === Number(e.target.value),
              );
              setSelectedYearId(yr?.academic_year_id);
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

      {/* ── History list for selected year ───────────────── */}
      <section>
        <h2 className="mb-4 text-base font-semibold text-gray-800">Mes déclarations</h2>

        {listError && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {listError}
          </div>
        )}

        {loadingList && (
          <div className="py-8 text-center text-sm text-gray-400">Chargement…</div>
        )}

        {!loadingList && mobilities.length === 0 && (
          <p className="text-sm text-gray-400">Aucune déclaration pour cette année.</p>
        )}

        {!loadingList && mobilities.length > 0 && (
          <div className="space-y-3">
            {mobilities.map((m) => (
              <div key={m.id} className="rounded-lg border bg-white p-5 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <p className="text-sm font-semibold text-gray-900">{m.experience_type}</p>
                    <p className="text-xs text-gray-500">
                      {m.destination_country_name}
                      {m.destination_institution ? ` — ${m.destination_institution}` : ""}
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatDate(m.start_date)} → {formatDate(m.end_date)}
                    </p>
                  </div>
                  <StatusBadge status={m.status} />
                </div>

                {m.status === "rejected" && m.rejection_reason && (
                  <div className="mt-3 rounded-md border border-red-100 bg-red-50 px-3 py-2 text-xs text-red-700">
                    <span className="font-medium">Motif du rejet :</span>{" "}
                    {m.rejection_reason}
                  </div>
                )}

                {m.document_url && (
                  <a
                    href={m.document_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 block text-xs font-medium text-[#1E3A8A] underline-offset-2 hover:underline"
                  >
                    {m.document_name || "Justificatif"} ↗
                  </a>
                )}

                <p className="mt-3 text-xs text-gray-300">
                  Déposée le {formatDate(m.created_at)}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Declaration form (always for current year) ───── */}
      <section>
        <h2 className="mb-1 text-base font-semibold text-gray-800">
          Déclarer une nouvelle expérience
        </h2>
        {currentYearLabel && (
          <p className="mb-4 text-xs text-gray-500">
            La déclaration sera enregistrée pour l&apos;année universitaire{" "}
            <span className="font-medium text-gray-700">{currentYearLabel}</span>.
          </p>
        )}

        <form
          onSubmit={handleSubmit}
          className="space-y-5 rounded-lg border bg-white p-6 shadow-sm"
        >
          {formError && (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {formError}
            </div>
          )}
          {formSuccess && (
            <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
              {formSuccess}
            </div>
          )}

          {/* Type d'expérience (texte libre) */}
          <div>
            <label
              htmlFor="experience_type"
              className="mb-1 block text-xs font-medium text-gray-700"
            >
              Type d&apos;expérience *{" "}
              <span className="font-normal text-gray-400">
                (ex. Summer school, séjour linguistique, programme court…)
              </span>
            </label>
            <input
              id="experience_type"
              name="experience_type"
              type="text"
              required
              value={form.experience_type}
              onChange={handleFieldChange}
              placeholder="Décrivez le type d'expérience"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            />
          </div>

          {/* Pays de destination */}
          <div>
            <label
              htmlFor="country_id"
              className="mb-1 block text-xs font-medium text-gray-700"
            >
              Pays de destination *
            </label>
            <select
              id="country_id"
              name="country_id"
              required
              value={form.country_id}
              onChange={handleFieldChange}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            >
              <option value="">— Sélectionner un pays —</option>
              {countries.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name_fr}
                </option>
              ))}
            </select>
          </div>

          {/* Établissement */}
          <div>
            <label
              htmlFor="destination_institution"
              className="mb-1 block text-xs font-medium text-gray-700"
            >
              Établissement d&apos;accueil{" "}
              <span className="font-normal text-gray-400">(optionnel)</span>
            </label>
            <input
              id="destination_institution"
              name="destination_institution"
              type="text"
              value={form.destination_institution}
              onChange={handleFieldChange}
              placeholder="ex. TU Berlin"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            />
          </div>

          {/* Dates */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="start_date"
                className="mb-1 block text-xs font-medium text-gray-700"
              >
                Date de début *
              </label>
              <input
                id="start_date"
                name="start_date"
                type="date"
                required
                value={form.start_date}
                onChange={handleFieldChange}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
              />
            </div>
            <div>
              <label
                htmlFor="end_date"
                className="mb-1 block text-xs font-medium text-gray-700"
              >
                Date de fin *
              </label>
              <input
                id="end_date"
                name="end_date"
                type="date"
                required
                value={form.end_date}
                onChange={handleFieldChange}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
              />
            </div>
          </div>

          {/* Justificatif */}
          <div>
            <label
              htmlFor="document"
              className="mb-1 block text-xs font-medium text-gray-700"
            >
              Justificatif *{" "}
              <span className="font-normal text-gray-400">
                (PDF, JPEG, PNG, WEBP — max 10 Mo)
              </span>
            </label>
            <input
              id="document"
              name="document"
              type="file"
              ref={fileRef}
              required
              accept=".pdf,.jpg,.jpeg,.png,.webp"
              className="block w-full text-sm text-gray-600 file:mr-4 file:rounded-md file:border-0 file:bg-[#1E3A8A] file:px-4 file:py-2 file:text-xs file:font-medium file:text-white hover:file:bg-[#1E3A8A]/90"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-[#1E3A8A] px-5 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Envoi en cours…" : "Soumettre la déclaration"}
          </button>
        </form>
      </section>
    </div>
  );
}
