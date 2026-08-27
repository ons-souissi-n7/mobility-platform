import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import RecommandationsPage from "@/app/student/recommandations/page";

vi.mock("@/lib/auth", () => ({
  getCurrentIne: vi.fn().mockReturnValue("12345678A"),
}));
vi.mock("@/lib/api/student", () => ({
  fetchStudentProfile: vi.fn().mockResolvedValue({
    ine: "12345678A",
    enrolled_years: [
      { academic_year_id: 1, academic_year_label: "2026-2027", academic_year_status: "recommendation" },
    ],
  }),
  fetchStudentRecommendations: vi.fn().mockResolvedValue([]),
}));

describe("RecommandationsPage", () => {
  it("renders without crashing and shows the year label", async () => {
    render(<RecommandationsPage />);
    await waitFor(() => {
      expect(screen.getByText("2026-2027")).toBeInTheDocument();
    });
    expect(screen.getByText("Recommandations")).toBeInTheDocument();
  });

  it("shows an empty-state message when there are no recommendations", async () => {
    render(<RecommandationsPage />);
    await waitFor(() => {
      expect(screen.getByText("Aucune destination éligible pour votre profil cette année.")).toBeInTheDocument();
    });
  });

  it("lists recommendations with score badges", async () => {
    const { fetchStudentRecommendations } = await import("@/lib/api/student");
    vi.mocked(fetchStudentRecommendations).mockResolvedValueOnce([
      {
        agreement_year_id: 1,
        university_name: "MIT",
        agreement_name: "Accord MIT",
        country_name: "USA",
        score: 0.87,
        model_based: true,
      } as never,
    ]);
    render(<RecommandationsPage />);
    await waitFor(() => {
      expect(screen.getByText("MIT")).toBeInTheDocument();
    });
    expect(screen.getByText("87%")).toBeInTheDocument();
  });

  it("shows the 'not yet open' message before the recommendation phase", async () => {
    const { fetchStudentProfile } = await import("@/lib/api/student");
    vi.mocked(fetchStudentProfile).mockResolvedValueOnce({
      ine: "12345678A",
      enrolled_years: [
        { academic_year_id: 1, academic_year_label: "2026-2027", academic_year_status: "initialization" },
      ],
    } as never);
    render(<RecommandationsPage />);
    await waitFor(() => {
      expect(
        screen.getByText("La phase de recommandation n'est pas encore ouverte pour cette année."),
      ).toBeInTheDocument();
    });
  });
});
