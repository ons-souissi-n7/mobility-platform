import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "@/app/login/page";

const mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockSearchParams.forEach((_, key) => mockSearchParams.delete(key));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the redirect message with no error param", () => {
    render(<LoginPage />);
    expect(screen.getByText("Redirection vers le portail CAS…")).toBeInTheDocument();
    expect(screen.getByText("N7 Mobilité")).toBeInTheDocument();
  });

  it("shows the mapped error message for a known error code", () => {
    mockSearchParams.set("error", "cas_unavailable");
    render(<LoginPage />);
    expect(screen.getByText("Le service CAS est indisponible. Réessayez.")).toBeInTheDocument();
  });

  it("falls back to a generic message for an unknown error code", () => {
    mockSearchParams.set("error", "something_else");
    render(<LoginPage />);
    expect(screen.getByText("Erreur d'authentification.")).toBeInTheDocument();
  });
});
