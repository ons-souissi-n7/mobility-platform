import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AccordsPage from "@/app/student/accords/page";

vi.mock("@/lib/auth", () => ({
  getCurrentIne: vi.fn().mockReturnValue("12345678A"),
}));
vi.mock("@/lib/api/student", () => ({
  fetchStudentAgreements: vi.fn().mockResolvedValue([]),
  fetchStudentProfile: vi.fn().mockResolvedValue({
    ine: "12345678A",
    enrolled_years: [
      { academic_year_id: 1, academic_year_label: "2026-2027", academic_year_status: "recommendation" },
    ],
  }),
}));

describe("AccordsPage", () => {
  it("renders without crashing and shows an empty-state message", async () => {
    render(<AccordsPage />);
    await waitFor(() => {
      expect(screen.getByText("Aucun accord disponible pour cette année.")).toBeInTheDocument();
    });
    expect(screen.getByText("Accords disponibles")).toBeInTheDocument();
  });

  it("lists agreements returned by the API", async () => {
    const { fetchStudentAgreements } = await import("@/lib/api/student");
    vi.mocked(fetchStudentAgreements).mockResolvedValueOnce([
      {
        agreement_year_id: 1,
        university_name: "MIT",
        country_name: "USA",
        agreement_name: "Accord MIT",
        direction: "outgoing",
        n7_places: 5,
        dept_quotas: [{ department_id: 1, department_code: "GI", effective_places: 2 }],
        valid_from: "2026-09-01",
        valid_until: "2027-08-31",
      } as never,
    ]);
    render(<AccordsPage />);
    await waitFor(() => {
      expect(screen.getByText("MIT")).toBeInTheDocument();
    });
    expect(screen.getByText("Sortant")).toBeInTheDocument();
    expect(screen.getByText("1 accord correspondant à votre profil")).toBeInTheDocument();
  });
});
