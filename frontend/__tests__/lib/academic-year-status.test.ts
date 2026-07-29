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
    expect(statusLabels.candidature).toBe("Candidature");
    expect(statusLabels.import).toBe("Import");
    expect(statusLabels.pre_assignment).toBe("Affectation en cours");
    expect(statusLabels.validation).toBe("Validation");
    expect(statusLabels.published).toBe("Publiée");
    expect(statusLabels.finalization).toBe("Finalisation CTI");
    expect(statusLabels.closed).toBe("Clôturée");
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

  it("defines a transition for recommendation", () => {
    expect(nextTransitions.recommendation?.transition).toBe("start-candidature");
  });

  it("defines a transition for import", () => {
    expect(nextTransitions.import?.transition).toBe("launch-assignment");
  });

  it("defines a transition for validation", () => {
    expect(nextTransitions.validation?.transition).toBe("publish-results");
  });

  it("defines a transition for candidature (manual close-wishes button)", () => {
    expect(nextTransitions.candidature?.transition).toBe("close-wishes");
  });

  it("does not define a transition for pre_assignment (automatic after algo)", () => {
    expect(nextTransitions.pre_assignment).toBeUndefined();
  });

  it("defines a transition for published (manual finalize-cti button)", () => {
    expect(nextTransitions.published?.transition).toBe("finalize-cti");
  });

  it("defines a transition for finalization (manual close button)", () => {
    expect(nextTransitions.finalization?.transition).toBe("close");
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
