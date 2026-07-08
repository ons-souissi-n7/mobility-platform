import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { OutgoingWorkspace } from "@/components/outgoing/outgoing-workspace";
import type { AcademicYear } from "@/lib/api/types";

// ── Mock all direct API calls made inside OutgoingWorkspace ────────────────
vi.mock("@/lib/api/outgoing-mutations", () => ({
  downloadWishTemplate: vi.fn(),
  exportWishesExcel: vi.fn(),
  getAssignmentResults: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  getAssignmentStats: vi.fn().mockResolvedValue(null),
  getAssignmentsForYear: vi.fn().mockResolvedValue([]),
  getWishImportErrors: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  getWishesByYear: vi.fn().mockResolvedValue([]),
  importOverridesFromExcel: vi.fn(),
  importWishesFromExcel: vi.fn(),
  publishAssignment: vi.fn(),
  retryWishImportError: vi.fn(),
  syncWishesFromMoveon: vi.fn(),
  validateAssignment: vi.fn(),
}));
vi.mock("@/lib/api/academic-year-mutations", () => ({
  applyAcademicYearTransition: vi.fn(),
}));
vi.mock("@/lib/api/mobility-mutations", () => ({
  getValidAgreements: vi.fn().mockResolvedValue([]),
}));
vi.mock("@/lib/api/student-mutations", () => ({
  getStudentSelectOptions: vi.fn().mockResolvedValue([]),
  ignoreStudentImportError: vi.fn(),
}));

// ── Helpers ────────────────────────────────────────────────────────────────

function makeYear(
  status: AcademicYear["status"] = "initialization",
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

// ── Tests ──────────────────────────────────────────────────────────────────

describe("OutgoingWorkspace", () => {
  it("renders without crashing with empty years list", () => {
    render(<OutgoingWorkspace academicYears={[]} />);
    // Si aucune année, le sélecteur est vide mais le composant ne crash pas
    expect(document.body).toBeTruthy();
  });

  it("shows the year label in the selector", async () => {
    render(<OutgoingWorkspace academicYears={[makeYear()]} />);
    await waitFor(() => {
      expect(screen.getByText("2026-2027")).toBeInTheDocument();
    });
  });

  it("Template button is disabled in initialization phase", async () => {
    render(<OutgoingWorkspace academicYears={[makeYear("initialization")]} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /template/i })).toBeDisabled();
    });
  });

  it("Template button is enabled in import phase", async () => {
    render(<OutgoingWorkspace academicYears={[makeYear("import")]} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /template/i })).not.toBeDisabled();
    });
  });

  it("Template button is disabled in pre_assignment phase", async () => {
    render(<OutgoingWorkspace academicYears={[makeYear("pre_assignment")]} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /template/i })).toBeDisabled();
    });
  });

  it("Template button is disabled in validation phase", async () => {
    render(<OutgoingWorkspace academicYears={[makeYear("validation")]} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /template/i })).toBeDisabled();
    });
  });

  it("Exporter button is enabled for closed year (always enabled)", async () => {
    render(<OutgoingWorkspace academicYears={[makeYear("closed")]} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /exporter/i })).not.toBeDisabled();
    });
  });

  it("Exporter button is enabled for open year", async () => {
    render(<OutgoingWorkspace academicYears={[makeYear("recommendation")]} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /exporter/i })).not.toBeDisabled();
    });
  });

  it("Sync MoveON button is disabled in pre_assignment phase", async () => {
    render(<OutgoingWorkspace academicYears={[makeYear("pre_assignment")]} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sync moveon/i })).toBeDisabled();
    });
  });

  it("Lancer l'affectation button is disabled in pre_assignment phase", async () => {
    render(<OutgoingWorkspace academicYears={[makeYear("pre_assignment")]} />);
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /lancer l.affectation/i }),
      ).toBeDisabled();
    });
  });
});
