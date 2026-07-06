"use client";

import type { ReactNode } from "react";
import { X, Lock } from "lucide-react";

import type {
  Agreement,
  AgreementYear,
  AgreementYearDepartment,
  Department,
  Level,
  MobilityCategory,
  PartnerUniversity,
} from "@/lib/api/types";

// ── N7 detection ────────────────────────────────────────────────────────────

function isN7Institution(name: string): boolean {
  const n = name.toLowerCase().replace(/[\s\-_]+/g, "");
  return n.includes("enseeiht") || n === "n7" || n.includes("inpenseeiht");
}

function parseInstitutions(raw: string): string[] {
  if (!raw.trim()) return [];
  return raw.split(/[,;|]/).map((s) => s.trim()).filter(Boolean);
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
        {title}
      </h3>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex gap-3">
      <span className="w-36 shrink-0 text-xs text-gray-500">{label}</span>
      <span className="text-sm text-gray-900">{value ?? "—"}</span>
    </div>
  );
}

function DirectionBadge({ direction }: { direction: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    outgoing: { label: "Sortant",  cls: "bg-blue-100 text-blue-700" },
    incoming: { label: "Entrant",  cls: "bg-orange-100 text-orange-700" },
    both:     { label: "Les deux", cls: "bg-purple-100 text-purple-700" },
  };
  const c = map[direction] ?? { label: direction, cls: "bg-gray-100 text-gray-500" };
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${c.cls}`}>
      {c.label}
    </span>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

type Props = {
  agreement: Agreement;
  allAgreementYears: AgreementYear[];
  allDeptQuotas: AgreementYearDepartment[];
  university: PartnerUniversity | undefined;
  category: MobilityCategory | undefined;
  departments: Map<number, Department>;
  levels: Map<number, Level>;
  onClose: () => void;
};

export function AgreementDetailModal({
  agreement,
  allAgreementYears,
  allDeptQuotas,
  university,
  category,
  departments,
  levels,
  onClose,
}: Props) {
  const yearInstances = allAgreementYears
    .filter((yi) => yi.agreement_id === agreement.id)
    .sort((a, b) => b.academic_year_label.localeCompare(a.academic_year_label));

  const deptQuotasByYearId = new Map<number, AgreementYearDepartment[]>();
  for (const dq of allDeptQuotas) {
    const list = deptQuotasByYearId.get(dq.agreement_year_id) ?? [];
    list.push(dq);
    deptQuotasByYearId.set(dq.agreement_year_id, list);
  }

  const rawInstitutions = parseInstitutions(agreement.inp_institutions);
  // N7 est toujours implicitement présent — on l'ajoute si non listé explicitement
  const n7AlreadyListed = rawInstitutions.some(isN7Institution);
  const institutions = n7AlreadyListed ? rawInstitutions : ["ENSEEIHT", ...rawInstitutions];

  const constrainedDepts = agreement.department_ids.length > 0
    ? agreement.department_ids.map((id) => departments.get(id)).filter(Boolean) as Department[]
    : null;

  const constrainedLevels = agreement.level_ids.length > 0
    ? agreement.level_ids.map((id) => levels.get(id)).filter(Boolean) as Level[]
    : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 px-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-white shadow-xl">

        {/* Header */}
        <div className="flex items-start justify-between border-b border-gray-200 px-6 py-5">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{agreement.name}</h2>
            <p className="mt-1 text-sm text-gray-500">Détails de l&apos;accord de mobilité</p>
          </div>
          <button
            className="rounded-md p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700"
            onClick={onClose}
            title="Fermer"
            type="button"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="space-y-6 px-6 py-5">

          {/* ── Informations générales ────────────────────────────────── */}
          <Section title="Informations générales">
            <div className="space-y-2">
              <InfoRow label="Référence" value={agreement.reference || "—"} />
              <InfoRow label="MoveON ID" value={agreement.moveon_id || "—"} />
              <InfoRow
                label="Direction"
                value={<DirectionBadge direction={agreement.direction} />}
              />
              <InfoRow
                label="Cadre de mobilité"
                value={category?.name ?? "Non défini"}
              />
              <InfoRow
                label="Validité"
                value={
                  agreement.valid_from || agreement.valid_until ? (
                    <span>
                      {agreement.valid_from?.slice(0, 7) ?? "—"}
                      {" → "}
                      {agreement.valid_until?.slice(0, 7) ?? "—"}
                    </span>
                  ) : "—"
                }
              />
              <InfoRow
                label="Dernière sync"
                value={agreement.last_sync_moveon
                  ? new Date(agreement.last_sync_moveon).toLocaleDateString("fr-FR")
                  : "—"}
              />
            </div>
          </Section>

          <hr className="border-gray-100" />

          {/* ── Établissement partenaire ──────────────────────────────── */}
          <Section title="Établissement partenaire">
            {university ? (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-2">
                <p className="font-semibold text-gray-900">{university.name}</p>
                <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs text-gray-600">
                  {university.short_name && (
                    <span><span className="text-gray-400">Abréviation : </span>{university.short_name}</span>
                  )}
                  {university.translated_name && (
                    <span><span className="text-gray-400">Nom traduit : </span>{university.translated_name}</span>
                  )}
                  {university.erasmus_code && (
                    <span><span className="text-gray-400">Code Erasmus : </span>{university.erasmus_code}</span>
                  )}
                  {university.city && (
                    <span><span className="text-gray-400">Ville : </span>{university.city}</span>
                  )}
                  {university.email && (
                    <span><span className="text-gray-400">Email : </span>{university.email}</span>
                  )}
                  {university.url && (
                    <span className="col-span-2">
                      <span className="text-gray-400">URL : </span>
                      <a
                        className="text-blue-600 underline hover:text-blue-800"
                        href={university.url}
                        rel="noreferrer"
                        target="_blank"
                      >
                        {university.url}
                      </a>
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm italic text-gray-400">Université partenaire non trouvée.</p>
            )}
          </Section>

          <hr className="border-gray-100" />

          {/* ── Établissements INP ────────────────────────────────────── */}
          <Section title="Établissements INP partageant cet accord">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold text-gray-900">{agreement.inp_total_places}</span>
                <span className="text-sm text-gray-500">places INP au total</span>
                <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                  N7 inclus
                </span>
              </div>

              <div className="flex flex-wrap gap-2">
                {institutions.map((inst, i) => {
                  const n7 = isN7Institution(inst);
                  return (
                    <span
                      key={i}
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
                        n7
                          ? "bg-amber-100 text-amber-900 ring-1 ring-amber-300"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {inst}
                      {n7 && (
                        <span className="rounded-full bg-amber-600 px-1.5 py-0.5 text-[9px] font-bold text-white">
                          N7
                        </span>
                      )}
                    </span>
                  );
                })}
              </div>
            </div>
          </Section>

          <hr className="border-gray-100" />

          {/* ── Contraintes ───────────────────────────────────────────── */}
          <Section title="Contraintes de l'accord">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="mb-2 text-xs font-medium text-gray-500">Départements</p>
                {constrainedDepts ? (
                  <div className="flex flex-wrap gap-1">
                    {constrainedDepts.map((d) => (
                      <span key={d.id} className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                        {d.code}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs italic text-gray-400">Tous les départements</span>
                )}
              </div>
              <div>
                <p className="mb-2 text-xs font-medium text-gray-500">Niveaux</p>
                {constrainedLevels ? (
                  <div className="flex flex-wrap gap-1">
                    {constrainedLevels.map((l) => (
                      <span key={l.id} className="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
                        {l.code}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs italic text-gray-400">Tous les niveaux</span>
                )}
              </div>
            </div>
          </Section>

          {/* ── Remarques ─────────────────────────────────────────────── */}
          <hr className="border-gray-100" />
          <Section title="Remarques">
            {agreement.remarks ? (
              <p className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
                {agreement.remarks}
              </p>
            ) : (
              <p className="text-sm italic text-gray-400">Aucune remarque.</p>
            )}
          </Section>

          <hr className="border-gray-100" />

          {/* ── Instances annuelles ───────────────────────────────────── */}
          <Section title="Instances annuelles">
            {yearInstances.length === 0 ? (
              <p className="text-sm italic text-gray-400">Aucune instance annuelle.</p>
            ) : (
              <div className="overflow-hidden rounded-lg border border-gray-200">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-left text-xs font-semibold uppercase text-gray-500">
                    <tr>
                      <th className="px-4 py-2">Année</th>
                      <th className="px-4 py-2">Statut</th>
                      <th className="px-4 py-2 text-right">Places N7</th>
                      <th className="px-4 py-2">Quotas départements</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {yearInstances.map((yi) => {
                      const quotas = deptQuotasByYearId.get(yi.id) ?? [];
                      return (
                        <tr key={yi.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">
                            {yi.academic_year_label}
                          </td>
                          <td className="px-4 py-3">
                            {yi.is_validated ? (
                              <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                                <Lock size={9} /> Validé
                              </span>
                            ) : yi.is_active ? (
                              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                                Actif
                              </span>
                            ) : (
                              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                                Inactif
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right font-semibold text-[#1E3A8A]">
                            {yi.n7_places}
                          </td>
                          <td className="px-4 py-3">
                            {quotas.length > 0 ? (
                              <div className="flex flex-wrap gap-1.5">
                                {quotas.map((dq) => {
                                  const dept = departments.get(dq.department_id);
                                  return (
                                    <span key={dq.id} className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700">
                                      {dept?.code ?? dq.department_id} : {dq.estimated_places}
                                    </span>
                                  );
                                })}
                              </div>
                            ) : (
                              <span className="text-xs italic text-gray-400">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Section>

        </div>
      </div>
    </div>
  );
}
