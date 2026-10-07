import type { Localized } from "@/content/types";
import { ApiError } from "./api";

export type Effect = "computed" | "reliable" | "finer";
export type Effects = Record<Effect, string[]>;
export type IndicatorStatus = "official" | "open" | "estimated" | "missing";

export type DataRequestRow = {
  code: string;
  priority: string;
  priority_label: Localized;
  holders: string[];
  alternatives: string[];
  complementary: string[];
  data: Localized;
  detail: Localized;
  format: Localized;
  frequency: Localized;
  value: Localized;
  effects: Effects;
  finer_scale: Localized | null;
  themes: string[];
  requires_also: string[];
  context: boolean;
  boundaries: boolean;
};
export type Tracking = {
  status: string;
  status_label: Localized | null;
  date: string | null;
  updated_by: string | null;
  history: { status: string; date: string; by: string }[];
};
export type InstitutionRow = {
  code: string;
  name: Localized;
  kind: string;
  to_verify: boolean;
  priority: string | null;
  priority_label: Localized | null;
  requests: string[];
  effects: Effects;
  computed_with: string[];
  themes: string[];
  sentence: Localized;
  tracking: Tracking;
};
export type AxisRow = {
  code: string;
  label: Localized;
  total: number;
  available: number;
  counts: Record<IndicatorStatus, number>;
  indicators: string[];
};
export type IndicatorRow = {
  code: string;
  axis: string;
  label: Localized;
  status: IndicatorStatus;
  units: number;
  missing_units: number;
};
export type DataNeeds = {
  territory: string;
  label: Localized;
  to_verify_label: Localized;
  rules_status: string;
  summary: { total: number; available: number; missing: number };
  statuses: Record<IndicatorStatus, Localized>;
  effects: Record<Effect, { verb: Localized; label: Localized }>;
  indicators: IndicatorRow[];
  axes: AxisRow[];
  requests: DataRequestRow[];
  institutions: InstitutionRow[];
  themes: Record<string, Localized>;
  tracking_statuses: Record<string, Localized>;
};

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { cache: "no-store", credentials: "same-origin", ...init });
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
  return (await response.json()) as T;
}

export const fetchDataNeeds = (code: string) =>
  call<DataNeeds>(`/api/territories/${code}/data-needs`);
export const saveTracking = (code: string, institution: string, status: string, date: string) =>
  call<Tracking>(`/api/territories/${code}/data-needs/institutions/${institution}/tracking`, {
    method: "PUT",
    body: JSON.stringify({ status, date }),
    headers: { "Content-Type": "application/json" },
  });

export type Simulation = {
  /** Requests whose every holder is selected. */
  obtained: Set<string>;
  computed: Set<string>;
  reliable: Set<string>;
  finer: Set<string>;
  available: number;
  total: number;
  axes: Record<string, { available: number; computed: number; reliable: number; finer: number }>;
};

/**
 * « Si nous obtenons les données de… »: nothing is added, the effects already computed by the
 * server are only combined. A request counts once ALL its holders are selected (a request to
 * several communes covers each one's territory); an indicator to compute also needs the
 * requests it depends on (`requires_also`). Each indicator counts under one effect only:
 * computed first, then made reliable, then refined.
 */
export function simulate(data: DataNeeds, selected: Set<string>): Simulation {
  const obtained = new Set(
    data.requests.filter((r) => r.holders.every((h) => selected.has(h))).map((r) => r.code),
  );
  const computed = new Set<string>();
  const reliable = new Set<string>();
  const finer = new Set<string>();
  for (const request of data.requests) {
    if (!obtained.has(request.code)) continue;
    if (request.requires_also.every((code) => obtained.has(code)))
      request.effects.computed.forEach((c) => computed.add(c));
    request.effects.reliable.forEach((c) => reliable.add(c));
    request.effects.finer.forEach((c) => finer.add(c));
  }
  computed.forEach((c) => reliable.delete(c));
  computed.forEach((c) => finer.delete(c));
  reliable.forEach((c) => finer.delete(c));
  const axes: Simulation["axes"] = {};
  for (const axis of data.axes) {
    const has = (set: Set<string>) => axis.indicators.filter((c) => set.has(c)).length;
    axes[axis.code] = {
      available: axis.available + has(computed),
      computed: has(computed),
      reliable: has(reliable),
      finer: has(finer),
    };
  }
  return {
    obtained,
    computed,
    reliable,
    finer,
    available: data.summary.available + computed.size,
    total: data.summary.total,
    axes,
  };
}
