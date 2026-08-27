import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AdminLoading from "@/app/admin/loading";
import AdminPage from "@/app/admin/page";
import { redirect } from "next/navigation";

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
}));

describe("AdminPage", () => {
  it("redirects to the analytics dashboard", () => {
    AdminPage();
    expect(redirect).toHaveBeenCalledWith("/admin/analytiques");
  });
});

describe("AdminLoading", () => {
  it("renders a loading spinner without crashing", () => {
    render(<AdminLoading />);
    expect(document.body).toBeTruthy();
  });
});
