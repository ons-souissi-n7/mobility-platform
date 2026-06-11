import { render, screen } from "@testing-library/react";
import { Users } from "lucide-react";
import { describe, expect, it } from "vitest";
import { StatCard } from "@/components/ui/stat-card";

describe("StatCard", () => {
  it("renders the label and value", () => {
    render(<StatCard label="Étudiants" value={42} helper="inscrits" icon={Users} tone="blue" />);
    expect(screen.getByText("Étudiants")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("renders the helper text", () => {
    render(<StatCard label="Total" value={0} helper="aucun résultat" icon={Users} tone="emerald" />);
    expect(screen.getByText("aucun résultat")).toBeInTheDocument();
  });

  it("renders a string value", () => {
    render(<StatCard label="GPA" value="15.50" helper="moyenne" icon={Users} tone="amber" />);
    expect(screen.getByText("15.50")).toBeInTheDocument();
  });
});
