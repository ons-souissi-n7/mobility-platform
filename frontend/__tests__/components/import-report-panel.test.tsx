import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ImportReportPanel } from "@/components/ui/import-report-panel";

const successReport = { created: 3, updated: 1, unresolved: [], errors: [] };
const warningReport = {
  created: 2,
  updated: 0,
  unresolved: [{ ine: "ABC123", reason: "Département inconnu" }],
  errors: [],
};
const errorReport = {
  created: 0,
  updated: 0,
  unresolved: [],
  errors: ["INE XYZ: champ manquant"],
};

describe("ImportReportPanel", () => {
  it("shows green style on full success", () => {
    const { container } = render(
      <ImportReportPanel report={successReport} onClose={vi.fn()} />,
    );
    expect(container.firstChild).toHaveClass("border-emerald-200");
  });

  it("shows amber style when there are unresolved items", () => {
    const { container } = render(
      <ImportReportPanel report={warningReport} onClose={vi.fn()} />,
    );
    expect(container.firstChild).toHaveClass("border-amber-200");
  });

  it("displays created and updated counts", () => {
    render(<ImportReportPanel report={successReport} onClose={vi.fn()} />);
    expect(screen.getByText(/3 créé/)).toBeInTheDocument();
    expect(screen.getByText(/1 mis à jour/)).toBeInTheDocument();
  });

  it("lists unresolved items (up to 5)", () => {
    render(<ImportReportPanel report={warningReport} onClose={vi.fn()} />);
    expect(screen.getByText(/INE ABC123/)).toBeInTheDocument();
    expect(screen.getByText(/Département inconnu/)).toBeInTheDocument();
  });

  it("lists errors", () => {
    render(<ImportReportPanel report={errorReport} onClose={vi.fn()} />);
    expect(screen.getByText(/INE XYZ: champ manquant/)).toBeInTheDocument();
  });

  it("calls onClose when the close button is clicked", async () => {
    const onClose = vi.fn();
    render(<ImportReportPanel report={successReport} onClose={onClose} />);
    await userEvent.click(screen.getByRole("button", { name: /fermer/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("uses a custom title when provided", () => {
    render(
      <ImportReportPanel
        report={successReport}
        title="Sync MoveON terminée"
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByText("Sync MoveON terminée")).toBeInTheDocument();
  });

  it("does not show skipped count", () => {
    const report = { ...successReport, skipped: 5 };
    render(<ImportReportPanel report={report} onClose={vi.fn()} />);
    expect(screen.queryByText(/ignoré/)).not.toBeInTheDocument();
  });
});
