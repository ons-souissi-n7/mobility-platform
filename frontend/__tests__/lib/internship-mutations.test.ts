import { describe, expect, it, vi } from "vitest";

import { browserApi, browserApiUpload } from "@/lib/api/browser-client";
import { downloadBlob } from "@/lib/api/download-utils";
import {
  addInternshipImportAsNew,
  createInternship,
  deleteInternship,
  downloadInternshipTemplate,
  exportInternshipsExcel,
  forceInternshipImport,
  getInternshipImportErrors,
  getInternshipReconciliationCandidates,
  ignoreInternshipImport,
  importInternshipsFromExcel,
  retryInternshipImport,
  syncInternshipsFromEudonet,
  updateInternship,
} from "@/lib/api/internship-mutations";

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

describe("internship-mutations", () => {
  it("internship CRUD hits the expected endpoints", () => {
    const payload = { company_name: "Acme" } as never;
    createInternship(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/internships/", {
      method: "POST",
      body: payload,
    });

    updateInternship(1, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/internships/1/", {
      method: "PUT",
      body: payload,
    });

    deleteInternship(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/internships/1/", {
      method: "DELETE",
    });
  });

  it("sync hits the expected endpoint, with and without year filter", () => {
    syncInternshipsFromEudonet(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/internships/sync/?year_id=1", {
      method: "POST",
    });

    syncInternshipsFromEudonet();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/internships/sync/", {
      method: "POST",
    });
  });

  it("importInternshipsFromExcel uploads the file as multipart form data", async () => {
    const file = new File(["a"], "stages.xlsx");
    await importInternshipsFromExcel(1, file);
    expect(mockedBrowserApiUpload).toHaveBeenCalledWith(
      "/internships/import/?year_id=1",
      expect.any(FormData),
    );
  });

  it("exportInternshipsExcel delegates to downloadBlob and downloadInternshipTemplate opens a tab", async () => {
    await exportInternshipsExcel(1, 2);
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/internships/export/?year_id=1&country_id=2",
      "stages.xlsx",
    );

    await exportInternshipsExcel();
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/internships/export/?",
      "stages.xlsx",
    );

    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
    downloadInternshipTemplate(1);
    expect(openSpy).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/internships/template/?year_id=1",
      "_blank",
    );
    openSpy.mockRestore();
  });

  it("import errors: get / retry / ignore / force / add hit the expected endpoints", () => {
    getInternshipImportErrors({ yearId: 1, page: 2, pageSize: 10 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/internships/import-errors/?year_id=1&page=2&page_size=10",
      {},
    );

    getInternshipImportErrors();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/internships/import-errors/?page=1&page_size=25",
      {},
    );

    retryInternshipImport(5);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/internships/import-errors/5/retry/",
      { method: "POST" },
    );

    ignoreInternshipImport(5);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/internships/import-errors/5/ignore/",
      { method: "POST" },
    );

    const forcePayload = { payload: { company_name: "Acme" } };
    forceInternshipImport(5, forcePayload);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/internships/import-errors/5/force/",
      { method: "POST", body: forcePayload },
    );

    addInternshipImportAsNew(5);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/internships/import-errors/5/add/",
      { method: "POST" },
    );

    getInternshipReconciliationCandidates(5);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/internships/import-errors/5/candidates/",
      { method: "GET" },
    );
  });
});
