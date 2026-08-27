import { describe, expect, it, vi } from "vitest";

import { browserApi } from "@/lib/api/browser-client";
import {
  applyAcademicYearTransition,
  createAcademicYear,
  deleteAcademicYear,
  updateAcademicYear,
} from "@/lib/api/academic-year-mutations";

vi.mock("@/lib/api/browser-client", () => ({
  browserApi: vi.fn().mockResolvedValue({}),
}));

const mockedBrowserApi = vi.mocked(browserApi);

describe("academic-year-mutations", () => {
  it("createAcademicYear / updateAcademicYear / deleteAcademicYear hit the expected endpoints", () => {
    const payload = { label: "2026-2027" } as never;
    createAcademicYear(payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/academic/years/", {
      method: "POST",
      body: payload,
    });

    updateAcademicYear(1, payload);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/academic/years/1/", {
      method: "PUT",
      body: payload,
    });

    deleteAcademicYear(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/academic/years/1/", {
      method: "DELETE",
    });
  });

  it("applyAcademicYearTransition posts to the transition-specific endpoint", () => {
    applyAcademicYearTransition(1, "open-recommendation");
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/academic/years/1/open-recommendation/",
      { method: "POST" },
    );

    applyAcademicYearTransition(1, "close");
    expect(mockedBrowserApi).toHaveBeenCalledWith("/academic/years/1/close/", {
      method: "POST",
    });
  });
});
