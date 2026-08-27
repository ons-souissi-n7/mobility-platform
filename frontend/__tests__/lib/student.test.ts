import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  declareComplementaryMobility,
  fetchComplementaryCountries,
  fetchComplementaryMobilities,
  fetchStudentAgreements,
  fetchStudentAssignment,
  fetchStudentProfile,
  fetchStudentRecommendations,
  fetchStudentWishes,
} from "@/lib/api/student";

describe("student (browser client)", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn();
    document.cookie = "auth_token=; path=/; max-age=0";
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("returns null for a 404 profile without throwing", async () => {
    vi.mocked(global.fetch).mockResolvedValue({ status: 404, ok: false } as Response);
    const result = await fetchStudentProfile("12345678A");
    expect(result).toBeNull();
  });

  it("fetchStudentProfile returns the parsed JSON on success", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({ ine: "12345678A" }),
    } as Response);
    const result = await fetchStudentProfile("12345678A");
    expect(result).toEqual({ ine: "12345678A" });
    const [url] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toContain("/student/12345678A/profile/");
  });

  it("list endpoints default to an empty array when the API returns 404", async () => {
    vi.mocked(global.fetch).mockResolvedValue({ status: 404, ok: false } as Response);
    expect(await fetchStudentAgreements("12345678A")).toEqual([]);
    expect(await fetchStudentWishes("12345678A")).toEqual([]);
    expect(await fetchStudentRecommendations("12345678A")).toEqual([]);
    expect(await fetchComplementaryCountries()).toEqual([]);
    expect(await fetchComplementaryMobilities("12345678A")).toEqual([]);
  });

  it("appends year_id to the query string when provided", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => [],
    } as Response);
    await fetchStudentAgreements("12345678A", 3);
    const [url] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toContain("year_id=3");
  });

  it("fetchStudentAssignment returns null (not []) when absent", async () => {
    vi.mocked(global.fetch).mockResolvedValue({ status: 404, ok: false } as Response);
    expect(await fetchStudentAssignment("12345678A")).toBeNull();
  });

  it("throws a formatted error when the API responds with a non-ok, non-404 status", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      status: 400,
      ok: false,
      text: async () => JSON.stringify({ detail: "Requête invalide" }),
    } as Response);
    await expect(fetchStudentProfile("12345678A")).rejects.toThrow("Requête invalide");
  });

  it("declareComplementaryMobility posts multipart form data with query params", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1 }),
    } as Response);
    const file = new File(["a"], "justificatif.pdf");
    await declareComplementaryMobility(
      "12345678A",
      {
        academic_year_id: 1,
        experience_type: "internship",
        country_id: 2,
        destination_institution: "MIT",
        start_date: "2026-01-01",
        end_date: "2026-06-01",
      },
      file,
    );
    const [url, options] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toContain("/complementary/student/12345678A/?");
    expect(url).toContain("academic_year_id=1");
    expect((options as RequestInit).method).toBe("POST");
    expect((options as RequestInit).body).toBeInstanceOf(FormData);
  });
});
