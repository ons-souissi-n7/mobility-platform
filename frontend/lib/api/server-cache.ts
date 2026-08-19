import { cache } from "react";

import { getApi } from "@/lib/api/client";
import type {
  AcademicYear,
  Country,
  Department,
  Level,
  MobilityCategory,
  Parcours,
  SelectOption,
} from "@/lib/api/types";

// Next.js 15: cookies() is an async dynamic API — calling it inside
// unstable_cache() throws "Accessing Dynamic data sources inside a cache
// scope is not supported." React cache() provides per-request memoization
// (deduplication within a single render pass) without this restriction.

export const getCachedCountries = cache(
  (): Promise<Country[]> => getApi<Country[]>("/reference/countries/"),
);

export const getCachedDepartments = cache(
  (): Promise<Department[]> => getApi<Department[]>("/reference/departments/"),
);

export const getCachedLevels = cache(
  (): Promise<Level[]> => getApi<Level[]>("/reference/levels/"),
);

export const getCachedParcours = cache(
  (): Promise<Parcours[]> => getApi<Parcours[]>("/reference/parcours/"),
);

// Academic years: no cross-request caching — status changes must be
// immediately reflected after FSM transitions.
export const getCachedAcademicYears = cache(
  (): Promise<AcademicYear[]> => getApi<AcademicYear[]>("/academic/years/"),
);

export const getCachedCurrentYear = cache(
  (): Promise<AcademicYear | null> =>
    getApi<AcademicYear | null>("/academic/years/current/"),
);

export const getCachedMobilityCategories = cache(
  (): Promise<MobilityCategory[]> =>
    getApi<MobilityCategory[]>("/mobility/agreement-categories/"),
);

export const getCachedPartnerUniversities = cache(
  (): Promise<SelectOption[]> =>
    getApi<SelectOption[]>("/institutions/universities/select-options/"),
);
