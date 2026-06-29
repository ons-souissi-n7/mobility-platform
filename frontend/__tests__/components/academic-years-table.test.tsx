import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AcademicYearsTable } from "@/components/academic-years/academic-years-table";
import type { AcademicYear } from "@/lib/api/types";

function makeYear(overrides: Partial<AcademicYear> = {}): AcademicYear {
  return {
    id: 1,
    label: "2026-2027",
    start_date: "2026-09-01",
    end_date: "2027-08-31",
    status: "initialization",
    wishes_open_date: null,
    wishes_close_date: null,
    closed_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("AcademicYearsTable", () => {
  it("renders year label in the table", () => {
    render(
      <AcademicYearsTable
        years={[makeYear({ label: "2026-2027" })]}
        onDelete={vi.fn()}
        onEdit={vi.fn()}
        onTransition={vi.fn()}
      />,
    );
    expect(screen.getByText("2026-2027")).toBeInTheDocument();
  });

  it("shows empty message when no years", () => {
    render(
      <AcademicYearsTable
        years={[]}
        onDelete={vi.fn()}
        onEdit={vi.fn()}
        onTransition={vi.fn()}
      />,
    );
    expect(
      screen.getByText(/aucune annee universitaire/i),
    ).toBeInTheDocument();
  });

  it("displays Initialisation status badge for initialization state", () => {
    render(
      <AcademicYearsTable
        years={[makeYear({ status: "initialization" })]}
        onDelete={vi.fn()}
        onEdit={vi.fn()}
        onTransition={vi.fn()}
      />,
    );
    expect(screen.getByText("Initialisation")).toBeInTheDocument();
  });

  it("displays Cloturee status badge for closed state", () => {
    render(
      <AcademicYearsTable
        years={[makeYear({ status: "closed" })]}
        onDelete={vi.fn()}
        onEdit={vi.fn()}
        onTransition={vi.fn()}
      />,
    );
    expect(screen.getByText("Cloturee")).toBeInTheDocument();
  });

  it("calls onEdit when edit button is clicked", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    const year = makeYear();
    render(
      <AcademicYearsTable
        years={[year]}
        onDelete={vi.fn()}
        onEdit={onEdit}
        onTransition={vi.fn()}
      />,
    );
    await user.click(screen.getByRole("button", { name: /modifier|edit/i }));
    expect(onEdit).toHaveBeenCalledWith(year);
  });

  it("renders multiple years", () => {
    const years = [
      makeYear({ id: 1, label: "2025-2026" }),
      makeYear({ id: 2, label: "2026-2027" }),
    ];
    render(
      <AcademicYearsTable
        years={years}
        onDelete={vi.fn()}
        onEdit={vi.fn()}
        onTransition={vi.fn()}
      />,
    );
    expect(screen.getByText("2025-2026")).toBeInTheDocument();
    expect(screen.getByText("2026-2027")).toBeInTheDocument();
  });
});
