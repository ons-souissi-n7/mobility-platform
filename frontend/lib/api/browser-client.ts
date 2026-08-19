export const publicApiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000/api/v1";

/** Read the JWT from the browser cookie (client-side only). */
function getAuthToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = /(?:^|; )auth_token=([^;]*)/.exec(document.cookie);
  return match ? decodeURIComponent(match[1]) : null;
}

function setAuthToken(token: string): void {
  const maxAge = 15 * 60;
  document.cookie = `auth_token=${encodeURIComponent(token)}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

// Refresh the JWT silently if it expires within 3 minutes. Prevents mid-session
// logouts when the user is actively working and the 15-min window expires.
const REFRESH_THRESHOLD_SECS = 180;
let _refreshing: Promise<string | null> | null = null;

async function getTokenWithProactiveRefresh(): Promise<string | null> {
  const token = getAuthToken();
  if (!token) return null;

  try {
    const parts = token.split(".");
    if (parts.length !== 3) return token;
    const payload = JSON.parse(
      atob(parts[1].replaceAll("-", "+").replaceAll("_", "/")),
    ) as { exp?: number };
    const exp = payload.exp ?? 0;
    const now = Math.floor(Date.now() / 1000);

    if (exp - now > REFRESH_THRESHOLD_SECS) return token;

    // Deduplicate concurrent refresh calls
    _refreshing ??= fetch(`${publicApiBaseUrl}/auth/refresh/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (!res.ok) return null;
        const data = (await res.json()) as { token?: string };
        if (data.token) {
          setAuthToken(data.token);
          return data.token;
        }
        return null;
      })
      .catch(() => null)
      .finally(() => {
        _refreshing = null;
      });

    const refreshed = await _refreshing;
    return refreshed ?? token;
  } catch {
    return token;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
};

export function formatApiErrorDetail(errorDetail: unknown): string {
  if (errorDetail == null) {
    return "Erreur inconnue";
  }

  if (typeof errorDetail === "string") {
    return errorDetail;
  }

  if (Array.isArray(errorDetail)) {
    return errorDetail.map(formatApiErrorDetail).join(" / ");
  }

  if (typeof errorDetail === "object") {
    return Object.entries(errorDetail)
      .map(([key, value]) => `${key}: ${formatApiErrorDetail(value)}`)
      .join(" / ");
  }

  return String(errorDetail);
}

async function extractErrorMessage(response: Response): Promise<string> {
  const text = await response.text();
  let message = `Erreur API ${response.status}`;

  if (text) {
    try {
      const payload = JSON.parse(text);

      if (payload && typeof payload === "object") {
        if ("detail" in payload) {
          message = formatApiErrorDetail((payload as { detail: unknown }).detail);
        } else if ("message" in payload) {
          message = formatApiErrorDetail((payload as { message: unknown }).message);
        } else {
          message = formatApiErrorDetail(payload);
        }
      } else {
        message = String(payload);
      }
    } catch {
      message = text;
    }
  }

  return message || `Erreur API ${response.status}`;
}

export async function browserApi<T>(
  path: string,
  { method, body }: RequestOptions,
): Promise<T> {
  let response: Response;
  const token = await getTokenWithProactiveRefresh();

  try {
    response = await fetch(`${publicApiBaseUrl}${path}`, {
      cache: "no-store",
      method: method ?? "GET",
      headers: {
        Accept: "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error(
      `Impossible de joindre l'API (${publicApiBaseUrl}). Vérifiez que le backend est démarré et que l'origine du frontend est autorisée.`,
    );
  }

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Variante de `browserApi` pour les uploads `multipart/form-data` (Excel, justificatifs…),
 * qui ne peuvent pas passer par `browserApi` car celui-ci sérialise toujours `body` en JSON.
 */
export async function browserApiUpload<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  let response: Response;
  const token = await getTokenWithProactiveRefresh();

  try {
    response = await fetch(`${publicApiBaseUrl}${path}`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
  } catch {
    throw new Error(
      `Impossible de joindre l'API (${publicApiBaseUrl}). Vérifiez que le backend est démarré et que l'origine du frontend est autorisée.`,
    );
  }

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
