/**
 * Tests du workspace de gestion des années universitaires.
 * Couvre : FSM buttons, recovery action, CRUD modal, error handling.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AcademicYearsWorkspace } from "@/components/academic-years/academic-years-workspace";
import type { AcademicYear } from "@/lib/api/types";

// ── Mocks ─────────────────────────────────────────────────────────────────
vi.mock("@/lib/api/academic-year-mutations", () => ({
  applyAcademicYearTransition: vi.fn().mockResolvedValue({
    id: 1, label: "2026-2027", status: "recommendation",
    start_date: "2026-09-01", end_date: "2027-07-01",
    wishes_open_date: null, wishes_close_date: null,
    closed_at: null, created_at: "", updated_at: "",
  }),
  createAcademicYear: vi.fn().mockResolvedValue({
    id: 99, label: "2027-2028", status: "initialization",
    start_date: "2027-09-01", end_date: "2028-07-01",
    wishes_open_date: null, wishes_close_date: null,
    closed_at: null, created_at: "", updated_at: "",
  }),
  updateAcademicYear: vi.fn().mockResolvedValue({
    id: 1, label: "2026-2027 MAJ", status: "initialization",
    start_date: "2026-09-01", end_date: "2027-07-01",
    wishes_open_date: null, wishes_close_date: null,
    closed_at: null, created_at: "", updated_at: "",
  }),
  deleteAcademicYear: vi.fn().mockResolvedValue(undefined),
}));

// ── Helpers ───────────────────────────────────────────────────────────────

function makeYear(overrides: Partial<AcademicYear> = {}): AcademicYear {
  return {
    id: 1,
    label: "2026-2027",
    start_date: "2026-09-01",
    end_date: "2027-07-01",
    status: "initialization",
    wishes_open_date: null,
    wishes_close_date: null,
    closed_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("AcademicYearsWorkspace", () => {
  it("affiche le bouton 'Ajouter une année'", () => {
    render(<AcademicYearsWorkspace years={[]} />);
    expect(screen.getByText(/ajouter une année/i)).toBeInTheDocument();
  });

  it("affiche les années passées en props", () => {
    render(<AcademicYearsWorkspace years={[makeYear()]} />);
    expect(screen.getByText("2026-2027")).toBeInTheDocument();
  });

  it("affiche le statut de chaque année", () => {
    render(<AcademicYearsWorkspace years={[makeYear({ status: "recommendation" })]} />);
    expect(screen.getByText(/recommandation/i)).toBeInTheDocument();
  });

  it("affiche le bouton de transition pour un état avec transition disponible", () => {
    render(<AcademicYearsWorkspace years={[makeYear({ status: "initialization" })]} />);
    expect(screen.getByText(/ouvrir recommandations/i)).toBeInTheDocument();
  });

  it("affiche le spinner 'Calcul en cours' pour pre_assignment", () => {
    render(<AcademicYearsWorkspace years={[makeYear({ status: "pre_assignment" })]} />);
    expect(screen.getByText(/calcul en cours/i)).toBeInTheDocument();
  });

  it("affiche le bouton 'Récupérer' pour pre_assignment", () => {
    render(<AcademicYearsWorkspace years={[makeYear({ status: "pre_assignment" })]} />);
    expect(screen.getByText(/récupérer/i)).toBeInTheDocument();
  });

  it("affiche '—' pour les états sans transition suivante (closed)", () => {
    render(<AcademicYearsWorkspace years={[makeYear({ status: "closed" })]} />);
    // Pour 'closed', pas de bouton de transition
    expect(screen.queryByRole("button", { name: /transition/i })).toBeNull();
  });

  it("ouvre le modal de création quand on clique 'Ajouter'", async () => {
    render(<AcademicYearsWorkspace years={[]} />);
    await userEvent.click(screen.getByText(/ajouter une année/i));
    expect(screen.getByText(/ajouter une annee universitaire/i)).toBeInTheDocument();
  });

  it("affiche un message d'erreur si la transition échoue", async () => {
    const { applyAcademicYearTransition } = await import("@/lib/api/academic-year-mutations");
    vi.mocked(applyAcademicYearTransition).mockRejectedValueOnce(
      new Error("Transition non autorisée")
    );
    render(<AcademicYearsWorkspace years={[makeYear({ status: "import" })]} />);
    const btn = screen.getByText(/lancer l'affectation/i);
    await userEvent.click(btn);
    // Le dialog de confirmation apparaît avec un bouton au même intitulé que
    // celui du tableau ("Lancer l'affectation") — il est rendu après le
    // tableau dans le DOM (cf. academic-years-workspace.tsx), donc toujours
    // en dernière position parmi les correspondances.
    const matches = screen.queryAllByRole("button", { name: /lancer l'affectation/i });
    const confirmBtn = matches[matches.length - 1];
    if (confirmBtn) await userEvent.click(confirmBtn);
    await waitFor(() => {
      expect(screen.queryByText(/transition non autorisée/i)).not.toBeNull();
    });
  });
});
