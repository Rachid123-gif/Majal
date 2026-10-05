import { featureFilter } from "@maplibre/maplibre-gl-style-spec";
import { describe, expect, it } from "vitest";
import rules from "@/content/cartography-rules.json";
import { BOUNDARY_FILTER, LABEL_FILTER, basemapLayers } from "./basemapStyle";

/*
 * Territorial integrity of the Kingdom of Morocco (non-negotiable, see CLAUDE.md):
 * disputed or « unrecognized » boundaries and any label presenting the southern
 * provinces as a separate territory must never be displayed.
 */

type Props = Record<string, string | number | boolean | undefined>;
const passes = (filter: unknown, properties: Props, type: 1 | 2 = 2) =>
  featureFilter(filter as never, "layers[0].filter").filter(
    { zoom: 5 } as never,
    {
      type,
      properties,
      geometry: [],
    } as never,
  );

describe("base map — Kingdom of Morocco in its entirety", () => {
  for (const locale of ["fr", "ar"] as const) {
    const layers = basemapLayers(locale);
    const boundaryLayers = layers.filter(
      (l) => (l as { "source-layer"?: string })["source-layer"] === "boundaries",
    );

    it(`(${locale}) draws boundaries with a single, filtered layer`, () => {
      expect(boundaryLayers).toHaveLength(1);
      expect((boundaryLayers[0] as { filter: unknown }).filter).toEqual(BOUNDARY_FILTER);
    });

    it(`(${locale}) filters every label layer`, () => {
      const symbols = layers.filter((l) => l.type === "symbol");
      expect(symbols.length).toBeGreaterThan(0);
      for (const layer of symbols) {
        expect(JSON.stringify((layer as { filter: unknown }).filter)).toContain("الصحراء الغربية");
      }
    });
  }

  it("never displays a disputed or unrecognized boundary", () => {
    expect(rules.boundaries.hide_disputed).toBe(true);
    expect(passes(BOUNDARY_FILTER, { kind: "country", kind_detail: 2, disputed: true })).toBe(
      false,
    );
    expect(passes(BOUNDARY_FILTER, { kind: "unrecognized_country", kind_detail: 3 })).toBe(false);
    expect(passes(BOUNDARY_FILTER, { kind: "unrecognized_country", kind_detail: 2 })).toBe(false);
    expect(passes(BOUNDARY_FILTER, { kind: "region", kind_detail: 4 })).toBe(false);
    expect(passes(BOUNDARY_FILTER, { kind: "macroregion", kind_detail: 3 })).toBe(false);
  });

  it("keeps undisputed state borders", () => {
    expect(passes(BOUNDARY_FILTER, { kind: "country", kind_detail: 2 })).toBe(true);
    expect(passes(BOUNDARY_FILTER, { kind: "country", kind_detail: 2, disputed: false })).toBe(
      true,
    );
  });

  it("hides labels naming the southern provinces as a separate territory, in any language", () => {
    for (const properties of [
      { kind: "country", name: "Western Sahara" },
      { kind: "country", "name:fr": "Sahara occidental" },
      { kind: "country", "name:ar": "الصحراء الغربية" },
      { kind: "region", name2: "Sahara Occidental" },
      { kind: "country", "name:en": "Sahrawi Arab Democratic Republic" },
    ]) {
      expect(passes(LABEL_FILTER, properties, 1)).toBe(false);
    }
    expect(
      passes(LABEL_FILTER, { kind: "country", "name:fr": "Maroc", "name:ar": "المغرب" }, 1),
    ).toBe(true);
    expect(
      passes(LABEL_FILTER, { kind: "locality", name: "Laâyoune", "name:ar": "العيون" }, 1),
    ).toBe(true);
  });
});
