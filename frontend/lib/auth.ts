const TOKEN_COOKIE = "auth_token";
const TOKEN_MAX_AGE = 15 * 60; // 15 minutes (rapport §3.4.7.3)

// ── Cookie management ─────────────────────────────────────────────────────────

export function setToken(token: string): void {
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(token)}; path=/; max-age=${TOKEN_MAX_AGE}; SameSite=Lax`;
}

export function getToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = new RegExp(`(?:^|; )${TOKEN_COOKIE}=([^;]*)`).exec(
    document.cookie
  );
  return match ? decodeURIComponent(match[1]) : null;
}

export function removeToken(): void {
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
}

// ── JWT payload decoder (no verification — routing use only) ──────────────────

export interface TokenPayload {
  sub: string;
  email: string;
  role: "admin" | "student";
  ine: string;
  exp: number;
  iat: number;
}

export function parseToken(token: string): TokenPayload | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const decoded = atob(payload.replaceAll("-", "+").replaceAll("_", "/"));
    return JSON.parse(decoded) as TokenPayload;
  } catch {
    return null;
  }
}

export function getTokenPayload(): TokenPayload | null {
  const token = getToken();
  return token ? parseToken(token) : null;
}

/** INE of the currently authenticated student, read from the session — never from the URL. */
export function getCurrentIne(): string {
  return getTokenPayload()?.ine ?? "";
}

export function isTokenExpired(payload: TokenPayload): boolean {
  return payload.exp < Date.now() / 1000;
}

// ── Auth actions ──────────────────────────────────────────────────────────────

export async function logout(): Promise<void> {
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  const token = getToken();
  try {
    const resp = await fetch(`${apiUrl}/auth/logout/`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    removeToken();
    if (resp.ok) {
      const data = (await resp.json()) as { cas_logout_url?: string };
      if (data.cas_logout_url) {
        window.location.href = data.cas_logout_url;
        return;
      }
    }
  } catch {
    removeToken();
  }
  window.location.href = "/login";
}

export async function refreshToken(): Promise<string | null> {
  const token = getToken();
  if (!token) return null;
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  try {
    const resp = await fetch(`${apiUrl}/auth/refresh/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resp.ok) {
      removeToken();
      return null;
    }
    const data = (await resp.json()) as { token?: string };
    if (data.token) {
      setToken(data.token);
      return data.token;
    }
  } catch {
    // network error — keep existing token
  }
  return null;
}

/** Redirect to the default page for the given role. */
export function getDefaultPath(payload: TokenPayload): string {
  if (payload.role === "student" && payload.ine) {
    return "/student/tableau-de-bord";
  }
  return "/admin";
}
