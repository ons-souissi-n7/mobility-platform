import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import MobilitePage from "@/app/student/mobilite/page";

vi.mock("@/lib/auth", () => ({
  getCurrentIne: vi.fn().mockReturnValue("12345678A"),
}));
vi.mock("@/lib/api/student", () => ({
  fetchStudentAssignment: vi.fn().mockResolvedValue(null),
  fetchStudentProfile: vi.fn().mockResolvedValue({
    ine: "12345678A",
    enrolled_years: [
      { academic_year_id: 1, academic_year_label: "2026-2027", academic_year_status: "recommendation" },
    ],
  }),
  fetchStudentWishes: vi.fn().mockResolvedValue([]),
}));

describe("MobilitePage", () => {
  it("renders without crashing and shows the year label", async () => {
    render(<MobilitePage />);
    await waitFor(() => {
      expect(screen.getByText("2026-2027")).toBeInTheDocument();
    });
    expect(screen.getByText("Ma mobilité")).toBeInTheDocument();
  });

  it("shows an empty-wishes message and a not-yet-published banner", async () => {
    render(<MobilitePage />);
    await waitFor(() => {
      expect(screen.getByText("Aucun vœu enregistré pour cette année.")).toBeInTheDocument();
    });
    expect(
      screen.getByText("Les résultats ne sont pas encore publiés pour cette année."),
    ).toBeInTheDocument();
  });

  it("lists wishes returned by the API", async () => {
    const { fetchStudentWishes } = await import("@/lib/api/student");
    vi.mocked(fetchStudentWishes).mockResolvedValueOnce([
      { rank: 1, university_name: "MIT", agreement_name: "Accord MIT", country_name: "USA" } as never,
    ]);
    render(<MobilitePage />);
    await waitFor(() => {
      expect(screen.getByText("MIT")).toBeInTheDocument();
    });
  });

  it("shows the assignment result when the student is assigned", async () => {
    const { fetchStudentAssignment } = await import("@/lib/api/student");
    vi.mocked(fetchStudentAssignment).mockResolvedValueOnce({
      is_assigned: true,
      university_name: "MIT",
      country_name: "USA",
      agreement_name: "Accord MIT",
    } as never);
    render(<MobilitePage />);
    await waitFor(() => {
      expect(screen.getByText("Affecté(e) en mobilité internationale")).toBeInTheDocument();
    });
  });
});
