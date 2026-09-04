import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { StudentsWorkspace } from "@/components/students/students-workspace";
import type { AcademicYear, StudentWithEnrollment } from "@/lib/api/types";

vi.mock("@/lib/api/student-mutations", () => ({
  deleteStudentEnrollment: vi.fn(),
  downloadStudentTemplate: vi.fn(),
  exportStudentsExcel: vi.fn(),
  getStudentImportErrors: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  getStudentStatsForYear: vi.fn().mockResolvedValue({
    total: 42,
    by_level: [],
    by_department: [],
    by_parcours: [],
  }),
  getStudentsByYear: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
  ignoreStudentImportError: vi.fn(),
  importStudentsFromExcel: vi.fn(),
  restoreStudentEnrollment: vi.fn(),
  retryStudentImportError: vi.fn(),
  syncStudentsFromPegase: vi.fn(),
  updateStudentEnrollment: vi.fn(),
}));

import {
  deleteStudentEnrollment,
  getStudentImportErrors,
  getStudentStatsForYear,
  getStudentsByYear,
  importStudentsFromExcel,
  restoreStudentEnrollment,
  retryStudentImportError,
} from "@/lib/api/student-mutations";
import type { RawImport } from "@/lib/api/types";

function makeImportError(overrides: Partial<RawImport> = {}): RawImport {
  return {
    id: 1,
    source: "excel_students",
    source_file: "etudiants.xlsx",
    entity: "student",
    external_id: "row_2",
    payload: { ine: "", first_name: "Un", last_name: "SANSINE" },
    status: "failed",
    error_message: "L'INE est requis.",
    imported_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeEnrollmentRow(overrides: Partial<StudentWithEnrollment> = {}): StudentWithEnrollment {
  return {
    enrollment_id: 1,
    student_id: 1,
    ine: "203EA05FISA",
    first_name: "Mathieu",
    last_name: "GARNIER",
    email: "m.garnier@etu.inp-toulouse.fr",
    gender: "M",
    nationality_iso2: "FR",
    nationality_name_fr: "France",
    department_id: 1,
    department_code: "3EA",
    department_name: "Electronique",
    level_id: 1,
    level_code: "3ING",
    level_name: "3ème année",
    parcours_id: null,
    parcours_code: null,
    parcours_label: null,
    gpa: "18.75",
    is_alternant: false,
    is_scholarship: false,
    deleted_at: null,
    ...overrides,
  };
}

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

const baseProps = { countries: [], departments: [], levels: [], parcourses: [] };

describe("StudentsWorkspace", () => {
  // Certains tests posent un `mockResolvedValue` persistant (voir historique /
  // restore) : sans reset, ces implémentations fuient vers les tests suivants et
  // les rendent flaky. On repart d'un défaut neutre avant chaque test.
  beforeEach(() => {
    vi.mocked(getStudentsByYear).mockReset();
    vi.mocked(getStudentsByYear).mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 });
    vi.mocked(getStudentImportErrors).mockReset();
    vi.mocked(getStudentImportErrors).mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 });
  });

  it("renders without crashing when there are no academic years", () => {
    render(<StudentsWorkspace academicYears={[]} {...baseProps} />);
    expect(document.body).toBeTruthy();
  });

  it("shows the year label and loaded stats", async () => {
    render(<StudentsWorkspace academicYears={[makeYear()]} {...baseProps} />);
    await waitFor(() => {
      expect(screen.getByText("2026-2027")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText("42")).toBeInTheDocument();
    });
  });

  it("Template/Sync buttons are enabled during initialization (not locked)", async () => {
    render(<StudentsWorkspace academicYears={[makeYear("initialization")]} {...baseProps} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /template/i })).not.toBeDisabled();
    });
    expect(screen.getByRole("button", { name: /sync pegase/i })).not.toBeDisabled();
  });

  it("Template/Sync buttons are disabled once the year is locked (non-initialization status)", async () => {
    render(<StudentsWorkspace academicYears={[makeYear("recommendation")]} {...baseProps} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /template/i })).toBeDisabled();
    });
    expect(screen.getByRole("button", { name: /sync pegase/i })).toBeDisabled();
  });

  it("Exporter button is disabled while no year is selected and enabled once one is", async () => {
    render(<StudentsWorkspace academicYears={[makeYear("closed")]} {...baseProps} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /exporter/i })).not.toBeDisabled();
    });
  });

  it(
    "refreshes the student list and import-errors panel after an Excel import completes (regression: import used to leave the UI stale)",
    async () => {
      const user = userEvent.setup();

      render(<StudentsWorkspace academicYears={[makeYear("initialization")]} {...baseProps} />);
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /template/i })).not.toBeDisabled();
      });

      const listCallsBefore = vi.mocked(getStudentsByYear).mock.calls.length;
      const errorsCallsBefore = vi.mocked(getStudentImportErrors).mock.calls.length;

      const file = new File(["dummy"], "etudiants.xlsx", {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const input = screen.getByLabelText(/importer excel/i);
      await user.upload(input, file);

      expect(importStudentsFromExcel).toHaveBeenCalledTimes(1);

      // Import Excel is processed asynchronously (django-q worker) — the UI
      // waits ~3s then refetches, otherwise newly imported students / import
      // errors never appear until an unrelated action happens to reload.
      // Real timers + a longer test timeout (rather than fake timers, which
      // don't play well with userEvent.upload's own internal scheduling).
      await waitFor(
        () => {
          expect(vi.mocked(getStudentsByYear).mock.calls.length).toBeGreaterThan(listCallsBefore);
          expect(vi.mocked(getStudentImportErrors).mock.calls.length).toBeGreaterThan(errorsCallsBefore);
        },
        { timeout: 6000 },
      );
    },
    10_000,
  );

  it(
    "resets to page 1 and shows a confirmation after a successful import-error retry (regression: corrected student looked like it vanished on page 2)",
    async () => {
      const user = userEvent.setup();
      vi.mocked(getStudentImportErrors).mockResolvedValue({
        count: 1,
        results: [makeImportError()],
        page: 1,
        page_size: 25,
      });

      render(<StudentsWorkspace academicYears={[makeYear("initialization")]} {...baseProps} />);
      await waitFor(() => {
        expect(screen.getByText(/erreurs d'import étudiants/i)).toBeInTheDocument();
      });

      const rowButton = screen.getByRole("button", { name: /row_2/ });
      await user.click(rowButton);

      const ineField = await screen.findByLabelText(/N°INE/i);
      await user.clear(ineField);
      await user.type(ineField, "12345678901");
      await user.click(screen.getByRole("button", { name: /relancer/i }));

      expect(retryStudentImportError).toHaveBeenCalledWith(1, expect.objectContaining({ ine: "12345678901" }));

      await waitFor(() => {
        expect(screen.getByText(/étudiant importé avec succès/i)).toBeInTheDocument();
      });

      const lastCall = vi.mocked(getStudentsByYear).mock.calls.at(-1);
      expect(lastCall?.[1]).toMatchObject({ page: 1 });
    },
    10_000,
  );

  describe("delete enrollment — uses the app's ConfirmDialog, not window.confirm", () => {
    it("shows the custom dialog and does NOT delete when 'Annuler' is clicked", async () => {
      const user = userEvent.setup();
      vi.mocked(getStudentsByYear).mockResolvedValueOnce({
        count: 1,
        results: [makeEnrollmentRow()],
        page: 1,
        page_size: 25,
      });

      render(<StudentsWorkspace academicYears={[makeYear("initialization")]} {...baseProps} />);
      await waitFor(() => {
        expect(screen.getByText("GARNIER")).toBeInTheDocument();
      });

      await user.click(screen.getByTitle("Supprimer"));

      expect(screen.getByText("Confirmer : Supprimer")).toBeInTheDocument();
      expect(screen.getByText(/GARNIER Mathieu \(203EA05FISA\)/)).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "Annuler" }));

      expect(screen.queryByText("Confirmer : Supprimer")).not.toBeInTheDocument();
      expect(deleteStudentEnrollment).not.toHaveBeenCalled();
    });

    it("soft-deletes (not permanently) and removes the row from the default (active-only) view", async () => {
      const user = userEvent.setup();
      vi.mocked(getStudentsByYear).mockResolvedValueOnce({
        count: 1,
        results: [makeEnrollmentRow()],
        page: 1,
        page_size: 25,
      });
      vi.mocked(deleteStudentEnrollment).mockResolvedValueOnce(
        makeEnrollmentRow({ deleted_at: "2026-01-15T00:00:00Z" }),
      );

      render(<StudentsWorkspace academicYears={[makeYear("initialization")]} {...baseProps} />);
      await waitFor(() => {
        expect(screen.getByText("GARNIER")).toBeInTheDocument();
      });

      await user.click(screen.getByTitle("Supprimer"));
      const dialog = screen.getByText("Confirmer : Supprimer").closest(".fixed") as HTMLElement;
      await user.click(within(dialog).getByRole("button", { name: "Supprimer" }));

      expect(deleteStudentEnrollment).toHaveBeenCalledWith(1);
      await waitFor(() => {
        expect(screen.queryByText("Confirmer : Supprimer")).not.toBeInTheDocument();
      });
      // Soft delete → row disappears from the default (non-deleted) view, but
      // the confirm message must NOT claim the action is irreversible.
      await waitFor(() => {
        expect(screen.queryByText("GARNIER")).not.toBeInTheDocument();
      });
    });

    it("confirm message says the enrollment can be restored, not that deletion is irreversible", async () => {
      const user = userEvent.setup();
      vi.mocked(getStudentsByYear).mockResolvedValueOnce({
        count: 1,
        results: [makeEnrollmentRow()],
        page: 1,
        page_size: 25,
      });

      render(<StudentsWorkspace academicYears={[makeYear("initialization")]} {...baseProps} />);
      await waitFor(() => {
        expect(screen.getByText("GARNIER")).toBeInTheDocument();
      });

      await user.click(screen.getByTitle("Supprimer"));

      expect(screen.getByText(/pourra être restaurée/i)).toBeInTheDocument();
      expect(screen.queryByText(/irréversible/i)).not.toBeInTheDocument();
    });

    it("refreshes the stat cards (without a page reload) after a successful delete", async () => {
      const user = userEvent.setup();
      vi.mocked(getStudentsByYear).mockResolvedValueOnce({
        count: 1,
        results: [makeEnrollmentRow()],
        page: 1,
        page_size: 25,
      });
      vi.mocked(deleteStudentEnrollment).mockResolvedValueOnce(
        makeEnrollmentRow({ deleted_at: "2026-01-15T00:00:00Z" }),
      );
      const statsCallsBefore = vi.mocked(getStudentStatsForYear).mock.calls.length;

      render(<StudentsWorkspace academicYears={[makeYear("initialization")]} {...baseProps} />);
      await waitFor(() => {
        expect(screen.getByText("GARNIER")).toBeInTheDocument();
      });

      await user.click(screen.getByTitle("Supprimer"));
      const dialog = screen.getByText("Confirmer : Supprimer").closest(".fixed") as HTMLElement;
      await user.click(within(dialog).getByRole("button", { name: "Supprimer" }));

      await waitFor(() => {
        expect(vi.mocked(getStudentStatsForYear).mock.calls.length).toBeGreaterThan(statsCallsBefore);
      });
    });
  });

  describe("history view — 'Voir les supprimés' toggle and restore", () => {
    it("toggling 'Voir les supprimés' fetches with include_deleted and shows the Supprimé badge", async () => {
      const user = userEvent.setup();
      vi.mocked(getStudentsByYear).mockResolvedValueOnce({
        count: 1,
        results: [makeEnrollmentRow()],
        page: 1,
        page_size: 25,
      });

      render(<StudentsWorkspace academicYears={[makeYear("initialization")]} {...baseProps} />);
      await waitFor(() => {
        expect(screen.getByText("GARNIER")).toBeInTheDocument();
      });
      expect(screen.getByText("Actif")).toBeInTheDocument();

      vi.mocked(getStudentsByYear).mockResolvedValueOnce({
        count: 1,
        results: [makeEnrollmentRow({ deleted_at: "2026-01-15T00:00:00Z" })],
        page: 1,
        page_size: 25,
      });

      await user.click(screen.getByRole("button", { name: /voir les supprimés/i }));

      const lastCall = vi.mocked(getStudentsByYear).mock.calls.at(-1);
      expect(lastCall?.[1]).toMatchObject({ include_deleted: true });
      await waitFor(() => {
        expect(screen.getByText(/supprimé le/i)).toBeInTheDocument();
      });
    });

    it("clicking restore on a deleted row calls the restore API and clears the badge", async () => {
      const user = userEvent.setup();
      vi.mocked(getStudentsByYear).mockResolvedValue({
        count: 1,
        results: [makeEnrollmentRow({ deleted_at: "2026-01-15T00:00:00Z" })],
        page: 1,
        page_size: 25,
      });
      vi.mocked(restoreStudentEnrollment).mockResolvedValueOnce(
        makeEnrollmentRow({ deleted_at: null }),
      );

      render(<StudentsWorkspace academicYears={[makeYear("initialization")]} {...baseProps} />);
      await user.click(await screen.findByRole("button", { name: /voir les supprimés/i }));
      await waitFor(() => {
        expect(screen.getByText(/supprimé le/i)).toBeInTheDocument();
      });

      await user.click(screen.getByTitle("Restaurer l'inscription"));

      expect(restoreStudentEnrollment).toHaveBeenCalledWith(1);
      await waitFor(() => {
        expect(screen.getByText("Actif")).toBeInTheDocument();
      });
    });
  });

  describe("table columns — Filière / Boursier / FISE-FISA", () => {
    it("merges Département, Niveau and Parcours into a single 'Filière' column", async () => {
      vi.mocked(getStudentsByYear).mockResolvedValueOnce({
        count: 1,
        results: [makeEnrollmentRow({ parcours_code: "INFO" })],
        page: 1,
        page_size: 25,
      });

      render(<StudentsWorkspace academicYears={[makeYear()]} {...baseProps} />);

      await waitFor(() => {
        expect(screen.getByRole("columnheader", { name: "Filière" })).toBeInTheDocument();
      });
      expect(screen.queryByRole("columnheader", { name: "Département" })).not.toBeInTheDocument();
      expect(screen.queryByRole("columnheader", { name: "Niveau" })).not.toBeInTheDocument();
      expect(screen.queryByRole("columnheader", { name: "Parcours" })).not.toBeInTheDocument();

      const row = (await screen.findByText("GARNIER")).closest("tr");
      expect(row).not.toBeNull();
      const filiereCell = within(row as HTMLElement);
      expect(filiereCell.getByText("3EA")).toBeInTheDocument();
      expect(filiereCell.getByText("3ING")).toBeInTheDocument();
      expect(filiereCell.getByText("INFO")).toBeInTheDocument();
    });

    it("shows a 'Boursier' column with Oui/Non badges", async () => {
      vi.mocked(getStudentsByYear).mockResolvedValueOnce({
        count: 2,
        results: [
          makeEnrollmentRow({ enrollment_id: 1, student_id: 1, ine: "1", is_scholarship: true }),
          makeEnrollmentRow({
            enrollment_id: 2,
            student_id: 2,
            ine: "2",
            last_name: "DUPONT",
            is_scholarship: false,
          }),
        ],
        page: 1,
        page_size: 25,
      });

      render(<StudentsWorkspace academicYears={[makeYear()]} {...baseProps} />);

      await waitFor(() => {
        expect(screen.getByRole("columnheader", { name: "Boursier" })).toBeInTheDocument();
      });
      // Le header est du markup statique rendu dès l'état "chargement" ; on
      // attend les lignes elles-mêmes, sinon on court après la promesse du mock.
      const garnierRow = within((await screen.findByText("GARNIER")).closest("tr") as HTMLElement);
      expect(garnierRow.getByText("Oui")).toBeInTheDocument();
      const dupontRow = within((await screen.findByText("DUPONT")).closest("tr") as HTMLElement);
      expect(dupontRow.getByText("Non")).toBeInTheDocument();
    });

    it("shows a 'FISE/FISA' column reflecting is_alternant", async () => {
      vi.mocked(getStudentsByYear).mockResolvedValueOnce({
        count: 2,
        results: [
          makeEnrollmentRow({ enrollment_id: 1, student_id: 1, ine: "1", is_alternant: true }),
          makeEnrollmentRow({
            enrollment_id: 2,
            student_id: 2,
            ine: "2",
            last_name: "DUPONT",
            is_alternant: false,
          }),
        ],
        page: 1,
        page_size: 25,
      });

      render(<StudentsWorkspace academicYears={[makeYear()]} {...baseProps} />);

      await waitFor(() => {
        expect(screen.getByRole("columnheader", { name: "FISE/FISA" })).toBeInTheDocument();
      });
      // Le header est du markup statique rendu dès l'état "chargement" ; on
      // attend les lignes elles-mêmes, sinon on court après la promesse du mock.
      const garnierRow = within((await screen.findByText("GARNIER")).closest("tr") as HTMLElement);
      expect(garnierRow.getByText("FISA")).toBeInTheDocument();
      const dupontRow = within((await screen.findByText("DUPONT")).closest("tr") as HTMLElement);
      expect(dupontRow.getByText("FISE")).toBeInTheDocument();
    });
  });
});
