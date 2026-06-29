import { describe, expect, it } from "vitest";
import {
  nextTransitions,
  statusLabels,
  statusTone,
} from "@/components/academic-years/status";

describe("statusLabels", () => {
  it("maps every status to a French label", () => {
    expect(statusLabels.initialization).toBe("Initialisation");
    expect(statusLabels.recommendation).toBe("Recommandation");
    expect(statusLabels.consolidation).toBe("Consolidation");
    expect(statusLabels.pre_assignment).toBe("Pre-affectation");
    expect(statusLabels.validation).toBe("Validation");
    expect(statusLabels.closed).toBe("Cloturee");
  });
});

describe("statusTone", () => {
  it("assigns distinct color classes to each status", () => {
    const tones = Object.values(statusTone);
    const unique = new Set(tones);
    expect(unique.size).toBe(tones.length);
  });

  it("uses red for closed state", () => {
    expect(statusTone.closed).toContain("red");
  });

  it("uses emerald for validation state", () => {
    expect(statusTone.validation).toContain("emerald");
  });
});

describe("nextTransitions", () => {
  it("defines a transition for initialization", () => {
    expect(nextTransitions.initialization?.transition).toBe("open-recommendation");
  });

  it("defines a transition for pre_assignment", () => {
    expect(nextTransitions.pre_assignment?.transition).toBe(
      "submit-for-validation",
    );
  });

  it("does not define a transition for closed (terminal state)", () => {
    expect(nextTransitions.closed).toBeUndefined();
  });

  it("all defined transitions have a non-empty label", () => {
    Object.values(nextTransitions).forEach((t) => {
      expect(t?.label.length).toBeGreaterThan(0);
    });
  });
});
