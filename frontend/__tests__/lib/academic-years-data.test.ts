import { describe, expect, it, vi } from "vitest";

import { getAcademicYearSelectOptions, getAcademicYearsData } from "@/lib/api/academic-years";
import { getApi } from "@/lib/api/client";
import { getCachedAcademicYears, getCachedCurrentYear } from "@/lib/api/server-cache";

vi.mock("@/lib/api/client", () => ({
  getApi: vi.fn().mockResolvedValue([]),
}));
vi.mock("@/lib/api/server-cache", () => ({
  getCachedAcademicYears: vi.fn().mockResolvedValue([{ id: 1 }]),
  getCachedCurrentYear: vi.fn().mockResolvedValue({ id: 1, status: "recommendation" }),
}));

const mockedGetApi = vi.mocked(getApi);
const mockedGetCachedAcademicYears = vi.mocked(getCachedAcademicYears);
const mockedGetCachedCurrentYear = vi.mocked(getCachedCurrentYear);

describe("academic-years (server data)", () => {
  it("getAcademicYearSelectOptions hits the expected endpoint", () => {
    getAcademicYearSelectOptions();
    expect(mockedGetApi).toHaveBeenCalledWith("/academic/years/select-options/");
  });

  it("getAcademicYearsData combines cached years and current year", async () => {
    const result = await getAcademicYearsData();
    expect(mockedGetCachedAcademicYears).toHaveBeenCalled();
    expect(mockedGetCachedCurrentYear).toHaveBeenCalled();
    expect(result).toEqual({
      currentYear: { id: 1, status: "recommendation" },
      years: [{ id: 1 }],
    });
  });
});
