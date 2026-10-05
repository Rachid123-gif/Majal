import { describe, expect, it } from "vitest";
import { formatNumber } from "./format";

describe("formatNumber", () => {
  it("follows French rules: narrow no-break space for thousands, decimal comma", () => {
    expect(formatNumber(1191, "fr")).toBe("1 191");
    expect(formatNumber(400.47, "fr", 1)).toBe("400,5");
  });
});
