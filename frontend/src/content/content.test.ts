import { describe, expect, it } from "vitest";
import { features } from "./features";
import { landing } from "./landing";

describe("landing content", () => {
  it("shows the same figures in French and Arabic, each with its source", () => {
    const fr = landing.fr.stakes.figures;
    const ar = landing.ar.stakes.figures;
    expect(fr.map((f) => f.value)).toEqual([210, 8, 75, 12]);
    expect(ar.map((f) => f.value)).toEqual(fr.map((f) => f.value));
    for (const figure of [...fr, ...ar]) expect(figure.source.trim()).not.toBe("");
  });

  it("is fully translated: same structure in both languages", () => {
    const shape = (value: unknown): unknown =>
      Array.isArray(value)
        ? value.map(shape)
        : value && typeof value === "object"
          ? Object.fromEntries(Object.entries(value).map(([k, v]) => [k, shape(v)]))
          : typeof value;
    expect(shape(landing.ar)).toEqual(shape(landing.fr));
  });

  it("describes every feature in both languages and marks only delivered work as available", () => {
    expect(features).toHaveLength(7);
    for (const feature of features) {
      expect(feature.points.fr.length).toBe(feature.points.ar.length);
      expect(feature.title.ar).toMatch(/[؀-ۿ]/);
    }
    // Delivered: stage 2 (diagnostic map, commune sheet, comparison), stage 3 (AI report).
    const available = features.filter((f) => f.status === "available").map((f) => f.id);
    expect(available).toEqual(["diagnostic", "commune", "report"]);
  });
});
