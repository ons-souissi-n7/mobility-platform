import type { AcademicYearStatus } from "@/lib/api/types";
import type { AcademicYearTransition } from "@/lib/api/academic-year-mutations";

export const statusLabels: Record<AcademicYearStatus, string> = {
  initialization: "Initialisation",
  recommendation: "Recommandation",
  consolidation: "Consolidation",
  pre_assignment: "Pre-affectation",
  validation: "Validation",
  closed: "Cloturee",
};

export const statusTone: Record<AcademicYearStatus, string> = {
  initialization: "bg-gray-100 text-gray-800",
  recommendation: "bg-blue-100 text-blue-800",
  consolidation: "bg-amber-100 text-amber-800",
  pre_assignment: "bg-purple-100 text-purple-800",
  validation: "bg-emerald-100 text-emerald-800",
  closed: "bg-red-100 text-red-800",
};

export const nextTransitions: Partial<
  Record<
    AcademicYearStatus,
    {
      label: string;
      transition: AcademicYearTransition;
    }
  >
> = {
  initialization: {
    label: "Ouvrir recommandations",
    transition: "open-recommendation",
  },
  recommendation: {
    label: "Demarrer consolidation",
    transition: "start-consolidation",
  },
  consolidation: {
    label: "Lancer pre-affectation",
    transition: "launch-pre-assignment",
  },
  pre_assignment: {
    label: "Soumettre validation",
    transition: "submit-for-validation",
  },
  validation: {
    label: "Close",
    transition: "close",
  },
};
