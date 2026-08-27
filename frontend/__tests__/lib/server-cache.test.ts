import { describe, expect, it, vi } from "vitest";

import { getApi } from "@/lib/api/client";
import {
  getCachedAcademicYears,
  getCachedCountries,
  getCachedCurrentYear,
  getCachedDepartments,
  getCachedLevels,
  getCachedMobilityCategories,
  getCachedParcours,
  getCachedPartnerUniversities,
} from "@/lib/api/server-cache";

vi.mock("@/lib/api/client", () => ({
  getApi: vi.fn().mockResolvedValue([]),
}));

const mockedGetApi = vi.mocked(getApi);

describe("server-cache", () => {
  it("each cached accessor delegates to getApi with its own endpoint", async () => {
    await getCachedCountries();
    expect(mockedGetApi).toHaveBeenCalledWith("/reference/countries/");

    await getCachedDepartments();
    expect(mockedGetApi).toHaveBeenCalledWith("/reference/departments/");

    await getCachedLevels();
    expect(mockedGetApi).toHaveBeenCalledWith("/reference/levels/");

    await getCachedParcours();
    expect(mockedGetApi).toHaveBeenCalledWith("/reference/parcours/");

    await getCachedAcademicYears();
    expect(mockedGetApi).toHaveBeenCalledWith("/academic/years/");

    await getCachedCurrentYear();
    expect(mockedGetApi).toHaveBeenCalledWith("/academic/years/current/");

    await getCachedMobilityCategories();
    expect(mockedGetApi).toHaveBeenCalledWith("/mobility/agreement-categories/");

    await getCachedPartnerUniversities();
    expect(mockedGetApi).toHaveBeenCalledWith("/institutions/universities/select-options/");
  });
});
