import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { InternshipsWorkspace } from "@/components/internships/internships-workspace";
import type { AcademicYear } from "@/lib/api/types";

vi.mock("@/lib/api/internship-mutations", () => ({
  addInternshipImportAsNew: vi.fn(),
  createInternship: vi.fn(),
  deleteInternship: vi.fn(),
  downloadInternshipTemplate: vi.fn(),
  exportInternshipsExcel: vi.fn(),
  forceInternshipImport: vi.fn(),
  getInternshipImportErrors: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  ignoreInternshipImport: vi.fn(),
  importInternshipsFromExcel: vi.fn(),
  syncInternshipsFromEudonet: vi.fn(),
  updateInternship: vi.fn(),
}));
vi.mock("@/lib/api/browser-client", () => ({
  browserApi: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
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

const baseProps = {
  countries: [],
  initialImportErrors: [],
  initialImportErrorsTotalCount: 0,
};

describe("InternshipsWorkspace", () => {
  it("renders without crashing when there are no academic years", () => {
    render(
      <InternshipsWorkspace
        {...baseProps}
        initialInternships={[]}
        initialTotalCount={0}
        academicYears={[]}
        currentYear={null}
      />,
    );
    expect(document.body).toBeTruthy();
  });

  it("shows initial internships", async () => {
    const year = makeYear();
    render(
      <InternshipsWorkspace
        {...baseProps}
        initialInternships={[
          {
            id: 1,
            student_id: 1,
            student_name: "Jean Dupont",
            company_name: "Acme Corp",
            country_id: null,
            country_name: null,
            city: "Toulouse",
            title: "Stage ingénieur",
            internship_type: "PFE",
            status_code: "in_progress",
            status_label: "En cours",
            start_date: "2026-01-01",
            end_date: "2026-06-01",
            weeks_in_company: 20,
            school_tutor: "",
            company_tutor: "",
            academic_year_id: 1,
          } as never,
        ]}
        initialTotalCount={1}
        academicYears={[year]}
        currentYear={year}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    });
  });
});
