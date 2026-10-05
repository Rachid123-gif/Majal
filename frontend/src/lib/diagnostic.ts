import type { Locale, Localized } from "@/content/types";
import { ApiError } from "./api";
import { formatNumber } from "./format";

export type Status =
  | "deficit_marked"
  | "watch"
  | "ok"
  | "context"
  | "not_evaluable"
  | "not_available"
  | "not_applicable";

export type Badge = "official" | "open" | "estimated" | "fictitious";

export type IndicatorValue = {
  value: number | null;
  status: Status;
  rank: number | null;
  rank_of?: number;
  year?: number | null;
  badge?: Badge;
  method?: "direct" | "derived" | "modeled";
  reliability?: number;
  provisional?: boolean;
  sources?: string[];
  extra?: Record<string, number>;
  ratio?: number;
  gap_pct?: number;
  reason?: string;
  excluded_from_ranking?: boolean;
};

export type IndicatorMeta = {
  code: string;
  axis: string;
  label: Localized;
  unit: Localized;
  direction: "higher_better" | "lower_better" | "neutral";
  decimals: number;
  reference: { type: "relative" | "norm"; value: number; source?: string } | null;
  source_expected: string;
  note: string | null;
  threshold_note: string | null;
  provisional: boolean;
  highlight: boolean;
  requested_from: string | null;
  formula: string;
  spatial: boolean;
};

export type DiagnosticUnit = {
  id: number;
  name_fr: string;
  name_ar: string | null;
  level: string;
  official_code: string | null;
  area_km2: number | null;
  scopes: string[];
  warning: Localized | null;
  excluded_from_ranking: boolean;
  values: Record<string, IndicatorValue>;
};

export type DiagnosticData = {
  territory: string;
  computed_at: string;
  grid: {
    version: string;
    label: Localized;
    status: string;
    axes: { code: string; number: number; label: Localized }[];
  };
  evaluation: {
    label: Localized;
    statuses: Record<Status, Localized>;
    reference_scope: string;
    reference_label: Localized;
    facility_minimum: number;
  };
  indicators: IndicatorMeta[];
  units: DiagnosticUnit[];
  meta: { diagnostic_id: number; computed_at: string; recomputed: boolean; author: string | null };
  typology?: Typology;
};

export type TypologyUnit = {
  group: number;
  profile: string;
  label: Localized;
  traits: Localized[];
};

export type Typology =
  | { available: false; reason: string; unclassified: number[] }
  | {
      available: true;
      label: Localized;
      status: string;
      variables: string[];
      groups: {
        group: number;
        profile: string;
        label: Localized;
        description: Localized | null;
        traits: Localized[];
        members: number[];
      }[];
      units: Record<string, TypologyUnit>;
      unclassified: number[];
    };

export async function fetchDiagnostic(code: string, recompute = false): Promise<DiagnosticData> {
  const response = await fetch(`/api/territories/${code}/diagnostic`, {
    method: recompute ? "POST" : "GET",
    cache: "no-store",
    credentials: "same-origin",
  });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // ignore
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as DiagnosticData;
}

export const STATUS_STYLE: Record<Status, { color: string; symbol: string; text: string }> = {
  deficit_marked: { color: "#a8461f", symbol: "▼", text: "text-white" },
  watch: { color: "#e0a43a", symbol: "◐", text: "text-petrol" },
  ok: { color: "#5b9aa0", symbol: "✓", text: "text-white" },
  context: { color: "#c9cfd1", symbol: "○", text: "text-petrol" },
  not_evaluable: { color: "#e3ded2", symbol: "?", text: "text-petrol" },
  not_available: { color: "#ece8de", symbol: "—", text: "text-slate" },
  not_applicable: { color: "#ece8de", symbol: "∅", text: "text-slate" },
};

/** 5-class sequential palette, readable by colour-blind viewers (ColorBrewer YlGnBu). */
export const SEQUENTIAL = ["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"];
export const NO_DATA = "#e8e4da";

export function quantileBreaks(values: number[], classes = 5): number[] {
  const sorted = [...values].sort((a, b) => a - b);
  if (!sorted.length) return [];
  const breaks: number[] = [];
  for (let i = 1; i < classes; i++) {
    const position = (sorted.length - 1) * (i / classes);
    const low = Math.floor(position);
    const high = Math.ceil(position);
    breaks.push(sorted[low] + (sorted[high] - sorted[low]) * (position - low));
  }
  return breaks;
}

export function classOf(value: number, breaks: number[]): number {
  let index = 0;
  while (index < breaks.length && value > breaks[index]) index++;
  return index;
}

export function formatValue(value: number | null, meta: IndicatorMeta, locale: Locale): string {
  if (value === null) return "—";
  return formatNumber(value, locale, meta.decimals);
}

export function unitName(unit: DiagnosticUnit, locale: Locale): string {
  return (locale === "ar" && unit.name_ar) || unit.name_fr;
}

/** Points d'attention: the most marked deficits, by deterministic rules (no AI). */
export function attentionPoints(
  unit: DiagnosticUnit,
  indicators: IndicatorMeta[],
  max = 5,
): { meta: IndicatorMeta; value: IndicatorValue; severity: number }[] {
  const items = indicators
    .map((meta) => ({ meta, value: unit.values[meta.code] }))
    .filter(
      (item) =>
        item.value && (item.value.status === "deficit_marked" || item.value.status === "watch"),
    )
    .map((item) => {
      const ratio = item.value.ratio ?? 1;
      const severity = item.meta.direction === "lower_better" ? ratio - 1 : 1 - ratio;
      return { ...item, severity };
    });
  return items.sort((a, b) => b.severity - a.severity).slice(0, max);
}
