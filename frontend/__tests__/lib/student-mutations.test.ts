import { describe, expect, it, vi } from "vitest";

import { browserApi, browserApiUpload } from "@/lib/api/browser-client";
import { downloadBlob } from "@/lib/api/download-utils";
import {
  deleteStudentEnrollment,
  downloadStudentTemplate,
  exportStudentsExcel,
  getReconciliationCandidates,
  getStudentDetail,
  getStudentImportErrors,
  getStudentSelectOptions,
  getStudentStatsForYear,
  getStudentsByYear,
  ignoreStudentImportError,
  importStudentsFromExcel,
  retryStudentImportError,
  syncStudentsFromPegase,
  updateStudentEnrollment,
} from "@/lib/api/student-mutations";

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

describe("student-mutations", () => {
  it("importStudentsFromExcel uploads the file as multipart form data", async () => {
    const file = new File(["a"], "etudiants.xlsx");
    await importStudentsFromExcel(1, file);
    expect(mockedBrowserApiUpload).toHaveBeenCalledWith(
      "/students/students/import-excel/1/",
      expect.any(FormData),
    );
  });

  it("sync / stats / select-options hit the expected endpoints", () => {
    syncStudentsFromPegase(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/sync-pegase/1/",
      { method: "POST" },
    );

    getStudentStatsForYear(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/stats/?academic_year_id=1",
      { method: "GET" },
    );

    getStudentSelectOptions(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/select-options/?academic_year_id=1",
      { method: "GET" },
    );

    getStudentSelectOptions();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/select-options/",
      { method: "GET" },
    );
  });

  it("getStudentsByYear builds query params and defaults page/page_size", () => {
    getStudentsByYear(1, { search: "n7", department_id: 2, level_id: 3, parcours_id: 4, page: 2, page_size: 10 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/by-year/1/?search=n7&department_id=2&level_id=3&parcours_id=4&page=2&page_size=10",
      { method: "GET" },
    );

    getStudentsByYear(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/by-year/1/?page=1&page_size=25",
      { method: "GET" },
    );
  });

  it("import errors: get / ignore / retry hit the expected endpoints", () => {
    getStudentImportErrors({ page: 2, page_size: 10, year_id: 1 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/import-errors/?page=2&page_size=10&year_id=1",
      { method: "GET" },
    );

    getStudentImportErrors();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/import-errors/?page=1&page_size=25",
      { method: "GET" },
    );

    ignoreStudentImportError(5);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/import-errors/5/ignore/",
      { method: "PUT" },
    );

    const correction = { ine: "12345678A" };
    retryStudentImportError(5, correction);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/import-errors/5/retry/",
      { method: "PUT", body: correction },
    );
  });

  it("getReconciliationCandidates / enrollment CRUD hit the expected endpoints", () => {
    getReconciliationCandidates(5);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/import-errors/5/candidates/",
      { method: "GET" },
    );

    deleteStudentEnrollment(7);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/enrollments/7/",
      { method: "DELETE" },
    );

    const patch = { department_id: 1, level_id: 2, parcours_id: null, gpa: null, is_alternant: false, is_scholarship: false };
    updateStudentEnrollment(7, patch);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/students/students/enrollments/7/",
      { method: "PATCH", body: patch },
    );

    getStudentDetail(9);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/students/students/9/", {
      method: "GET",
    });
  });

  it("downloadStudentTemplate / exportStudentsExcel delegate to downloadBlob", async () => {
    await downloadStudentTemplate();
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/students/students/template/",
      "template_etudiants.xlsx",
    );

    await exportStudentsExcel(1, { levelId: "2", deptId: "3", parcoursId: "4" });
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/students/students/export-excel/1/?level_id=2&dept_id=3&parcours_id=4",
      "etudiants.xlsx",
    );
  });
});
