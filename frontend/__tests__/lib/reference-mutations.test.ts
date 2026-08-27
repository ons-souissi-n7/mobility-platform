import { describe, expect, it, vi } from "vitest";

import { browserApi } from "@/lib/api/browser-client";
import {
  createCountry,
  createDepartment,
  createLevel,
  createParcours,
  createUniversity,
  deleteCountry,
  deleteDepartment,
  deleteLevel,
  deleteParcours,
  deleteUniversity,
  fetchUniversitiesPage,
  forceDepartmentImport,
  forceLevelImport,
  forceUniversityImport,
  getDepartmentImportErrors,
  getDepartments,
  getLevelImportErrors,
  getLevels,
  getParcours,
  getUniversityImportErrors,
  ignoreDepartmentImport,
  ignoreLevelImport,
  ignoreUniversityImport,
  retryDepartmentImport,
  retryUniversityImport,
  syncDepartmentsFromPegase,
  syncLevelsFromPegase,
  syncUniversitiesFromMoveon,
  updateCountry,
  updateDepartment,
  updateLevel,
  updateParcours,
  updateUniversity,
} from "@/lib/api/reference-mutations";

vi.mock("@/lib/api/browser-client", () => ({
  browserApi: vi.fn().mockResolvedValue({}),
}));

const mockedBrowserApi = vi.mocked(browserApi);

describe("reference-mutations", () => {
  it("fetchUniversitiesPage builds query params and defaults page/page_size", () => {
    fetchUniversitiesPage({ search: "n7", country_id: 3 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/institutions/universities/?search=n7&country_id=3&page=1&page_size=25",
      { method: "GET" },
    );
  });

  it("fetchUniversitiesPage omits empty filters", () => {
    fetchUniversitiesPage();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/institutions/universities/?page=1&page_size=25",
      { method: "GET" },
    );
  });

  it("createCountry / updateCountry / deleteCountry hit the expected endpoints", () => {
    const payload = { name: "France", iso2: "FR" } as never;
    createCountry(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/countries/", {
      method: "POST",
      body: payload,
    });

    updateCountry(1, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/countries/1/", {
      method: "PUT",
      body: payload,
    });

    deleteCountry(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/countries/1/", {
      method: "DELETE",
    });
  });

  it("department CRUD + sync + import errors hit the expected endpoints", () => {
    const payload = { code: "GI", name: "Génie Industriel" } as never;
    createDepartment(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/departments/", {
      method: "POST",
      body: payload,
    });

    updateDepartment(2, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/departments/2/", {
      method: "PUT",
      body: payload,
    });

    deleteDepartment(2);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/departments/2/", {
      method: "DELETE",
    });

    getDepartments();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/departments/", {});

    syncDepartmentsFromPegase();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/departments/sync-pegase/",
      { method: "POST" },
    );

    getDepartmentImportErrors({ page: 2, page_size: 10 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/departments/import-errors/?page=2&page_size=10",
      {},
    );

    getDepartmentImportErrors();
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/departments/import-errors/?page=1&page_size=25",
      {},
    );

    const correction = { code: "GI2" };
    retryDepartmentImport(5, correction);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/departments/import-errors/5/retry/",
      { method: "PUT", body: correction },
    );

    ignoreDepartmentImport(5);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/departments/import-errors/5/ignore/",
      { method: "PUT" },
    );

    forceDepartmentImport(5);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/departments/import-errors/5/force-overwrite/",
      { method: "POST" },
    );
  });

  it("university CRUD + sync + import errors hit the expected endpoints", () => {
    const payload = { name: "MIT" } as never;
    createUniversity(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/institutions/universities/", {
      method: "POST",
      body: payload,
    });

    updateUniversity(7, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/institutions/universities/7/", {
      method: "PUT",
      body: payload,
    });

    deleteUniversity(7);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/institutions/universities/7/", {
      method: "DELETE",
    });

    syncUniversitiesFromMoveon();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/institutions/sync-moveon/", {
      method: "POST",
    });

    getUniversityImportErrors({ page: 3, page_size: 5 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/institutions/import-errors/?page=3&page_size=5",
      {},
    );

    const correction = { name: "MIT2" };
    retryUniversityImport(9, correction);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/institutions/import-errors/9/retry/",
      { method: "PUT", body: correction },
    );

    ignoreUniversityImport(9);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/institutions/import-errors/9/ignore/",
      { method: "PUT" },
    );

    forceUniversityImport(9);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/institutions/import-errors/9/force-overwrite/",
      { method: "POST" },
    );
  });

  it("level CRUD + sync + import errors hit the expected endpoints", () => {
    getLevels();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/levels/", {});

    const payload = { name: "M1" } as never;
    createLevel(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/levels/", {
      method: "POST",
      body: payload,
    });

    updateLevel(4, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/levels/4/", {
      method: "PUT",
      body: payload,
    });

    deleteLevel(4);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/levels/4/", {
      method: "DELETE",
    });

    syncLevelsFromPegase();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/levels/sync/", {
      method: "POST",
    });

    getLevelImportErrors({ page: 1, page_size: 25 });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/levels/import-errors/?page=1&page_size=25",
      {},
    );

    ignoreLevelImport(6);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/levels/import-errors/6/ignore/",
      { method: "PUT" },
    );

    forceLevelImport(6);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/levels/import-errors/6/force-overwrite/",
      { method: "POST" },
    );
  });

  it("parcours CRUD hits the expected endpoints, with and without department filter", () => {
    getParcours();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/parcours/", {});

    getParcours(8);
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/reference/parcours/?department_id=8",
      {},
    );

    const payload = { name: "Info" } as never;
    createParcours(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/parcours/", {
      method: "POST",
      body: payload,
    });

    updateParcours(3, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/parcours/3/", {
      method: "PUT",
      body: payload,
    });

    deleteParcours(3);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/reference/parcours/3/", {
      method: "DELETE",
    });
  });
});
