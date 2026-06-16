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
const TTL_LONG = 3600;  // 1h  — pays (quasi-immuable)
const TTL_MED  = 300;   // 5min — données synchro Pégase / MoveON
const TTL_SHORT = 60;   // 1min — données modifiables par l'UI

export const getCachedCountries = unstable_cache(
  () => getApi<Country[]>("/reference/countries/"),
  ["ref-countries"],
  { revalidate: TTL_LONG, tags: ["ref-countries"] },
);

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

export const getCachedAcademicYears = unstable_cache(
  () => getApi<AcademicYear[]>("/academic/years/"),
  ["ref-academic-years"],
  { revalidate: TTL_MED, tags: ["ref-academic-years"] },
);

export const getCachedCurrentYear = unstable_cache(
  () => getApi<AcademicYear | null>("/academic/years/current/"),
  ["ref-current-year"],
  { revalidate: TTL_MED, tags: ["ref-academic-years"] },
);

export const getCachedMobilityCategories = unstable_cache(
  () => getApi<MobilityCategory[]>("/mobility/agreement-categories/"),
  ["ref-mobility-categories"],
  { revalidate: TTL_MED, tags: ["ref-mobility-categories"] },
);
