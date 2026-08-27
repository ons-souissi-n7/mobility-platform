import { describe, expect, it, vi } from "vitest";

import { getApi } from "@/lib/api/client";
import { getAuditLogs } from "@/lib/api/audit";

vi.mock("@/lib/api/client", () => ({
  getApi: vi.fn().mockResolvedValue({ count: 0, results: [], page: 1, page_size: 25 }),
}));

const mockedGetApi = vi.mocked(getApi);

describe("audit", () => {
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
    expect(mockedGetApi).toHaveBeenCalledWith(
      "/audit/logs/?entity_type=agreement&action=create&date_from=2026-01-01&date_to=2026-01-31&actor_username=alice&page=2&page_size=10",
    );
  });

  it("omits the query string entirely when no filters are given", () => {
    getAuditLogs();
    expect(mockedGetApi).toHaveBeenCalledWith("/audit/logs/");
  });
});
