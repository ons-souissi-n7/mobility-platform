import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ImportReportsWorkspace } from "@/components/imports/import-reports-workspace";
import type { AcademicYear, ImportReportList } from "@/lib/api/types";

function makeReport(overrides: Partial<ImportReportList> = {}): ImportReportList {
  return {
    id: 1,
    source: "pegase",
    source_display: "Pégase",
    academic_year_label: "2026-2027",
    total: 10,
    success_count: 8,
    error_count: 2,
    duplicate_count: 0,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  } as never;
}

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

describe("ImportReportsWorkspace", () => {
  it("renders without crashing when there are no reports", () => {
    render(<ImportReportsWorkspace reports={[]} academicYears={[]} />);
    expect(document.body).toBeTruthy();
  });

  it("shows the report source and status counts", () => {
    render(
      <ImportReportsWorkspace
        reports={[makeReport()]}
        academicYears={[makeYear()]}
      />,
    );
    expect(screen.getAllByText("Pégase").length).toBeGreaterThan(0);
    expect(screen.getByText("8 ok")).toBeInTheDocument();
    expect(screen.getByText("2 erreurs")).toBeInTheDocument();
  });

  it("shows a single error label (no plural) when there is exactly one error", () => {
    render(
      <ImportReportsWorkspace
        reports={[makeReport({ error_count: 1, duplicate_count: 3 })]}
        academicYears={[makeYear()]}
      />,
    );
    expect(screen.getByText("1 erreur")).toBeInTheDocument();
    expect(screen.getByText("3 doublons")).toBeInTheDocument();
  });

  it("shows a dash placeholder when the report has zero total", () => {
    render(
      <ImportReportsWorkspace
        reports={[makeReport({ total: 0, success_count: 0, error_count: 0, duplicate_count: 0 })]}
        academicYears={[makeYear()]}
      />,
    );
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });
});
