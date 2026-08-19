/**
 * Tests de sécurité du proxy Next.js — BNF02 (Auth & RBAC côté frontend).
 *
 * Exerce directement le middleware réel (`@/proxy`) plutôt qu'une copie de sa
 * logique — une régression dans le vrai fichier est ainsi détectée ici.
 *
 * Vérifie que le middleware proxy :
 * - Redirige les utilisateurs non authentifiés vers /login
 * - Redirige un token expiré vers /login (en supprimant le cookie)
 * - Laisse passer les chemins publics (/login, /auth/callback)
 * - Redirige les étudiants vers leur tableau de bord (et non /admin)
 * - Bloque les étudiants qui tentent d'accéder à /admin, ET bloque les admins
 *   qui tentent d'accéder à /student (étanchéité dans les deux sens)
 * - Traite un rôle absent ou inattendu comme une session invalide plutôt que
 *   de laisser passer par défaut
 * - Redirige la racine / selon le rôle
 * - Ne fait jamais figurer l'INE dans une URL de redirection : l'identité de
 *   l'étudiant vient uniquement du JWT en session (cookie), jamais du lien
 */

import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { proxy } from "@/proxy";

function makeJwt(payload: object, expOffsetSecs = 3600): string {
  const b64 = (obj: object) =>
    btoa(JSON.stringify(obj)).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
  const header = b64({ alg: "HS256", typ: "JWT" });
  const body = b64({
    ...payload,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + expOffsetSecs,
  });
  // Signature fictive (non vérifiée côté proxy — proxy vérifie seulement l'expiry)
  const sig = b64({ sig: "mock" });
  return `${header}.${body}.${sig}`;
}

function expiredJwt(role: string, ine = ""): string {
  return makeJwt({ role, ine, sub: "test@n7.fr", email: "test@n7.fr" }, -60);
}

function validAdminJwt(): string {
  return makeJwt({ role: "admin", ine: "", sub: "admin@n7.fr", email: "admin@n7.fr" });
}

function validStudentJwt(ine = "1234567890A"): string {
  return makeJwt({ role: "student", ine, sub: `${ine}@etud.n7.fr`, email: `${ine}@etud.n7.fr` });
}

// ── Appel du middleware réel ────────────────────────────────────────────────

type ProxyOutcome =
  | { action: "next" }
  | { action: "redirect"; to: string; deleteCookie: boolean };

function runProxy(pathname: string, cookieToken?: string): ProxyOutcome {
  const headers: Record<string, string> = {};
  if (cookieToken) headers["cookie"] = `auth_token=${cookieToken}`;
  const request = new NextRequest(`http://localhost:3000${pathname}`, { headers });
  const response = proxy(request);

  const location = response.headers.get("location");
  if (!location) return { action: "next" };

  const url = new URL(location);
  const deleteCookie = response.cookies.get("auth_token")?.value === "";
  return { action: "redirect", to: url.pathname + url.search, deleteCookie };
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("proxy — chemins publics", () => {
  it("laisse passer /login sans token", () => {
    const result = runProxy("/login");
    expect(result.action).toBe("next");
  });

  it("laisse passer /auth/callback sans token", () => {
    const result = runProxy("/auth/callback");
    expect(result.action).toBe("next");
  });

  it("laisse passer /login?error=cas_unavailable", () => {
    const result = runProxy("/login?error=cas_unavailable");
    expect(result.action).toBe("next");
  });
});

describe("proxy — utilisateur non authentifié", () => {
  it("redirige /admin vers /login avec next= si pas de token", () => {
    const result = runProxy("/admin/analytiques") as { action: string; to: string };
    expect(result.action).toBe("redirect");
    expect(result.to).toContain("/login");
    expect(result.to).toContain("next=");
  });

  it("redirige /admin/sortantes vers /login si pas de token", () => {
    const result = runProxy("/admin/sortantes") as { action: string; to: string };
    expect(result.action).toBe("redirect");
    expect(result.to).toContain("/login");
  });

  it("redirige / vers /login si pas de token", () => {
    const result = runProxy("/");
    expect(result.action).toBe("redirect");
  });
});

describe("proxy — token expiré", () => {
  it("redirige vers /login et supprime le cookie si token expiré (admin)", () => {
    const token = expiredJwt("admin");
    const result = runProxy("/admin/analytiques", token) as {
      action: string;
      to: string;
      deleteCookie: boolean;
    };
    expect(result.action).toBe("redirect");
    expect(result.to).toContain("/login");
    expect(result.deleteCookie).toBe(true);
  });

  it("redirige vers /login et supprime le cookie si token expiré (étudiant)", () => {
    const token = expiredJwt("student", "1234567890A");
    const result = runProxy("/student/tableau-de-bord", token) as {
      action: string;
      deleteCookie: boolean;
    };
    expect(result.action).toBe("redirect");
    expect(result.deleteCookie).toBe(true);
  });
});

describe("proxy — admin authentifié", () => {
  it("laisse passer /admin avec token admin valide", () => {
    const result = runProxy("/admin/analytiques", validAdminJwt());
    expect(result.action).toBe("next");
  });

  it("laisse passer /admin/sortantes avec token admin", () => {
    const result = runProxy("/admin/sortantes", validAdminJwt());
    expect(result.action).toBe("next");
  });

  it("redirige / vers /admin/analytiques pour un admin", () => {
    const result = runProxy("/", validAdminJwt()) as { action: string; to: string };
    expect(result.action).toBe("redirect");
    expect(result.to).toBe("/admin/analytiques");
  });

  it("redirige un admin qui accède à /student/tableau-de-bord vers /admin/analytiques", () => {
    const result = runProxy("/student/tableau-de-bord", validAdminJwt()) as {
      action: string;
      to: string;
    };
    expect(result.action).toBe("redirect");
    expect(result.to).toBe("/admin/analytiques");
  });

  it("redirige un admin qui accède à /student (bare) vers /admin/analytiques", () => {
    const result = runProxy("/student", validAdminJwt()) as { action: string; to: string };
    expect(result.action).toBe("redirect");
    expect(result.to).toBe("/admin/analytiques");
  });

  it("redirige un admin qui accède à l'espace d'un étudiant précis vers /admin/analytiques", () => {
    // Même avec une ancienne URL contenant un INE, un admin ne doit jamais
    // pouvoir consulter l'espace étudiant — l'isolation se fait sur le rôle,
    // pas sur la forme de l'URL.
    const result = runProxy("/student/20SN010FISE/voeux", validAdminJwt()) as {
      action: string;
      to: string;
    };
    expect(result.action).toBe("redirect");
    expect(result.to).toBe("/admin/analytiques");
  });
});

describe("proxy — étudiant authentifié", () => {
  const INE = "1234567890A";

  it("laisse passer /student/tableau-de-bord avec token étudiant", () => {
    const result = runProxy("/student/tableau-de-bord", validStudentJwt(INE));
    expect(result.action).toBe("next");
  });

  it("laisse passer /student (page interne gère la redirection vers tableau-de-bord)", () => {
    const result = runProxy("/student", validStudentJwt(INE));
    expect(result.action).toBe("next");
  });

  it("redirige un étudiant qui accède à /admin vers son tableau de bord", () => {
    const result = runProxy("/admin/analytiques", validStudentJwt(INE)) as {
      action: string;
      to: string;
    };
    expect(result.action).toBe("redirect");
    expect(result.to).toBe("/student/tableau-de-bord");
  });

  it("redirige un étudiant qui accède à /admin/sortantes", () => {
    const result = runProxy("/admin/sortantes", validStudentJwt(INE)) as {
      action: string;
      to: string;
    };
    expect(result.action).toBe("redirect");
    expect(result.to).toBe("/student/tableau-de-bord");
  });

  it("redirige / vers /student/tableau-de-bord pour un étudiant", () => {
    const result = runProxy("/", validStudentJwt(INE)) as { action: string; to: string };
    expect(result.action).toBe("redirect");
    expect(result.to).toBe("/student/tableau-de-bord");
  });
});

describe("proxy — JWT parsing (via le comportement observable du middleware)", () => {
  it("un token malformé est traité comme non authentifié", () => {
    // parseJwtPayload("notavalidtoken") renvoie null en interne ; le proxy
    // traite alors la requête comme s'il n'y avait pas de session du tout et
    // redirige vers /login (plutôt que de laisser passer sans rôle connu).
    const result = runProxy("/admin/analytiques", "notavalidtoken") as {
      action: string;
      to: string;
      deleteCookie: boolean;
    };
    expect(result.action).toBe("redirect");
    expect(result.to).toContain("/login");
    expect(result.deleteCookie).toBe(true);
  });

  it("un JWT admin valide donne accès aux routes /admin", () => {
    const result = runProxy("/admin/analytiques", validAdminJwt());
    expect(result.action).toBe("next");
  });

  it("un JWT étudiant valide redirige vers son espace sans exposer l'INE dans l'URL", () => {
    const result = runProxy("/admin/analytiques", validStudentJwt("9876543210Z")) as {
      action: string;
      to: string;
    };
    expect(result.action).toBe("redirect");
    expect(result.to).toBe("/student/tableau-de-bord");
    expect(result.to).not.toContain("9876543210Z");
  });

  it("un rôle absent ou inattendu est traité comme non authentifié (pas d'accès implicite)", () => {
    const token = makeJwt({ role: "superadmin", sub: "x@n7.fr", email: "x@n7.fr" });
    const result = runProxy("/admin/analytiques", token) as {
      action: string;
      to: string;
      deleteCookie: boolean;
    };
    expect(result.action).toBe("redirect");
    expect(result.to).toContain("/login");
    expect(result.deleteCookie).toBe(true);
  });
});
