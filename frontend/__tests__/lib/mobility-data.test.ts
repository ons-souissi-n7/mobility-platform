import { describe, expect, it, vi } from "vitest";

import {
  fetchAgreements,
  getAgreementSelectOptions,
  getExpiringAgreements,
  getMobilityData,
} from "@/lib/api/mobility";
import { getApi } from "@/lib/api/client";
import {
  getCachedAcademicYears,
  getCachedCountries,
  getCachedCurrentYear,
  getCachedDepartments,
  getCachedLevels,
  getCachedMobilityCategories,
} from "@/lib/api/server-cache";

vi.mock("@/lib/api/client", () => ({
  getApi: vi.fn().mockResolvedValue({ results: [], count: 0 }),
}));
vi.mock("@/lib/api/server-cache", () => ({
  getCachedAcademicYears: vi.fn().mockResolvedValue([{ id: 1 }]),
  getCachedCountries: vi.fn().mockResolvedValue([{ id: 2 }]),
  getCachedCurrentYear: vi.fn().mockResolvedValue({ id: 1 }),
  getCachedDepartments: vi.fn().mockResolvedValue([{ id: 3 }]),
  getCachedLevels: vi.fn().mockResolvedValue([{ id: 4 }]),
  getCachedMobilityCategories: vi.fn().mockResolvedValue([{ id: 5 }]),
}));

const mockedGetApi = vi.mocked(getApi);

describe("mobility (server data)", () => {
  it("getAgreementSelectOptions / getExpiringAgreements hit the expected endpoints", () => {
    getAgreementSelectOptions();
    expect(mockedGetApi).toHaveBeenCalledWith("/mobility/agreements/select-options/");

    getExpiringAgreements(6);
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/mobility/agreements/expiring-soon/?months=6",
    );

    getExpiringAgreements();
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/mobility/agreements/expiring-soon/?months=4",
    );
  });

  it("fetchAgreements builds query params with the 200 default page_size", () => {
    fetchAgreements({ search: "n7", country_id: 1, is_active: true, page: 2 });
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/mobility/agreements/?search=n7&country_id=1&is_active=true&page_size=200&page=2",
    );

    fetchAgreements();
    expect(mockedGetApi).toHaveBeenCalledWith("/mobility/agreements/?page_size=200");
  });

  it("getMobilityData aggregates volatile and cached data in parallel", async () => {
    const result = await getMobilityData();

    expect(mockedGetApi).toHaveBeenCalledWith("/mobility/agreements/?page=1&page_size=500");
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/mobility/agreements/?include_deleted=true&page=1&page_size=500",
    );
    expect(mockedGetApi).toHaveBeenCalledWith("/mobility/agreement-years/?page=1&page_size=500");
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/mobility/agreement-year-departments/?page=1&page_size=500",
    );
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/mobility/raw-imports/moveon-errors/?page=1&page_size=25",
    );
    expect(mockedGetApi).toHaveBeenCalledWith("/institutions/universities/?page=1&page_size=500");
    expect(vi.mocked(getCachedMobilityCategories)).toHaveBeenCalled();
    expect(vi.mocked(getCachedLevels)).toHaveBeenCalled();
    expect(vi.mocked(getCachedCountries)).toHaveBeenCalled();
    expect(vi.mocked(getCachedDepartments)).toHaveBeenCalled();
    expect(vi.mocked(getCachedAcademicYears)).toHaveBeenCalled();
    expect(vi.mocked(getCachedCurrentYear)).toHaveBeenCalled();

    expect(result).toEqual({
      academicYears: [{ id: 1 }],
      agreementYears: [],
      agreementYearDepartments: [],
      mobilityCategories: [{ id: 5 }],
      agreements: [],
      allAgreements: [],
      currentYear: { id: 1 },
      countries: [{ id: 2 }],
      departments: [{ id: 3 }],
      importErrors: [],
      importErrorsTotalCount: 0,
      mobilityLevels: [{ id: 4 }],
      universities: [],
    });
  });
});
