/**
 * Tests unitaires du client API navigateur — BNF02 (Auth JWT côté frontend).
 *
 * Vérifie :
 * - Lecture du token depuis document.cookie
 * - Ajout automatique du header Authorization
 * - Gestion des erreurs API (4xx, 5xx)
 * - Refresh proactif du token avant expiration
 */

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { browserApi } from "@/lib/api/browser-client";

// ── Helpers JWT ────────────────────────────────────────────────────────────

function makeJwtPayload(expOffsetSecs: number, role = "admin"): string {
  const b64 = (obj: object) =>
    btoa(JSON.stringify(obj))
      .replace(/=/g, "")
      .replace(/\+/g, "-")
      .replace(/\//g, "_");

  const now = Math.floor(Date.now() / 1000);
  const payload = { role, ine: "", sub: "test@n7.fr", email: "test@n7.fr", iat: now, exp: now + expOffsetSecs };
  const header = b64({ alg: "HS256", typ: "JWT" });
  const body = b64(payload);
  const sig = b64({ sig: "mock" });
  return `${header}.${body}.${sig}`;
}

function setAuthCookie(token: string): void {
  Object.defineProperty(document, "cookie", {
    writable: true,
    value: `auth_token=${encodeURIComponent(token)}`,
  });
}

function clearAuthCookie(): void {
  Object.defineProperty(document, "cookie", {
    writable: true,
    value: "",
  });
}

// ── Setup ─────────────────────────────────────────────────────────────────

beforeEach(() => {
  clearAuthCookie();
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

// ── Tests ─────────────────────────────────────────────────────────────────

describe("browserApi — en-tête Authorization", () => {
  it("envoie le token JWT dans l'en-tête Authorization", async () => {
    const token = makeJwtPayload(3600);
    setAuthCookie(token);

    const mockFetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ count: 0, results: [] }), { status: 200 })
    );
    vi.stubGlobal("fetch", mockFetch);

    await browserApi("/reference/countries/", { method: "GET" });

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect((options.headers as Record<string, string>)["Authorization"]).toBe(`Bearer ${token}`);
  });

  it("n'envoie pas de header Authorization si pas de token", async () => {
    clearAuthCookie();

    const mockFetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({}), { status: 200 })
    );
    vi.stubGlobal("fetch", mockFetch);

    await browserApi("/reference/countries/", { method: "GET" });

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;
    expect(headers["Authorization"]).toBeUndefined();
  });
});

describe("browserApi — gestion des erreurs HTTP", () => {
  it("lève une erreur si la réponse est 401", async () => {
    setAuthCookie(makeJwtPayload(3600));
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Non autorisé" }), { status: 401 })
      )
    );

    await expect(browserApi("/students/students/", { method: "GET" })).rejects.toThrow();
  });

  it("lève une erreur si la réponse est 403", async () => {
    setAuthCookie(makeJwtPayload(3600));
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Accès refusé" }), { status: 403 })
      )
    );

    await expect(browserApi("/students/students/", { method: "GET" })).rejects.toThrow(
      /403|accès refusé/i
    );
  });

  it("lève une erreur si la réponse est 500", async () => {
    setAuthCookie(makeJwtPayload(3600));
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        new Response("Internal Server Error", { status: 500 })
      )
    );

    await expect(browserApi("/some/endpoint/", { method: "GET" })).rejects.toThrow();
  });

  it("lève une erreur réseau si fetch échoue", async () => {
    setAuthCookie(makeJwtPayload(3600));
    vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce(new TypeError("Network error")));

    await expect(browserApi("/some/endpoint/", { method: "GET" })).rejects.toThrow();
  });

  it("retourne undefined pour une réponse 204 No Content", async () => {
    setAuthCookie(makeJwtPayload(3600));
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(new Response(null, { status: 204 }))
    );

    const result = await browserApi<void>("/some/endpoint/", { method: "DELETE" });
    expect(result).toBeUndefined();
  });
});

describe("browserApi — sérialisation JSON", () => {
  it("envoie le body en JSON avec le bon Content-Type", async () => {
    setAuthCookie(makeJwtPayload(3600));
    const mockFetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ id: 1 }), { status: 201 })
    );
    vi.stubGlobal("fetch", mockFetch);

    await browserApi("/reference/countries/", {
      method: "POST",
      body: { code: "DE", name: "Allemagne" },
    });

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
    expect(options.body).toBe(JSON.stringify({ code: "DE", name: "Allemagne" }));
  });
});

describe("browserApi — refresh proactif du token (BNF02)", () => {
  it("tente un refresh si le token expire dans moins de 3 minutes", async () => {
    const soonExpiring = makeJwtPayload(120); // expire dans 2 min
    setAuthCookie(soonExpiring);

    const newToken = makeJwtPayload(900);
    const mockFetch = vi
      .fn()
      // Premier appel : refresh
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ token: newToken }), { status: 200 })
      )
      // Deuxième appel : la vraie requête
      .mockResolvedValueOnce(
        new Response(JSON.stringify([]), { status: 200 })
      );

    vi.stubGlobal("fetch", mockFetch);

    await browserApi("/reference/countries/", { method: "GET" });

    // Le refresh endpoint doit avoir été appelé
    const firstCallUrl = mockFetch.mock.calls[0][0] as string;
    expect(firstCallUrl).toContain("/auth/refresh/");
  });

  it("ne tente pas de refresh si le token est valide pour plus de 3 minutes", async () => {
    const validToken = makeJwtPayload(3600); // expire dans 1h
    setAuthCookie(validToken);

    const mockFetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify([]), { status: 200 })
    );
    vi.stubGlobal("fetch", mockFetch);

    await browserApi("/reference/countries/", { method: "GET" });

    // Un seul appel — pas de refresh
    expect(mockFetch).toHaveBeenCalledTimes(1);
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).not.toContain("/auth/refresh/");
  });
});
