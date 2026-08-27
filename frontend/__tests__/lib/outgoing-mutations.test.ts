import { describe, expect, it, vi } from "vitest";

import { browserApi, browserApiUpload } from "@/lib/api/browser-client";
import { downloadBlob } from "@/lib/api/download-utils";
import {
  deleteStudentWish,
  downloadWishTemplate,
  exportWishesExcel,
  getAssignmentAgreementYears,
  getAssignmentResults,
  getAssignmentStats,
  getAssignmentsForYear,
  getWishImportErrors,
  getWishesByYear,
  importOverridesFromExcel,
  importWishesFromExcel,
  patchAssignmentResult,
  publishAssignment,
  retryWishImportError,
  syncWishesFromMoveon,
  updateStudentWish,
  validateAssignment,
} from "@/lib/api/outgoing-mutations";

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

describe("outgoing-mutations", () => {
  it("assignment read helpers hit the expected endpoints", () => {
    getAssignmentsForYear(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/outgoing/assignments/?year_id=1&page_size=20",
      { method: "GET" },
    );

    getAssignmentResults(1, { slot_type: "s", department_id: 2, search: "n7", page: 1, page_size: 10 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/outgoing/assignments/1/results/?slot_type=s&department_id=2&search=n7&page=1&page_size=10",
      { method: "GET" },
    );

    getAssignmentResults(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/outgoing/assignments/1/results/", {
      method: "GET",
    });

    getAssignmentStats(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/outgoing/assignments/1/stats/", {
      method: "GET",
    });

    getAssignmentAgreementYears(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/outgoing/assignments/1/agreement-years/",
      { method: "GET" },
    );
  });

  it("wish import errors: get / retry hit the expected endpoints", () => {
    getWishImportErrors({ page: 2, page_size: 10, year_id: 3 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/outgoing/wishes/import-errors/?page=2&page_size=10&year_id=3",
      { method: "GET" },
    );

    getWishImportErrors();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/outgoing/wishes/import-errors/?page=1&page_size=25",
      { method: "GET" },
    );

    const correction = { rank: 1 };
    retryWishImportError(5, correction);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/outgoing/wishes/import-errors/5/retry/",
      { method: "PUT", body: correction },
    );
  });

  it("sync / by-year / template / import / export hit the expected endpoints", async () => {
    syncWishesFromMoveon(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/outgoing/wishes/sync-moveon/1/", {
      method: "POST",
    });

    getWishesByYear(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/outgoing/wishes/by-year/1/?page=1&page_size=500",
      { method: "GET" },
    );

    await downloadWishTemplate(1);
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/outgoing/wishes/template/1/",
      "template_voeux.xlsx",
    );

    const file = new File(["a"], "voeux.xlsx");
    await importWishesFromExcel(1, file);
    expect(mockedBrowserApiUpload).toHaveBeenCalledWith(
      "/outgoing/wishes/import-excel/1/",
      expect.any(FormData),
    );

    await exportWishesExcel(1, { deptCode: "GI" });
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/outgoing/wishes/export-excel/1/?dept_code=GI",
      "voeux.xlsx",
    );
  });

  it("assignment actions and result overrides hit the expected endpoints", () => {
    validateAssignment(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/outgoing/assignments/1/validate/", {
      method: "POST",
    });

    publishAssignment(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/outgoing/assignments/1/publish/", {
      method: "POST",
    });

    const patch = { override_agreement_year_id: 2, override_reason: "r" };
    patchAssignmentResult(1, 3, patch);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/outgoing/assignments/1/results/3/",
      { method: "PATCH", body: patch },
    );

    deleteStudentWish(9);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/outgoing/wishes/9/", {
      method: "DELETE",
    });

    updateStudentWish(9, 2);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/outgoing/wishes/9/", {
      method: "PATCH",
      body: { rank: 2 },
    });
  });

  it("importOverridesFromExcel uploads the file as multipart form data", async () => {
    const file = new File(["a"], "overrides.xlsx");
    await importOverridesFromExcel(1, file);
    expect(mockedBrowserApiUpload).toHaveBeenCalledWith(
      "/outgoing/assignments/1/import-overrides/",
      expect.any(FormData),
    );
  });
});
