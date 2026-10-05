import { layers, namedFlavor } from "@protomaps/basemaps";
import type { ExpressionSpecification, FilterSpecification, LayerSpecification } from "maplibre-gl";
import type { Locale } from "@/content/types";
import rules from "@/content/cartography-rules.json";

/**
 * Base-map layers for MAJAL, built from the Protomaps style and the cartography rules
 * (src/content/cartography-rules.json): the Kingdom of Morocco is shown in its entirety.
 * Only the display is filtered; the tile data is left untouched.
 */

/** Visible boundaries: undisputed state borders only. */
export const BOUNDARY_FILTER: ExpressionSpecification = [
  "all",
  ["<=", ["to-number", ["get", "kind_detail"], 99], rules.boundaries.max_kind_detail],
  ["!", ["to-boolean", ["get", "disputed"]]],
  ["!", ["in", ["to-string", ["get", "kind"]], ["literal", rules.boundaries.hide_kinds]]],
];

/** Labels that would present the southern provinces as a separate territory are hidden. */
export const LABEL_FILTER: ExpressionSpecification = [
  "!",
  [
    "any",
    ...rules.labels.fields.flatMap((field) =>
      rules.labels.hide_if_contains.map(
        (needle) =>
          [
            "in",
            needle,
            ["to-string", ["coalesce", ["get", field], ""]],
          ] as ExpressionSpecification,
      ),
    ),
  ],
];

function combine(filter: FilterSpecification | undefined, extra: ExpressionSpecification) {
  // Protomaps uses legacy filters (["==", "kind", "x"]); turn them into expressions.
  const legacy = (f: unknown): ExpressionSpecification => {
    if (!Array.isArray(f)) return ["literal", true] as unknown as ExpressionSpecification;
    const [op, key, ...values] = f as [string, unknown, ...unknown[]];
    if (typeof key === "string" && ["==", "!=", "<", "<=", ">", ">="].includes(op)) {
      return [op, ["get", key], values[0]] as unknown as ExpressionSpecification;
    }
    if (typeof key === "string" && op === "in") {
      return ["in", ["get", key], ["literal", values]] as unknown as ExpressionSpecification;
    }
    if (op === "all" || op === "any") {
      return [op, ...(f as unknown[]).slice(1).map(legacy)] as unknown as ExpressionSpecification;
    }
    return f as ExpressionSpecification;
  };
  return (filter ? ["all", legacy(filter), extra] : extra) as FilterSpecification;
}

export function basemapLayers(locale: Locale): LayerSpecification[] {
  const flavor = {
    ...namedFlavor("light"),
    background: "#f6f3ec",
    earth: "#f6f3ec",
    water: "#cfdfdd",
  };
  return layers("protomaps", flavor, { lang: locale }).flatMap((layer) => {
    const sourceLayer = (layer as { "source-layer"?: string })["source-layer"];
    if (sourceLayer === "boundaries") {
      // Keep only the state-border layer, with the rule filter; drop sub-national lines.
      if (layer.id !== "boundaries_country") return [];
      return [{ ...layer, filter: BOUNDARY_FILTER } as LayerSpecification];
    }
    if (sourceLayer === "places" || layer.type === "symbol") {
      const filter = (layer as { filter?: FilterSpecification }).filter;
      return [{ ...layer, filter: combine(filter, LABEL_FILTER) } as LayerSpecification];
    }
    return [layer];
  });
}
