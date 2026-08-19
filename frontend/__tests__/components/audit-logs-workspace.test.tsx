/**
 * Tests du journal d'audit — BF08 : Traçabilité des actions.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuditLogsWorkspace } from "@/components/audit/audit-logs-workspace";
import type { AuditLog, PagedResponse } from "@/lib/api/types";

vi.mock("@/lib/api/audit-mutations", () => ({
  getAuditLogs: vi.fn().mockResolvedValue({
    count: 0,
    results: [],
    page: 1,
    page_size: 25,
  }),
}));

function makeLog(overrides: Partial<AuditLog> = {}): AuditLog {
  return {
    id: 1,
    timestamp: "2026-01-15T10:30:00Z",
    actor_username: "admin@n7.fr",
    action: "create",
    entity_type: "country",
    entity_id: 42,
    entity_repr: "France (FR)",
    changes: null,
    ...overrides,
  };
}

function makePagedResponse(logs: AuditLog[]): PagedResponse<AuditLog> {
  return { count: logs.length, results: logs, page: 1, page_size: 25 };
}

describe("AuditLogsWorkspace", () => {
  it("affiche un message vide quand aucune entrée", () => {
    render(<AuditLogsWorkspace initialData={makePagedResponse([])} />);
    // Le libellé de pagination affiche aussi "Aucune entrée dans le journal" —
    // on cible le message spécifique au tableau, qui précise "pour ces critères".
    expect(screen.getByText(/aucune entrée dans le journal pour ces critères/i)).toBeInTheDocument();
  });

  it("affiche les logs passés en initialData", () => {
    const logs = [
      makeLog({ action: "create", entity_type: "country", entity_repr: "France (FR)" }),
    ];
    render(<AuditLogsWorkspace initialData={makePagedResponse(logs)} />);
    expect(screen.getByText("France (FR)")).toBeInTheDocument();
  });

  it("affiche le badge d'action 'Création' pour action=create", () => {
    const logs = [makeLog({ action: "create" })];
    render(<AuditLogsWorkspace initialData={makePagedResponse(logs)} />);
    // "Création" apparaît aussi comme option du filtre — on cible le badge,
    // rendu dans le corps du tableau des résultats.
    const table = screen.getByRole("table");
    expect(within(table).getByText(/création/i)).toBeInTheDocument();
  });

  it("affiche le badge 'Suppression' pour action=delete", () => {
    const logs = [makeLog({ action: "delete" })];
    render(<AuditLogsWorkspace initialData={makePagedResponse(logs)} />);
    const table = screen.getByRole("table");
    expect(within(table).getByText(/suppression/i)).toBeInTheDocument();
  });

  it("affiche l'utilisateur acteur", () => {
    const logs = [makeLog({ actor_username: "responsable@n7.fr" })];
    render(<AuditLogsWorkspace initialData={makePagedResponse(logs)} />);
    expect(screen.getByText("responsable@n7.fr")).toBeInTheDocument();
  });

  it("affiche 'système' si actor_username est null", () => {
    const logs = [makeLog({ actor_username: null as unknown as string })];
    render(<AuditLogsWorkspace initialData={makePagedResponse(logs)} />);
    expect(screen.getByText(/système/i)).toBeInTheDocument();
  });

  it("affiche les filtres d'action", () => {
    render(<AuditLogsWorkspace initialData={makePagedResponse([])} />);
    expect(screen.getByText(/toutes les actions/i)).toBeInTheDocument();
  });

  it("affiche le bouton Diff si le log a des changements", () => {
    const logs = [makeLog({
      action: "update",
      changes: { name: ["Ancien", "Nouveau"] } as unknown as Record<string, [unknown, unknown]>,
    })];
    render(<AuditLogsWorkspace initialData={makePagedResponse(logs)} />);
    expect(screen.getByText(/diff/i)).toBeInTheDocument();
  });

  it("affiche le diff au clic sur le bouton Diff", async () => {
    const logs = [makeLog({
      action: "update",
      changes: { name: ["Ancien", "Nouveau"] } as unknown as Record<string, [unknown, unknown]>,
    })];
    render(<AuditLogsWorkspace initialData={makePagedResponse(logs)} />);
    await userEvent.click(screen.getByText(/diff/i));
    expect(screen.getByText("Ancien")).toBeInTheDocument();
    expect(screen.getByText("Nouveau")).toBeInTheDocument();
  });

  it("affiche le compteur total d'entrées", () => {
    const data = makePagedResponse([makeLog(), makeLog({ id: 2 })]);
    data.count = 2;
    render(<AuditLogsWorkspace initialData={data} />);
    expect(screen.getByText(/2 entrée/i)).toBeInTheDocument();
  });

  it("appelle getAuditLogs avec les filtres lors du changement d'action", async () => {
    const { getAuditLogs } = await import("@/lib/api/audit-mutations");
    vi.mocked(getAuditLogs).mockResolvedValue(makePagedResponse([]));

    render(<AuditLogsWorkspace initialData={makePagedResponse([])} />);

    const select = screen.getByRole("combobox", { name: /filtrer par action/i });
    await userEvent.selectOptions(select, "create");

    await waitFor(() => {
      expect(getAuditLogs).toHaveBeenCalledWith(
        expect.objectContaining({ action: "create" })
      );
    });
  });
});
