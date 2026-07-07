export const publicApiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000/api/v1";

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

  try {
    response = await fetch(`${publicApiBaseUrl}${path}`, {
      cache: "no-store",
      method: method ?? "GET",
      headers: body
        ? {
            Accept: "application/json",
            "Content-Type": "application/json",
          }
        : {
            Accept: "application/json",
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

  try {
    response = await fetch(`${publicApiBaseUrl}${path}`, {
      method: "POST",
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
