import { describe, expect, it, vi } from "vitest";

import { browserApi } from "@/lib/api/browser-client";
import { downloadBlob } from "@/lib/api/download-utils";
import {
  exportAnalytics,
  getCountryBreakdown,
  getCountryOptions,
  getDepartmentBreakdown,
  getDepartmentOptions,
  getMobilityTrends,
  getUniversityBreakdown,
  getUniversityOptions,
} from "@/lib/api/analytics";

vi.mock("@/lib/api/browser-client", () => ({
  browserApi: vi.fn().mockResolvedValue({}),
}));
vi.mock("@/lib/api/download-utils", () => ({
  downloadBlob: vi.fn().mockResolvedValue(undefined),
  publicApiBaseUrl: "http://localhost:8000/api/v1",
}));

const mockedBrowserApi = vi.mocked(browserApi);
const mockedDownloadBlob = vi.mocked(downloadBlob);

describe("analytics", () => {
  it("getMobilityTrends defaults to 5 years and accepts an override", () => {
    getMobilityTrends();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/analytics/trends/?years=5", {
      method: "GET",
    });

    getMobilityTrends(3);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/analytics/trends/?years=3", {
      method: "GET",
    });
  });

  it("breakdown endpoints build query params with and without id filters", () => {
    getDepartmentBreakdown(4, [1, 2]);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/analytics/by-department/?years=4&dept_ids=1%2C2",
      { method: "GET" },
    );
    getDepartmentBreakdown();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/analytics/by-department/?years=5", {
      method: "GET",
    });

    getCountryBreakdown(4, [3]);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/analytics/by-country/?years=4&country_ids=3",
      { method: "GET" },
    );

    getUniversityBreakdown(4, [7]);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/analytics/by-university/?years=4&univ_ids=7",
      { method: "GET" },
    );
  });

  it("select-option endpoints hit the expected endpoints", () => {
    getDepartmentOptions();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/departments/select-options/",
      { method: "GET" },
    );

    getCountryOptions();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/countries/select-options/",
      { method: "GET" },
    );

    getUniversityOptions();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/institutions/universities/select-options/",
      { method: "GET" },
    );
  });

  it("exportAnalytics delegates to downloadBlob with a year-scoped filename", () => {
    exportAnalytics(3);
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/analytics/export/?years=3",
      "statistiques_mobilite_3ans.xlsx",
    );
  });
});
