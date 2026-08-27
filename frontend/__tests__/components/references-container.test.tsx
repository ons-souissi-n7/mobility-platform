import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ReferencesContainer } from "@/components/references/references-container";

vi.mock("@/lib/api/reference-mutations", () => ({
  createCountry: vi.fn(),
  createDepartment: vi.fn(),
  createLevel: vi.fn(),
  createParcours: vi.fn(),
  createUniversity: vi.fn(),
  deleteCountry: vi.fn(),
  deleteDepartment: vi.fn(),
  deleteLevel: vi.fn(),
  deleteParcours: vi.fn(),
  deleteUniversity: vi.fn(),
  fetchUniversitiesPage: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  forceDepartmentImport: vi.fn(),
  forceLevelImport: vi.fn(),
  forceUniversityImport: vi.fn(),
  getDepartmentImportErrors: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  getDepartments: vi.fn().mockResolvedValue([]),
  getLevelImportErrors: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  getLevels: vi.fn().mockResolvedValue([]),
  getUniversityImportErrors: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  ignoreDepartmentImport: vi.fn(),
  ignoreLevelImport: vi.fn(),
  ignoreUniversityImport: vi.fn(),
  retryDepartmentImport: vi.fn(),
  retryUniversityImport: vi.fn(),
  syncDepartmentsFromPegase: vi.fn(),
  syncLevelsFromPegase: vi.fn(),
  syncUniversitiesFromMoveon: vi.fn(),
  updateCountry: vi.fn(),
  updateDepartment: vi.fn(),
  updateLevel: vi.fn(),
  updateParcours: vi.fn(),
  updateUniversity: vi.fn(),
}));

vi.mock("@/lib/actions/cache-revalidation", () => ({
  revalidateDepartments: vi.fn(),
  revalidateLevels: vi.fn(),
  revalidateParcours: vi.fn(),
  revalidateUniversities: vi.fn(),
}));

const baseProps = {
  initialCountries: [],
  initialDepartments: [],
  initialUniversities: { count: 0, results: [], page: 1, page_size: 25 },
  initialUniversityImportErrors: [],
  initialUniversityImportErrorsCount: 0,
  initialDepartmentImportErrors: [],
  initialDepartmentImportErrorsCount: 0,
  initialMobilityLevels: [],
  initialLevelImportErrors: [],
  initialLevelImportErrorsCount: 0,
  initialParcours: [],
  currentYear: null,
};

describe("ReferencesContainer", () => {
  it("renders without crashing with empty reference data", () => {
    render(<ReferencesContainer {...baseProps} />);
    expect(document.body).toBeTruthy();
  });

  it("shows the reference stat cards with counts from initial data", async () => {
    render(
      <ReferencesContainer
        {...baseProps}
        initialDepartments={[{ id: 1, code: "GI", name: "Génie Industriel" } as never]}
        initialCountries={[{ id: 1, name: "France", iso2: "FR" } as never]}
      />,
    );
    await waitFor(() => {
      expect(screen.getAllByText("Departements").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Referentiels")).toBeInTheDocument();
  });
});
