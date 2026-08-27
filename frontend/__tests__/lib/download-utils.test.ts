import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { downloadBlob } from "@/lib/api/download-utils";

describe("downloadBlob", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn();
    document.cookie = "auth_token=; path=/; max-age=0";
    URL.createObjectURL = vi.fn().mockReturnValue("blob:mock");
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("triggers a download using the filename from Content-Disposition", async () => {
    const blob = new Blob(["data"]);
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      blob: async () => blob,
      headers: new Headers({ "Content-Disposition": 'attachment; filename="rapport.xlsx"' }),
    } as Response);

    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    await downloadBlob("http://localhost:8000/api/v1/export/");

    expect(clickSpy).toHaveBeenCalled();
    expect(URL.createObjectURL).toHaveBeenCalledWith(blob);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock");
  });

  it("falls back to the default filename when no Content-Disposition header is present", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      blob: async () => new Blob(["data"]),
      headers: new Headers(),
    } as Response);
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    let capturedDownload = "";
    const originalSetAttribute = HTMLAnchorElement.prototype.click;
    const appendSpy = vi.spyOn(document.body, "appendChild").mockImplementation((node) => {
      capturedDownload = (node as HTMLAnchorElement).download;
      return node;
    });

    await downloadBlob("http://localhost:8000/api/v1/export/", "fallback.xlsx");

    expect(capturedDownload).toBe("fallback.xlsx");
    appendSpy.mockRestore();
    void originalSetAttribute;
  });

  it("throws a descriptive error when the response is not ok", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 403,
      text: async () => "Forbidden",
    } as Response);

    await expect(downloadBlob("http://localhost:8000/api/v1/export/")).rejects.toThrow(
      "Erreur export 403",
    );
  });
});
