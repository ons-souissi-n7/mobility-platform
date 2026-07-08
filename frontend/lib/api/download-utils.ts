export { publicApiBaseUrl } from "@/lib/api/browser-client";

export async function downloadBlob(url: string, defaultFilename = "export.xlsx"): Promise<void> {
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Erreur export ${response.status}${text ? ` — ${text}` : ""}`);
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
  document.body.removeChild(a);
  URL.revokeObjectURL(href);
}
