import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MobilityWorkspace } from "@/components/mobility/mobility-workspace";
import type { AcademicYear } from "@/lib/api/types";

vi.mock("@/lib/api/mobility-mutations", () => ({
  adjustAgreementYearInp: vi.fn(),
  createAgreement: vi.fn(),
  createMobilityCategory: vi.fn(),
  deleteAgreement: vi.fn(),
  deleteMobilityCategory: vi.fn(),
  downloadExcelTemplate: vi.fn(),
  exportAgreementsExcel: vi.fn(),
  fetchAgreementYearDepartments: vi.fn().mockResolvedValue([]),
  fetchAgreementYearsList: vi.fn().mockResolvedValue([]),
  fetchAgreements: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 200 }),
  fetchMobilityCategories: vi.fn().mockResolvedValue([]),
  fetchMobilityImportErrors: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  forceMobilityImport: vi.fn(),
  getMoveonMobilityImportErrors: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  ignoreMobilityImport: vi.fn(),
  importAgreementsFromExcel: vi.fn(),
  restoreAgreement: vi.fn(),
  retryMobilityImport: vi.fn(),
  syncMobilityFromMoveon: vi.fn(),
  syncMobilityCategoriesFromMoveon: vi.fn(),
  toggleAgreementYearActive: vi.fn(),
  updateAgreement: vi.fn(),
  updateAgreementYear: vi.fn(),
  updateAgreementYearDepartment: vi.fn(),
  updateMobilityCategory: vi.fn(),
  validateAgreementYear: vi.fn(),
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
  academicYears: [makeYear()],
  mobilityCategories: [],
  countries: [],
  currentYear: makeYear(),
  initialAgreementYears: [],
  initialAgreements: [],
  initialAllAgreements: [],
  initialAgreementYearDepartments: [],
  initialImportErrors: [],
  initialImportErrorsTotalCount: 0,
  initialExpiringAgreements: [],
  departments: [],
  mobilityLevels: [],
  universities: [],
};

describe("MobilityWorkspace", () => {
  it("renders without crashing with no data", () => {
    render(<MobilityWorkspace {...baseProps} currentYear={null} academicYears={[]} />);
    expect(document.body).toBeTruthy();
  });

  it("shows the accords/cadres tabs and stat cards", async () => {
    render(<MobilityWorkspace {...baseProps} />);
    await waitFor(() => {
      expect(screen.getByText("Accords total")).toBeInTheDocument();
    });
    expect(screen.getAllByText("Cadres").length).toBeGreaterThan(0);
    expect(screen.getByText("Accords de mobilité")).toBeInTheDocument();
    expect(screen.getByText("Cadres de mobilité")).toBeInTheDocument();
  });

  it("shows agreement count and cadre count from initial props", async () => {
    render(
      <MobilityWorkspace
        {...baseProps}
        initialAgreements={[
          {
            id: 1,
            name: "Accord MIT",
            partner_university_id: 1,
            partner_university_name: "MIT",
            category_id: null,
            category_name: null,
            direction: "outgoing",
            valid_from: null,
            valid_until: null,
            inp_total_places: 0,
            inp_institutions: "",
            remarks: "",
            level_ids: [],
            department_ids: [],
            country_name: "USA",
          } as never,
        ]}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText("Accord MIT")).toBeInTheDocument();
    });
  });

  it("shows an agreement import error with its message", async () => {
    render(
      <MobilityWorkspace
        {...baseProps}
        initialImportErrors={[
          {
            id: 1,
            source: "moveon",
            source_file: "moveon_accords.xlsx",
            entity: "agreement",
            external_id: "ext-1",
            payload: { name: "Accord cassé" },
            status: "error",
            error_message: "Université partenaire introuvable",
            imported_at: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]}
        initialImportErrorsTotalCount={1}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText("Université partenaire introuvable")).toBeInTheDocument();
    });
  });
});
