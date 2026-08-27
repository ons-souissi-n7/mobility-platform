import { describe, expect, it, vi } from "vitest";

import { getAffectationsData } from "@/lib/api/outgoing";
import { getCachedAcademicYears } from "@/lib/api/server-cache";

vi.mock("@/lib/api/server-cache", () => ({
  getCachedAcademicYears: vi.fn().mockResolvedValue([{ id: 1, label: "2026-2027" }]),
}));

const mockedGetCachedAcademicYears = vi.mocked(getCachedAcademicYears);

describe("outgoing (server data)", () => {
  it("getAffectationsData wraps the cached academic years", async () => {
    const result = await getAffectationsData();
    expect(mockedGetCachedAcademicYears).toHaveBeenCalled();
    expect(result).toEqual({ academicYears: [{ id: 1, label: "2026-2027" }] });
  });
});
