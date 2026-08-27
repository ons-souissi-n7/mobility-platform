import { describe, expect, it, vi } from "vitest";

import { browserApi } from "@/lib/api/browser-client";
import { acknowledgeAlert, fetchUnreadAlerts } from "@/lib/api/alerts";

vi.mock("@/lib/api/browser-client", () => ({
  browserApi: vi.fn().mockResolvedValue([]),
}));

const mockedBrowserApi = vi.mocked(browserApi);

describe("alerts", () => {
  it("fetchUnreadAlerts / acknowledgeAlert hit the expected endpoints", () => {
    fetchUnreadAlerts();
    expect(mockedBrowserApi).toHaveBeenCalledWith("/alerts/", { method: "GET" });

    acknowledgeAlert(1);
    expect(mockedBrowserApi).toHaveBeenCalledWith("/alerts/1/acknowledge/", {
      method: "POST",
    });
  });
});
