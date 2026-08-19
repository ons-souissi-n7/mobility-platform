import { cookies } from "next/headers";

import { apiBaseUrl } from "@/lib/config";

/** Server-side authenticated fetch — reads the JWT from the request cookie. */
async function authHeader(): Promise<Record<string, string>> {
  const token = (await cookies()).get("auth_token")?.value;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getApi<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(await authHeader()),
    },
  });

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<T>;
}
