import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { StudentImportErrorsPanel } from "@/components/students/student-import-errors-panel";
import type { RawImport } from "@/lib/api/types";

function makeError(overrides: Partial<RawImport> = {}): RawImport {
  return {
    id: 1,
    source: "pegase",
    source_file: "import.xlsx",
    external_id: "INE123",
    payload: { ine: "INE123", first_name: "Jean", last_name: "Dupont" },
    status: "error",
    error_message: "INE introuvable",
    imported_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

const defaultProps = {
  countries: [],
  departments: [],
  levels: [],
  parcourses: [],
  isBusy: false,
  onIgnore: vi.fn(),
  onRetry: vi.fn(),
};

describe("StudentImportErrorsPanel", () => {
  it("renders the panel title with error count", () => {
    render(
      <StudentImportErrorsPanel
        {...defaultProps}
        errors={[makeError()]}
        title="Erreurs import étudiants"
      />,
    );
    expect(screen.getByText(/erreurs import étudiants/i)).toBeInTheDocument();
  });

  it("returns null when errors list is empty", () => {
    const { container } = render(
      <StudentImportErrorsPanel {...defaultProps} errors={[]} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders error entry with external_id", () => {
    render(
      <StudentImportErrorsPanel
        {...defaultProps}
        errors={[makeError({ external_id: "INE999" })]}
      />,
    );
    expect(screen.getByText(/INE999/)).toBeInTheDocument();
  });

  it("renders error message", () => {
    render(
      <StudentImportErrorsPanel
        {...defaultProps}
        errors={[makeError({ error_message: "Département introuvable: MFEE" })]}
      />,
    );
    expect(screen.getByText(/Département introuvable: MFEE/)).toBeInTheDocument();
  });

  it("expands an error row on click to show payload", async () => {
    const user = userEvent.setup();
    const error = makeError({
      payload: { ine: "INE123", first_name: "Jean" },
    });
    render(
      <StudentImportErrorsPanel {...defaultProps} errors={[error]} />,
    );
    const row = screen.getByText(/INE123/);
    await user.click(row);
    expect(screen.getByText("Jean")).toBeInTheDocument();
  });

  it("renders multiple errors", () => {
    render(
      <StudentImportErrorsPanel
        {...defaultProps}
        errors={[
          makeError({ id: 1, external_id: "INE001" }),
          makeError({ id: 2, external_id: "INE002" }),
        ]}
      />,
    );
    expect(screen.getByText(/INE001/)).toBeInTheDocument();
    expect(screen.getByText(/INE002/)).toBeInTheDocument();
  });
});
