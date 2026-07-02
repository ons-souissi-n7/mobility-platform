import { unstable_cache } from "next/cache";

import { getApi } from "@/lib/api/client";
import type {
  AcademicYear,
  Country,
  Department,
  Level,
  MobilityCategory,
  Parcours,
} from "@/lib/api/types";

// TTL constants (seconds)
const TTL_MED  = 60;    // 1min — données synchro Pégase / MoveON
const TTL_SHORT = 30;   // 30s  — données modifiables par l'UI

// Pays : pas de cache — données légères (< 300 entrées), modifiables via fixtures
export const getCachedCountries = () => getApi<Country[]>("/reference/countries/");

export const getCachedDepartments = unstable_cache(
  () => getApi<Department[]>("/reference/departments/"),
  ["ref-departments"],
  { revalidate: TTL_MED, tags: ["ref-departments"] },
);

export const getCachedLevels = unstable_cache(
  () => getApi<Level[]>("/reference/levels/"),
  ["ref-levels"],
  { revalidate: TTL_MED, tags: ["ref-levels"] },
);

export const getCachedParcours = unstable_cache(
  () => getApi<Parcours[]>("/reference/parcours/"),
  ["ref-parcours"],
  { revalidate: TTL_SHORT, tags: ["ref-parcours"] },
);

// Pas de cache pour les années : le statut change via transitions et doit être immédiatement reflété.
export const getCachedAcademicYears = () => getApi<AcademicYear[]>("/academic/years/");
export const getCachedCurrentYear = () => getApi<AcademicYear | null>("/academic/years/current/");

export const getCachedMobilityCategories = unstable_cache(
  () => getApi<MobilityCategory[]>("/mobility/agreement-categories/"),
  ["ref-mobility-categories"],
  { revalidate: TTL_MED, tags: ["ref-mobility-categories"] },
);
