import type { AcademicYearStatus } from "@/lib/api/types";
import type { AcademicYearTransition } from "@/lib/api/academic-year-mutations";

export const statusLabels: Record<AcademicYearStatus, string> = {
  initialization: "Initialisation",
  recommendation: "Recommandation",
  candidature: "Candidature",
  import: "Import",
  pre_assignment: "Affectation en cours",
  validation: "Validation",
  published: "Publiée",
  closed: "Clôturée",
};

export const statusTone: Record<AcademicYearStatus, string> = {
  initialization: "bg-gray-100 text-gray-800",
  recommendation: "bg-blue-100 text-blue-800",
  candidature: "bg-amber-100 text-amber-800",
  import: "bg-orange-100 text-orange-800",
  pre_assignment: "bg-purple-100 text-purple-800",
  validation: "bg-emerald-100 text-emerald-800",
  published: "bg-teal-100 text-teal-800",
  closed: "bg-red-100 text-red-800",
};

export type NextTransition = {
  label: string;
  transition: AcademicYearTransition;
  /** Confirmation popup message — null = pas de popup */
  confirmMessage: string | null;
};

export const nextTransitions: Partial<Record<AcademicYearStatus, NextTransition>> = {
  initialization: {
    label: "Ouvrir recommandations",
    transition: "open-recommendation",
    confirmMessage:
      "Confirmez-vous que toutes les données sont prêtes (références, étudiants, accords, GPA) ?",
  },
  recommendation: {
    label: "Démarrer candidature",
    transition: "start-candidature",
    confirmMessage: null,
  },
  candidature: {
    label: "Clôturer les vœux",
    transition: "close-wishes",
    confirmMessage: "Confirmez-vous la clôture des vœux ? Les étudiants ne pourront plus modifier leurs souhaits.",
  },
  import: {
    label: "Lancer l'affectation",
    transition: "launch-assignment",
    confirmMessage:
      "Confirmez-vous que tous les vœux ont été importés (MoveOn, Excel) et que les données sont correctes ?",
  },
  validation: {
    label: "Publier les résultats",
    transition: "publish-results",
    confirmMessage:
      "Confirmez-vous que toutes les corrections sont validées et que les résultats peuvent être publiés aux étudiants ?",
  },
  published: {
    label: "Clôturer l'année",
    transition: "close",
    confirmMessage: "Confirmez-vous la clôture définitive de cette année universitaire ? Cette action est irréversible.",
  },
};

// État sans bouton manuel (transition automatique en cours)
// pre_assignment → validation : automatique (fin Gale-Shapley)
