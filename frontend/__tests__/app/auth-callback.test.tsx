import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AuthCallbackPage from "@/app/auth/callback/page";
import { getDefaultPath, parseToken, setToken } from "@/lib/auth";

const mockSearchParams = new URLSearchParams();
const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
  useRouter: () => ({ replace: mockReplace }),
}));

vi.mock("@/lib/auth", () => ({
  getDefaultPath: vi.fn().mockReturnValue("/student/tableau-de-bord"),
  parseToken: vi.fn(),
  setToken: vi.fn(),
}));

describe("AuthCallbackPage", () => {
  beforeEach(() => {
    mockSearchParams.forEach((_, key) => mockSearchParams.delete(key));
    mockReplace.mockClear();
    vi.mocked(getDefaultPath).mockClear();
    vi.mocked(parseToken).mockClear();
    vi.mocked(setToken).mockClear();
  });

  it("redirects to the login error page when there is no token", async () => {
    render(<AuthCallbackPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/login?error=auth_failed");
    });
    expect(setToken).not.toHaveBeenCalled();
  });

  it("redirects to the login error page when the token cannot be parsed", async () => {
    mockSearchParams.set("token", "bad-token");
    vi.mocked(parseToken).mockReturnValueOnce(null);
    render(<AuthCallbackPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/login?error=auth_failed");
    });
    expect(setToken).toHaveBeenCalledWith("bad-token");
  });

  it("stores the token and redirects to the role-specific default when next is /", async () => {
    mockSearchParams.set("token", "good-token");
    vi.mocked(parseToken).mockReturnValueOnce({
      sub: "1",
      email: "a@b.com",
      role: "student",
      ine: "12345678A",
      exp: 0,
      iat: 0,
    });
    render(<AuthCallbackPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/student/tableau-de-bord");
    });
  });

  it("redirects to the explicit next destination when provided", async () => {
    mockSearchParams.set("token", "good-token");
    mockSearchParams.set("next", "/admin/analytiques");
    vi.mocked(parseToken).mockReturnValueOnce({
      sub: "1",
      email: "a@b.com",
      role: "admin",
      ine: "",
      exp: 0,
      iat: 0,
    });
    render(<AuthCallbackPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/analytiques");
    });
    expect(getDefaultPath).not.toHaveBeenCalled();
  });
});
