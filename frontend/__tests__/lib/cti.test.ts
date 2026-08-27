import { describe, expect, it, vi } from "vitest";

import { browserApi } from "@/lib/api/browser-client";
import { downloadBlob } from "@/lib/api/download-utils";
import {
  downloadCtiExport,
  getCtiDuration,
  getCtiHistory,
  getCtiStats,
  refreshCtiDuration,
} from "@/lib/api/cti";

vi.mock("@/lib/api/browser-client", () => ({
  browserApi: vi.fn().mockResolvedValue({}),
}));
vi.mock("@/lib/api/download-utils", () => ({
  downloadBlob: vi.fn().mockResolvedValue(undefined),
  publicApiBaseUrl: "http://localhost:8000/api/v1",
}));

const mockedBrowserApi = vi.mocked(browserApi);
const mockedDownloadBlob = vi.mocked(downloadBlob);

describe("cti", () => {
  it("duration / history endpoints hit the expected endpoints", () => {
    getCtiDuration("12345678A");
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/cti/students/12345678A/duration/",
      { method: "GET" },
    );

    refreshCtiDuration("12345678A");
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/cti/students/12345678A/duration/refresh/",
      { method: "POST" },
    );

    getCtiHistory("12345678A");
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/cti/students/12345678A/history/",
      { method: "GET" },
    );
  });

  it("downloadCtiExport delegates to downloadBlob with a year-scoped filename", () => {
    downloadCtiExport(1);
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/cti/export/?academic_year_id=1",
      "rapport_cti_1.xlsx",
    );
  });

  it("getCtiStats hits the expected endpoint", () => {
    getCtiStats(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/cti/stats/?academic_year_id=1",
      { method: "GET" },
    );
  });
});
