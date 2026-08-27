import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

vi.mock("next/headers", () => ({
  cookies: vi.fn(),
}));

import { cookies } from "next/headers";
import { getApi } from "@/lib/api/client";

const mockedCookies = vi.mocked(cookies);

describe("client (server-side getApi)", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("attaches the Authorization header when a cookie token is present", async () => {
    mockedCookies.mockResolvedValue({
      get: vi.fn().mockReturnValue({ value: "abc123" }),
    } as never);
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1 }),
    } as Response);

    const result = await getApi<{ id: number }>("/academic/years/");

    expect(result).toEqual({ id: 1 });
    const [, options] = vi.mocked(global.fetch).mock.calls[0];
    expect((options as RequestInit).headers).toMatchObject({
      Authorization: "Bearer abc123",
    });
  });

  it("omits the Authorization header when there is no cookie token", async () => {
    mockedCookies.mockResolvedValue({
      get: vi.fn().mockReturnValue(undefined),
    } as never);
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ([]),
    } as Response);

    await getApi("/reference/countries/");

    const [, options] = vi.mocked(global.fetch).mock.calls[0];
    expect((options as RequestInit).headers).not.toHaveProperty("Authorization");
  });

  it("throws when the response is not ok", async () => {
    mockedCookies.mockResolvedValue({
      get: vi.fn().mockReturnValue(undefined),
    } as never);
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    } as Response);

    await expect(getApi("/broken/")).rejects.toThrow("API request failed: 500");
  });
});
