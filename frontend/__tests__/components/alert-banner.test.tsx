/**
 * Tests du bandeau d'alertes système — BNF07 (supervision et alertes).
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import type { SystemAlert } from "@/lib/api/types";

vi.mock("@/lib/api/alerts", () => ({
  fetchUnreadAlerts: vi.fn(),
  acknowledgeAlert: vi.fn().mockResolvedValue(undefined),
}));

// Import après le mock
async function renderAlertBanner(alerts: SystemAlert[]) {
  const { fetchUnreadAlerts } = await import("@/lib/api/alerts");
  vi.mocked(fetchUnreadAlerts).mockResolvedValue(alerts);
  const { AlertBanner } = await import("@/components/layout/alert-banner");
  return render(<AlertBanner />);
}

function makeAlert(overrides: Partial<SystemAlert> = {}): SystemAlert {
  return {
    id: 1,
    level: "warning",
    title: "Titre alerte",
    message: "Message de l'alerte système",
    created_at: "2026-01-01T10:00:00Z",
    acknowledged_at: null,
    ...overrides,
  };
}

describe("AlertBanner", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("n'affiche rien si aucune alerte non lue", async () => {
    const { container } = await renderAlertBanner([]);
    await waitFor(() => {
      expect(container.querySelector("[data-alert]")).toBeNull();
    });
  });

  it("affiche le titre et le message de l'alerte", async () => {
    await renderAlertBanner([makeAlert({ title: "Affectation échouée", message: "Erreur Gale-Shapley" })]);
    await waitFor(() => {
      expect(screen.getByText("Affectation échouée")).toBeInTheDocument();
    });
  });

  it("affiche les alertes de niveau error avec un bandeau rouge", async () => {
    // "error" est la seule valeur de SystemAlert.level qui déclenche le style
    // rouge (alert-banner.tsx: hasError = alerts.some(a => a.level === "error")) —
    // "critical" n'existe pas dans ce type et ne peut jamais survenir en production.
    await renderAlertBanner([makeAlert({ level: "error", title: "Erreur critique" })]);
    await waitFor(() => {
      expect(screen.getByText("Erreur critique")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /alerte système/i })).toHaveClass("bg-red-600");
  });

  it("appelle acknowledgeAlert au clic sur 'J'ai pris note'", async () => {
    const { acknowledgeAlert } = await import("@/lib/api/alerts");
    await renderAlertBanner([makeAlert({ id: 42 })]);
    await screen.findByText("Titre alerte");

    const ackBtn = screen.getByRole("button", { name: /j'ai pris note/i });
    await userEvent.click(ackBtn);

    expect(acknowledgeAlert).toHaveBeenCalledWith(42);
  });

  it("affiche plusieurs alertes", async () => {
    await renderAlertBanner([
      makeAlert({ id: 1, title: "Alerte 1" }),
      makeAlert({ id: 2, title: "Alerte 2" }),
    ]);
    await waitFor(() => {
      expect(screen.getByText("Alerte 1")).toBeInTheDocument();
      expect(screen.getByText("Alerte 2")).toBeInTheDocument();
    });
  });
});
