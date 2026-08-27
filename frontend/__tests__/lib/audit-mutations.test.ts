import { describe, expect, it, vi } from "vitest";

import { browserApi } from "@/lib/api/browser-client";
import { getAuditLogs } from "@/lib/api/audit-mutations";

vi.mock("@/lib/api/browser-client", () => ({
  browserApi: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
}));

const mockedBrowserApi = vi.mocked(browserApi);

describe("audit-mutations", () => {
  it("builds the query string from all provided filters", () => {
    getAuditLogs({
      entity_type: "agreement",
      action: "create",
      date_from: "2026-01-01",
      date_to: "2026-01-31",
      actor_username: "alice",
      page: 2,
      page_size: 10,
    });
    expect(mockedBrowserApi).toHaveBeenCalledWith(
      "/audit/logs/?entity_type=agreement&action=create&date_from=2026-01-01&date_to=2026-01-31&actor_username=alice&page=2&page_size=10",
      { method: "GET" },
    );
  });

  it("omits the query string entirely when no filters are given", () => {
    getAuditLogs();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/audit/logs/", { method: "GET" });
  });
});
