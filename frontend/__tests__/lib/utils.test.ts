import { describe, expect, it } from "vitest";
import { createIdMap } from "@/lib/utils";

describe("createIdMap", () => {
  it("builds a Map keyed by id", () => {
    const items = [
      { id: 1, name: "Alice" },
      { id: 2, name: "Bob" },
    ];
    const map = createIdMap(items);
    expect(map.get(1)).toEqual({ id: 1, name: "Alice" });
    expect(map.get(2)).toEqual({ id: 2, name: "Bob" });
  });

  it("returns empty Map for empty input", () => {
    expect(createIdMap([]).size).toBe(0);
  });

  it("last item wins on duplicate id", () => {
    const items = [
      { id: 1, name: "Alice" },
      { id: 1, name: "Alice2" },
    ];
    const map = createIdMap(items);
    expect(map.get(1)?.name).toBe("Alice2");
  });

  it("preserves all fields of each item", () => {
    const items = [{ id: 42, code: "SN", label: "Informatique" }];
    const map = createIdMap(items);
    expect(map.get(42)).toEqual({ id: 42, code: "SN", label: "Informatique" });
  });
});
