export { publicApiBaseUrl } from "@/lib/api/browser-client";

function getAuthToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = /(?:^|; )auth_token=([^;]*)/.exec(document.cookie);
  return match ? decodeURIComponent(match[1]) : null;
}

export async function downloadBlob(
  url: string,
  defaultFilename = "export.xlsx"
): Promise<void> {
  const token = getAuthToken();
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(
      `Erreur export ${response.status}` + (text ? ` — ${text}` : "")
    );
  }
  const blob = await response.blob();
  const cd = response.headers.get("Content-Disposition") ?? "";
  const match = /filename[^;=\n]*=["']?([^"'\n;]+)["']?/.exec(cd);
  const filename = match?.[1]?.trim() ?? defaultFilename;
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(href);
}
