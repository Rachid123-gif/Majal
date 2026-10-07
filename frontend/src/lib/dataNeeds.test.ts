import { describe, expect, it } from "vitest";
import { DATA } from "@/lib/dataNeeds.fixture";
import { simulate } from "@/lib/dataNeeds";

describe("simulate", () => {
  it("adds nothing when nothing is ticked", () => {
    const sim = simulate(DATA, new Set());
    expect([sim.available, sim.total, sim.computed.size]).toEqual([2, 4, 0]);
  });

  it("needs both holders for an indicator computed jointly", () => {
    const hcpOnly = simulate(DATA, new Set(["hcp"]));
    expect(hcpOnly.computed.size).toBe(0);
    expect([...hcpOnly.finer]).toEqual(["DEM_POP"]);
    const both = simulate(DATA, new Set(["hcp", "aref"]));
    expect([...both.computed]).toEqual(["EDU_ECOLES"]);
    expect([...both.reliable]).toEqual(["EDU_PROX"]);
    expect(both.available).toBe(3);
    expect(both.axes.education).toEqual({ available: 2, computed: 1, reliable: 1, finer: 0 });
  });

  it("counts a request to several institutions only when all are ticked", () => {
    expect(simulate(DATA, new Set(["rabat"])).obtained.has("voirie")).toBe(false);
    expect(simulate(DATA, new Set(["rabat", "sale"])).obtained.has("voirie")).toBe(true);
  });
});
