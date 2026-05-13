const publicApiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000/api/v1";

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
};

function formatApiErrorDetail(errorDetail: unknown): string {
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

export async function browserApi<T>(
  path: string,
  { method, body }: RequestOptions,
): Promise<T> {
  const response = await fetch(`${publicApiBaseUrl}${path}`, {
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

  if (!response.ok) {
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

    throw new Error(message || `Erreur API ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}