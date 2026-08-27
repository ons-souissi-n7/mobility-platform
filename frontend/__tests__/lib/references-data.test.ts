import { describe, expect, it, vi } from "vitest";

import { getApi } from "@/lib/api/client";
import {
  getCountrySelectOptions,
  getDepartmentSelectOptions,
  getLevelSelectOptions,
  getParcoursSelectOptions,
  getReferenceData,
  getUniversitySelectOptions,
} from "@/lib/api/references";
import {
  getCachedCountries,
  getCachedDepartments,
  getCachedLevels,
  getCachedParcours,
} from "@/lib/api/server-cache";

vi.mock("@/lib/api/client", () => ({
  getApi: vi.fn().mockResolvedValue({ results: [], count: 0 }),
}));
vi.mock("@/lib/api/server-cache", () => ({
  getCachedCountries: vi.fn().mockResolvedValue([{ id: 1 }]),
  getCachedDepartments: vi.fn().mockResolvedValue([{ id: 2 }]),
  getCachedLevels: vi.fn().mockResolvedValue([{ id: 3 }]),
  getCachedParcours: vi.fn().mockResolvedValue([{ id: 4 }]),
}));

const mockedGetApi = vi.mocked(getApi);

describe("references (server data)", () => {
  it("select-option endpoints hit the expected endpoints", () => {
    getCountrySelectOptions();
    expect(mockedGetApi).toHaveBeenCalledWith("/reference/countries/select-options/");

    getDepartmentSelectOptions();
    expect(mockedGetApi).toHaveBeenCalledWith("/reference/departments/select-options/");

    getLevelSelectOptions();
    expect(mockedGetApi).toHaveBeenCalledWith("/reference/levels/select-options/");

    getParcoursSelectOptions(5);
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/reference/parcours/select-options/?department_id=5",
    );

    getParcoursSelectOptions();
    expect(mockedGetApi).toHaveBeenCalledWith("/reference/parcours/select-options/");

    getUniversitySelectOptions();
    expect(mockedGetApi).toHaveBeenCalledWith("/institutions/universities/select-options/");
  });

  it("getReferenceData aggregates volatile and cached data in parallel", async () => {
    const result = await getReferenceData();

    expect(mockedGetApi).toHaveBeenCalledWith(
      "/institutions/universities/?page=1&page_size=25",
    );
    expect(mockedGetApi).toHaveBeenCalledWith("/institutions/import-errors/?page=1&page_size=25");
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/reference/departments/import-errors/?page=1&page_size=25",
    );
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/reference/levels/import-errors/?page=1&page_size=25",
    );
    expect(vi.mocked(getCachedCountries)).toHaveBeenCalled();
    expect(vi.mocked(getCachedDepartments)).toHaveBeenCalled();
    expect(vi.mocked(getCachedLevels)).toHaveBeenCalled();
    expect(vi.mocked(getCachedParcours)).toHaveBeenCalled();

    expect(result).toEqual({
      countries: [{ id: 1 }],
      departments: [{ id: 2 }],
      universities: { results: [], count: 0 },
      universityImportErrors: [],
      universityImportErrorsCount: 0,
      departmentImportErrors: [],
      departmentImportErrorsCount: 0,
      mobilityLevels: [{ id: 3 }],
      levelImportErrors: [],
      levelImportErrorsCount: 0,
      parcours: [{ id: 4 }],
    });
  });
});
