import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ComplementaryWorkspace } from "@/components/complementary/complementary-workspace";
import type { AcademicYear } from "@/lib/api/types";

vi.mock("@/lib/api/complementary", () => ({
  fetchComplementaryMobilitiesAdmin: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  rejectMobility: vi.fn(),
  validateMobility: vi.fn(),
}));

function makeYear(overrides: Partial<AcademicYear> = {}): AcademicYear {
  return {
    id: 1,
    label: "2026-2027",
    start_date: "2026-09-01",
    end_date: "2027-08-31",
    status: "recommendation",
    wishes_open_date: null,
    wishes_close_date: null,
    closed_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("ComplementaryWorkspace", () => {
  it("renders without crashing when there are no academic years", () => {
    render(
      <ComplementaryWorkspace
        initialMobilities={[]}
        initialTotalCount={0}
        academicYears={[]}
        currentYear={null}
      />,
    );
    expect(document.body).toBeTruthy();
  });

  it("shows initial mobilities and stat count", async () => {
    const year = makeYear();
    render(
      <ComplementaryWorkspace
        initialMobilities={[
          {
            id: 1,
            student_ine: "12345678A",
            student_last_name: "Dupont",
            student_first_name: "Jean",
            academic_year_id: 1,
            experience_type: "internship",
            country_id: 1,
            country_name: "USA",
            destination_institution: "MIT",
            start_date: "2026-01-01",
            end_date: "2026-06-01",
            status: "pending",
            rejection_reason: "",
            document_url: null,
            created_at: "2026-01-01T00:00:00Z",
          } as never,
        ]}
        initialTotalCount={1}
        academicYears={[year]}
        currentYear={year}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText("Dupont Jean")).toBeInTheDocument();
    });
  });
});
