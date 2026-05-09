const publicApiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000/api/v1";

type RequestOptions = {
  method: "POST" | "PUT" | "DELETE";
  body?: unknown;
};

export async function browserApi<T>(
  path: string,
  { method, body }: RequestOptions,
): Promise<T> {
  const response = await fetch(`${publicApiBaseUrl}${path}`, {
    method,
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
    const message = await response.text();
    throw new Error(message || `Erreur API ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
