import { render, screen, within } from "@testing-library/react";
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

  describe("Boursier / FISE-FISA — regression: false was silently invisible", () => {
    it("shows Boursier: Oui and FISE/FISA: FISA when both true", async () => {
      const user = userEvent.setup();
      const error = makeError({
        payload: { ine: "", last_name: "SOUISSI", is_scholarship: true, is_alternant: true },
      });
      render(<StudentImportErrorsPanel {...defaultProps} errors={[error]} />);
      await user.click(screen.getByText("INE123"));

      const payloadSection = within(screen.getByText("Enregistrement complet").parentElement as HTMLElement);
      expect(payloadSection.getByText("Boursier")).toBeInTheDocument();
      expect(payloadSection.getByText("Oui")).toBeInTheDocument();
      expect(payloadSection.getByText("FISE/FISA")).toBeInTheDocument();
      expect(payloadSection.getByText("FISA")).toBeInTheDocument();
    });

    it("shows Boursier: Non and FISE/FISA: FISE when both false (false must not be filtered out as 'empty')", async () => {
      const user = userEvent.setup();
      const error = makeError({
        payload: { ine: "", last_name: "SOUISSI", is_scholarship: false, is_alternant: false },
      });
      render(<StudentImportErrorsPanel {...defaultProps} errors={[error]} />);
      await user.click(screen.getByText("INE123"));

      const payloadSection = within(screen.getByText("Enregistrement complet").parentElement as HTMLElement);
      expect(payloadSection.getByText("Boursier")).toBeInTheDocument();
      expect(payloadSection.getByText("Non")).toBeInTheDocument();
      expect(payloadSection.getByText("FISE/FISA")).toBeInTheDocument();
      expect(payloadSection.getByText("FISE")).toBeInTheDocument();
    });

    it("correction form pre-fills Boursier/FISE-FISA from the payload (fixes: dropdown used to come up blank)", async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn().mockResolvedValue(undefined);
      const error = makeError({
        payload: {
          ine: "",
          last_name: "SOUISSI",
          first_name: "Ons",
          is_scholarship: true,
          is_alternant: true,
        },
      });
      render(<StudentImportErrorsPanel {...defaultProps} errors={[error]} onRetry={onRetry} />);
      await user.click(screen.getByText("INE123"));

      const scholarshipSelect = screen.getByLabelText("Boursier") as HTMLSelectElement;
      const alternantSelect = screen.getByLabelText("FISE/FISA") as HTMLSelectElement;
      expect(scholarshipSelect.value).toBe("true");
      expect(alternantSelect.value).toBe("true");

      // Pre-filled from the stored payload — sent back as-is on retry, same
      // as every other field in this form (GPA, nationality, etc.).
      const ineField = screen.getByLabelText("N°INE");
      await user.type(ineField, "12345678901");
      await user.click(screen.getByRole("button", { name: /relancer/i }));

      const correction = onRetry.mock.calls[0][1];
      expect(correction.ine).toBe("12345678901");
      expect(correction.is_scholarship).toBe(true);
      expect(correction.is_alternant).toBe(true);
    });

    it("correction form sends the changed value when Boursier is corrected", async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn().mockResolvedValue(undefined);
      const error = makeError({
        payload: { ine: "", last_name: "SOUISSI", is_scholarship: true, is_alternant: true },
      });
      render(<StudentImportErrorsPanel {...defaultProps} errors={[error]} onRetry={onRetry} />);
      await user.click(screen.getByText("INE123"));

      await user.selectOptions(screen.getByLabelText("Boursier"), "false");
      const ineField = screen.getByLabelText("N°INE");
      await user.type(ineField, "12345678901");
      await user.click(screen.getByRole("button", { name: /relancer/i }));

      const correction = onRetry.mock.calls[0][1];
      expect(correction.is_scholarship).toBe(false);
      // FISE/FISA untouched — still reflects the original payload, not lost.
      expect(correction.is_alternant).toBe(true);
    });
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
