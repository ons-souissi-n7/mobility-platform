import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { IncomingWorkspace } from "@/components/incoming/incoming-workspace";
import type { AcademicYear } from "@/lib/api/types";

vi.mock("@/lib/api/incoming-mutations", () => ({
  createIncomingStudent: vi.fn(),
  deleteIncomingStudent: vi.fn(),
  downloadIncomingTemplate: vi.fn(),
  exportIncomingExcel: vi.fn(),
  getIncomingImportErrors: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  getIncomingStatsCountry: vi.fn().mockResolvedValue([]),
  getIncomingStatsUniv: vi.fn().mockResolvedValue([]),
  ignoreIncomingImportError: vi.fn(),
  importIncomingFromExcel: vi.fn(),
  listIncomingStudents: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  updateIncomingStudent: vi.fn(),
}));

function makeYear(
  status: AcademicYear["status"] = "recommendation",
  overrides: Partial<AcademicYear> = {},
): AcademicYear {
  return {
    id: 1,
    label: "2026-2027",
    start_date: "2026-09-01",
    end_date: "2027-08-31",
    status,
    wishes_open_date: null,
    wishes_close_date: null,
    closed_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

const baseProps = {
  initialStudents: [],
  initialTotalCount: 0,
  initialImportErrors: [],
  initialImportErrorsCount: 0,
  countries: [],
  departments: [],
  levels: [],
  parcours: [],
  mobilityCategories: [],
  universities: [],
};

describe("IncomingWorkspace", () => {
  it("renders without crashing when there are no academic years", () => {
    render(<IncomingWorkspace {...baseProps} academicYears={[]} currentYear={null} />);
    expect(document.body).toBeTruthy();
  });

  it("shows the year label for the current year", async () => {
    const year = makeYear();
    render(<IncomingWorkspace {...baseProps} academicYears={[year]} currentYear={year} />);
    await waitFor(() => {
      expect(screen.getByText("2026-2027")).toBeInTheDocument();
    });
  });

  it("renders the initial student list without crashing", async () => {
    const year = makeYear();
    render(
      <IncomingWorkspace
        {...baseProps}
        academicYears={[year]}
        currentYear={year}
        initialStudents={[
          {
            id: 1,
            academic_year_id: 1,
            department_id: null,
            civility: "M",
            last_name: "Doe",
            first_name: "John",
            country_id: null,
            country_name: "USA",
            origin_university_id: null,
            origin_university_name: "MIT",
            birth_date: null,
            mobility_category_id: null,
            mobility_category_name: null,
            personal_email: "",
            n7_email: "",
            duration: "",
            level_id: null,
            parcours_id: null,
            remarks: "",
            internship_info: "",
            diploma_info: "",
            doctoral_continuation: false,
          } as never,
        ]}
        initialTotalCount={1}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText("Doe")).toBeInTheDocument();
    });
  });

  it("is read-only when the selected year is closed", async () => {
    const year = makeYear("closed");
    render(<IncomingWorkspace {...baseProps} academicYears={[year]} currentYear={year} />);
    await waitFor(() => {
      expect(screen.getByText(/2026-2027 \(clôturée\)/)).toBeInTheDocument();
    });
  });
});
