import { describe, expect, it, vi } from "vitest";

import { browserApi, browserApiUpload } from "@/lib/api/browser-client";
import { downloadBlob } from "@/lib/api/download-utils";
import {
  createIncomingStudent,
  deleteIncomingStudent,
  downloadIncomingTemplate,
  exportIncomingExcel,
  forceIncomingImportError,
  getIncomingImportErrors,
  getIncomingStatsCountry,
  getIncomingStatsUniv,
  ignoreIncomingImportError,
  importIncomingFromExcel,
  listIncomingStudents,
  updateIncomingStudent,
} from "@/lib/api/incoming-mutations";

vi.mock("@/lib/api/browser-client", () => ({
  browserApi: vi.fn().mockResolvedValue({ results: [] }),
  browserApiUpload: vi.fn().mockResolvedValue({ task_id: "t1", message: "ok" }),
  publicApiBaseUrl: "http://localhost:8000/api/v1",
}));
vi.mock("@/lib/api/download-utils", () => ({
  downloadBlob: vi.fn().mockResolvedValue(undefined),
  publicApiBaseUrl: "http://localhost:8000/api/v1",
}));

const mockedBrowserApi = vi.mocked(browserApi);
const mockedBrowserApiUpload = vi.mocked(browserApiUpload);
const mockedDownloadBlob = vi.mocked(downloadBlob);

describe("incoming-mutations", () => {
  it("listIncomingStudents builds query params from all filters", () => {
    listIncomingStudents({
      year_id: 1,
      country_id: 2,
      department_id: 3,
      level_id: 4,
      parcours_id: 5,
      mobility_category_id: 6,
      university_id: 7,
      search: "n7",
      page: 2,
      page_size: 10,
    });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/incoming/?year_id=1&country_id=2&department_id=3&level_id=4&parcours_id=5&mobility_category_id=6&university_id=7&search=n7&page=2&page_size=10",
      { method: "GET" },
    );

    listIncomingStudents();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/?page=1&page_size=25", {
      method: "GET",
    });
  });

  it("importIncomingFromExcel uploads the file as multipart form data", async () => {
    const file = new File(["a"], "entrants.xlsx");
    await importIncomingFromExcel(1, file);
    expect(mockedBrowserApiUpload).toHaveBeenCalledWith(
      "/incoming/import/?year_id=1",
      expect.any(FormData),
    );
  });

  it("downloadIncomingTemplate / exportIncomingExcel delegate to downloadBlob", async () => {
    await downloadIncomingTemplate(1);
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/incoming/template/?year_id=1",
      "template_entrants.xlsx",
    );

    await exportIncomingExcel(1, { countryId: 2, departmentId: 3 });
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/incoming/export/?year_id=1&country_id=2&department_id=3",
      "entrants.xlsx",
    );

    await exportIncomingExcel();
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/incoming/export/?",
      "entrants.xlsx",
    );
  });

  it("import errors: get / ignore / force hit the expected endpoints", () => {
    getIncomingImportErrors({ year_id: 1, page: 2, page_size: 10 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/incoming/import-errors/?year_id=1&page=2&page_size=10",
      { method: "GET" },
    );

    getIncomingImportErrors();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/incoming/import-errors/?page=1&page_size=25",
      { method: "GET" },
    );

    ignoreIncomingImportError(5);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/import-errors/5/ignore/", {
      method: "POST",
    });

    const payload = { country_id: "2" };
    forceIncomingImportError(5, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/import-errors/5/force/", {
      method: "POST",
      body: JSON.stringify({ payload }),
    });
  });

  it("incoming student CRUD hits the expected endpoints", () => {
    const payload = { last_name: "Doe" } as never;
    createIncomingStudent(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/", {
      method: "POST",
      body: payload,
    });

    updateIncomingStudent(1, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/1/", {
      method: "PUT",
      body: payload,
    });

    deleteIncomingStudent(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/1/", {
      method: "DELETE",
    });
  });

  it("stats endpoints hit the expected endpoints, with and without year filter", () => {
    getIncomingStatsUniv(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/stats/univ/?year_id=1", {
      method: "GET",
    });

    getIncomingStatsUniv();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/stats/univ/", {
      method: "GET",
    });

    getIncomingStatsCountry(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/stats/country/?year_id=1", {
      method: "GET",
    });

    getIncomingStatsCountry();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/incoming/stats/country/", {
      method: "GET",
    });
  });
});
