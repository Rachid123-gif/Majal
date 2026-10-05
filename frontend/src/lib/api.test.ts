import { describe, expect, it } from "vitest";
import { safeNextPath } from "./api";

describe("safeNextPath", () => {
  it("keeps same-site paths", () => {
    expect(safeNextPath("/presentation?territoire=rabat")).toBe("/presentation?territoire=rabat");
  });

  it.each([
    null,
    "",
    "https://evil.example",
    "//evil.example",
    "/\\evil.example",
    "javascript:alert(1)",
  ])("falls back to the dashboard for %s", (value) => {
    expect(safeNextPath(value)).toBe("/tableau-de-bord");
  });
});
