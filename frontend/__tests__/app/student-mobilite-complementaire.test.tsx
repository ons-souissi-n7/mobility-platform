import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import MobiliteComplementairePage from "@/app/student/mobilite-complementaire/page";

vi.mock("@/lib/auth", () => ({
  getCurrentIne: vi.fn().mockReturnValue("12345678A"),
}));
vi.mock("@/lib/api/student", () => ({
  declareComplementaryMobility: vi.fn(),
  fetchComplementaryCountries: vi.fn().mockResolvedValue([]),
  fetchComplementaryMobilities: vi.fn().mockResolvedValue([]),
  fetchStudentProfile: vi.fn().mockResolvedValue({
    ine: "12345678A",
    enrolled_years: [
      { academic_year_id: 1, academic_year_label: "2026-2027", academic_year_status: "recommendation" },
    ],
  }),
}));

describe("MobiliteComplementairePage", () => {
  it("renders without crashing and shows the year selector", async () => {
    render(<MobiliteComplementairePage />);
    await waitFor(() => {
      expect(screen.getAllByText("2026-2027").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Mobilité complémentaire")).toBeInTheDocument();
  });

  it("shows the declaration form and empty history message", async () => {
    render(<MobiliteComplementairePage />);
    await waitFor(() => {
      expect(screen.getByText("Aucune déclaration pour cette année.")).toBeInTheDocument();
    });
    expect(screen.getByText("Déclarer une nouvelle expérience")).toBeInTheDocument();
    expect(screen.getByLabelText(/type d.expérience/i)).toBeInTheDocument();
  });

  it("lists mobilities from the API and their status badge", async () => {
    const { fetchComplementaryMobilities } = await import("@/lib/api/student");
    vi.mocked(fetchComplementaryMobilities).mockResolvedValueOnce([
      {
        id: 1,
        experience_type: "Summer school",
        destination_country_name: "USA",
        destination_institution: "MIT",
        start_date: "2026-06-01",
        end_date: "2026-08-01",
        status: "pending",
        rejection_reason: "",
        document_url: null,
        document_name: null,
        created_at: "2026-01-01T00:00:00Z",
      } as never,
    ]);
    render(<MobiliteComplementairePage />);
    await waitFor(() => {
      expect(screen.getByText("Summer school")).toBeInTheDocument();
    });
  });

  it("hides the declaration form when the selected year is closed", async () => {
    const { fetchStudentProfile } = await import("@/lib/api/student");
    vi.mocked(fetchStudentProfile).mockResolvedValueOnce({
      ine: "12345678A",
      enrolled_years: [
        { academic_year_id: 1, academic_year_label: "2025-2026", academic_year_status: "closed" },
      ],
    } as never);
    render(<MobiliteComplementairePage />);
    await waitFor(() => {
      expect(screen.getByText(/Année clôturée/)).toBeInTheDocument();
    });
    expect(screen.queryByText("Déclarer une nouvelle expérience")).not.toBeInTheDocument();
  });
});
