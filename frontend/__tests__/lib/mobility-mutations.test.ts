import { describe, expect, it, vi } from "vitest";

import { browserApi, browserApiUpload } from "@/lib/api/browser-client";
import { downloadBlob } from "@/lib/api/download-utils";
import {
  adjustAgreementYearInp,
  createAgreement,
  createAgreementYear,
  createAgreementYearDepartment,
  createMobilityCategory,
  deleteAgreement,
  deleteAgreementYear,
  deleteAgreementYearDepartment,
  deleteMobilityCategory,
  downloadExcelTemplate,
  exportAgreementsExcel,
  fetchAgreementYearDepartments,
  fetchAgreementYearsList,
  fetchAgreements,
  fetchMobilityCategories,
  fetchMobilityImportErrors,
  forceMobilityImport,
  getAgreements,
  getMoveonMobilityImportErrors,
  getValidAgreements,
  ignoreMobilityImport,
  importAgreementsFromExcel,
  initializeCurrentYear,
  redistributeAgreementYear,
  retryMobilityImport,
  syncMobilityCategoriesFromMoveon,
  syncMobilityFromMoveon,
  toggleAgreementYearActive,
  updateAgreement,
  updateAgreementYear,
  updateAgreementYearDepartment,
  updateMobilityCategory,
  validateAgreementYear,
} from "@/lib/api/mobility-mutations";

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

describe("mobility-mutations", () => {
  it("fetchAgreements builds query params with the 200 default page_size", () => {
    fetchAgreements({ search: "n7", country_id: 1, is_active: true, page: 2 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreements/?search=n7&country_id=1&is_active=true&page_size=200&page=2",
      { method: "GET" },
    );
  });

  it("fetchAgreements omits empty filters", () => {
    fetchAgreements();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreements/?page_size=200",
      { method: "GET" },
    );
  });

  it("read helpers unwrap PagedResponse.results", async () => {
    await fetchAgreementYearDepartments();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-year-departments/?page=1&page_size=500",
      { method: "GET" },
    );

    await fetchAgreementYearsList();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-years/?page=1&page_size=500",
      { method: "GET" },
    );

    await getAgreements();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreements/?page_size=500",
      { method: "GET" },
    );

    await getValidAgreements();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreements/?valid_only=true&page_size=500",
      { method: "GET" },
    );
  });

  it("fetchMobilityCategories / fetchMobilityImportErrors hit the expected endpoints", () => {
    fetchMobilityCategories();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-categories/",
      { method: "GET" },
    );

    fetchMobilityImportErrors(2, 10);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/raw-imports/moveon-errors/?page=2&page_size=10",
      { method: "GET" },
    );

    fetchMobilityImportErrors();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/raw-imports/moveon-errors/?page=1&page_size=25",
      { method: "GET" },
    );
  });

  it("forceMobilityImport posts to the force-overwrite endpoint", () => {
    forceMobilityImport(42);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/imports/raw/42/force-overwrite/",
      { method: "POST" },
    );
  });

  it("agreement CRUD hits the expected endpoints", () => {
    const payload = { name: "Accord X" } as never;
    createAgreement(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/mobility/agreements/", {
      method: "POST",
      body: payload,
    });

    updateAgreement(1, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/mobility/agreements/1/", {
      method: "PUT",
      body: payload,
    });

    deleteAgreement(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/mobility/agreements/1/", {
      method: "DELETE",
    });
  });

  it("agreement year CRUD + actions hit the expected endpoints", () => {
    const payload = { agreement_id: 1 } as never;
    createAgreementYear(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/mobility/agreement-years/", {
      method: "POST",
      body: payload,
    });

    updateAgreementYear(2, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/mobility/agreement-years/2/", {
      method: "PUT",
      body: payload,
    });

    toggleAgreementYearActive(2);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-years/2/toggle-active/",
      { method: "POST" },
    );

    validateAgreementYear(2);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-years/2/validate/",
      { method: "POST", body: { validated_by: "Administrateur" } },
    );

    validateAgreementYear(2, "Alice");
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-years/2/validate/",
      { method: "POST", body: { validated_by: "Alice" } },
    );

    redistributeAgreementYear(2);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-years/2/redistribute/",
      { method: "POST" },
    );

    adjustAgreementYearInp(2, 15);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-years/2/adjust-inp/",
      { method: "POST", body: { inp_total_places: 15 } },
    );

    deleteAgreementYear(2);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/mobility/agreement-years/2/", {
      method: "DELETE",
    });
  });

  it("agreement year department CRUD hits the expected endpoints", () => {
    const payload = { agreement_year_id: 1, department_id: 2 } as never;
    createAgreementYearDepartment(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-year-departments/",
      { method: "POST", body: payload },
    );

    updateAgreementYearDepartment(3, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-year-departments/3/",
      { method: "PUT", body: payload },
    );

    deleteAgreementYearDepartment(3);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-year-departments/3/",
      { method: "DELETE" },
    );
  });

  it("mobility category CRUD + sync hits the expected endpoints", () => {
    const payload = { name: "Stage" };
    createMobilityCategory(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-categories/",
      { method: "POST", body: payload },
    );

    updateMobilityCategory(4, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-categories/4/",
      { method: "PUT", body: payload },
    );

    deleteMobilityCategory(4);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-categories/4/",
      { method: "DELETE" },
    );

    syncMobilityCategoriesFromMoveon();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/agreement-categories/sync/",
      { method: "POST" },
    );
  });

  it("sync & init hit the expected endpoints", () => {
    syncMobilityFromMoveon();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/mobility/sync-moveon/", {
      method: "POST",
    });

    initializeCurrentYear();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/mobility/initialize-year/", {
      method: "POST",
    });
  });

  it("import errors: get / ignore / retry hit the expected endpoints", () => {
    getMoveonMobilityImportErrors({ page: 2, page_size: 5 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/raw-imports/moveon-errors/?page=2&page_size=5",
      {},
    );

    getMoveonMobilityImportErrors();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/raw-imports/moveon-errors/?page=1&page_size=25",
      {},
    );

    ignoreMobilityImport(7);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/raw-imports/7/ignore/",
      { method: "PUT" },
    );

    const retryPayload = { name: "Accord Y" };
    retryMobilityImport(7, retryPayload);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/mobility/raw-imports/7/retry/",
      { method: "PUT", body: retryPayload },
    );
  });

  it("importAgreementsFromExcel uploads the file as multipart form data", async () => {
    const file = new File(["a,b"], "accords.xlsx");
    await importAgreementsFromExcel(file);

    expect(mockedBrowserApiUpload).toHaveBeenCalledWith(
      "/mobility/import-excel/",
      expect.any(FormData),
    );
    const formData = mockedBrowserApiUpload.mock.calls[0][1] as FormData;
    expect(formData.get("file")).toBe(file);
  });

  it("downloadExcelTemplate opens the template URL in a new tab", () => {
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
    downloadExcelTemplate();
    expect(openSpy).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/mobility/excel-template/",
      "_blank",
    );
    openSpy.mockRestore();
  });

  it("exportAgreementsExcel builds the query string and delegates to downloadBlob", async () => {
    await exportAgreementsExcel({
      yearLabel: "2026-2027",
      country: "FR",
      category: "all",
      activity: "active",
    });
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/mobility/agreements/export-excel/?year_label=2026-2027&country=FR&activity=active",
      "accords.xlsx",
    );
  });

  it("exportAgreementsExcel works with no filters", async () => {
    await exportAgreementsExcel();
    expect(mockedDownloadBlob).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/mobility/agreements/export-excel/?",
      "accords.xlsx",
    );
  });
});
