import { describe, expect, it } from "vitest";
import {
  attentionPoints,
  classOf,
  quantileBreaks,
  type DiagnosticUnit,
  type IndicatorMeta,
} from "./diagnostic";

const meta = (code: string, direction: IndicatorMeta["direction"]): IndicatorMeta => ({
  code,
  axis: "a",
  label: { fr: code, ar: code },
  unit: { fr: "%", ar: "%" },
  direction,
  decimals: 1,
  reference: { type: "relative", value: 10 },
  source_expected: "",
  note: null,
  threshold_note: null,
  provisional: false,
  highlight: false,
  requested_from: null,
  formula: "raw",
  spatial: false,
});

describe("map classes", () => {
  it("splits values into five quantile classes", () => {
    const breaks = quantileBreaks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    expect(breaks).toHaveLength(4);
    expect(classOf(1, breaks)).toBe(0);
    expect(classOf(10, breaks)).toBe(4);
  });
});

describe("attention points", () => {
  it("keeps deficits and watch statuses, most marked first, whatever the direction", () => {
    const unit = {
      values: {
        A: { value: 5, status: "deficit_marked", rank: 1, ratio: 0.5 },
        B: { value: 15, status: "deficit_marked", rank: 1, ratio: 1.5 },
        C: { value: 9, status: "watch", rank: 1, ratio: 0.9 },
        D: { value: 20, status: "ok", rank: 1, ratio: 2 },
        E: { value: null, status: "not_available", rank: null },
      },
    } as unknown as DiagnosticUnit;
    const points = attentionPoints(unit, [
      meta("A", "higher_better"),
      meta("B", "lower_better"),
      meta("C", "higher_better"),
      meta("D", "higher_better"),
      meta("E", "higher_better"),
    ]);
    expect(points.map((p) => p.meta.code)).toEqual(["A", "B", "C"]);
  });
});
