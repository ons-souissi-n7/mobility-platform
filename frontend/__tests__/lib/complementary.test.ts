import { describe, expect, it, vi } from "vitest";

import { browserApi } from "@/lib/api/browser-client";
import {
  deleteComplementaryMobility,
  fetchComplementaryMobilitiesAdmin,
  rejectMobility,
  updateComplementaryMobility,
  validateMobility,
} from "@/lib/api/complementary";

vi.mock("@/lib/api/browser-client", () => ({
  browserApi: vi.fn().mockResolvedValue({ results: [] }),
}));

const mockedBrowserApi = vi.mocked(browserApi);

describe("complementary", () => {
  it("fetchComplementaryMobilitiesAdmin builds query params and defaults page/page_size", () => {
    fetchComplementaryMobilitiesAdmin({
      status: "pending",
      student_search: "n7",
      experience_type: "internship",
      year_id: 1,
      page: 2,
      page_size: 10,
    });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/complementary/?status=pending&student_search=n7&experience_type=internship&year_id=1&page=2&page_size=10",
      { method: "GET" },
    );

    fetchComplementaryMobilitiesAdmin();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/complementary/?page=1&page_size=25", {
      method: "GET",
    });
  });

  it("validateMobility / rejectMobility / deleteComplementaryMobility / updateComplementaryMobility hit the expected endpoints", () => {
    validateMobility(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/complementary/1/validate/", {
      method: "POST",
    });

    rejectMobility(1, "incomplete");
    expect(mockedBrowserApi).toHaveBeenCalledWith("/complementary/1/reject/", {
      method: "POST",
      body: { reason: "incomplete" },
    });

    deleteComplementaryMobility(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/complementary/1/", {
      method: "DELETE",
    });

    updateComplementaryMobility(1, "validated", "");
    expect(mockedBrowserApi).toHaveBeenCalledWith("/complementary/1/", {
      method: "PATCH",
      body: { status: "validated", rejection_reason: "" },
    });
  });
});
