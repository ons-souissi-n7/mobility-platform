import { describe, expect, it, vi } from "vitest";

import { getStudentsData, getWishesData } from "@/lib/api/students";
import {
  getCachedAcademicYears,
  getCachedCountries,
  getCachedDepartments,
  getCachedLevels,
  getCachedParcours,
} from "@/lib/api/server-cache";

vi.mock("@/lib/api/server-cache", () => ({
  getCachedAcademicYears: vi.fn().mockResolvedValue([{ id: 1 }]),
  getCachedCountries: vi.fn().mockResolvedValue([{ id: 2 }]),
  getCachedDepartments: vi.fn().mockResolvedValue([{ id: 3 }]),
  getCachedLevels: vi.fn().mockResolvedValue([{ id: 4 }]),
  getCachedParcours: vi.fn().mockResolvedValue([{ id: 5 }]),
}));

describe("students (server data)", () => {
  it("getStudentsData aggregates all reference data in parallel", async () => {
    const result = await getStudentsData();
    expect(vi.mocked(getCachedAcademicYears)).toHaveBeenCalled();
    expect(vi.mocked(getCachedDepartments)).toHaveBeenCalled();
    expect(vi.mocked(getCachedLevels)).toHaveBeenCalled();
    expect(vi.mocked(getCachedParcours)).toHaveBeenCalled();
    expect(vi.mocked(getCachedCountries)).toHaveBeenCalled();
    expect(result).toEqual({
      academicYears: [{ id: 1 }],
      departments: [{ id: 3 }],
      levels: [{ id: 4 }],
      parcourses: [{ id: 5 }],
      countries: [{ id: 2 }],
    });
  });

  it("getWishesData only fetches academic years", async () => {
    const result = await getWishesData();
    expect(result).toEqual({ academicYears: [{ id: 1 }] });
  });
});
