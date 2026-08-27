import { describe, expect, it, vi } from "vitest";

import { getApi } from "@/lib/api/client";
import { getImportReportDetail, getImportReportsData } from "@/lib/api/import-reports";

vi.mock("@/lib/api/client", () => ({
  getApi: vi.fn().mockResolvedValue([]),
}));

const mockedGetApi = vi.mocked(getApi);

describe("import-reports", () => {
  it("getImportReportsData fetches reports and academic years in parallel", async () => {
    mockedGetApi.mockResolvedValueOnce([{ id: 1 }]).mockResolvedValueOnce([{ id: 2 }]);
    const result = await getImportReportsData();
    expect(mockedGetApi).toHaveBeenCalledWith("/imports/");
    expect(mockedGetApi).toHaveBeenCalledWith("/academic/years/");
    expect(result).toEqual({ reports: [{ id: 1 }], academicYears: [{ id: 2 }] });
  });

  it("getImportReportDetail hits the expected endpoint", async () => {
    await getImportReportDetail(5);
    expect(mockedGetApi).toHaveBeenCalledWith("/imports/5/");
  });
});
