import type { Localized } from "@/content/types";
import { ApiError } from "./api";

export type ThemeRow = { code: string; label: Localized; count: number; share: number | null };
export type UnitRow = {
  id: number;
  name_fr: string;
  name_ar: string | null;
  count: number;
  per_10k: number | null;
  main_theme: string | null;
  describe_with_counts: boolean;
  members: number[];
};
export type Summary = {
  total: number;
  located: number;
  analysed_by_ai: number;
  secondary_included: boolean;
  secondary_note: Localized | null;
  themes: ThemeRow[];
  units: UnitRow[];
  languages: [string, number][];
  tonalities: [string, number][];
  rules: { min_contributions: number; percent_min_total: number };
};
export type Prf = { precision: number | null; recall: number | null; f1: number | null };
export type Accuracy = { accuracy: number | null; n: number; correct: number };
export type EvaluationResult = {
  /** « professor »: reference evaluation; « second_model »: AI annotator, awaiting review. */
  kind?: "professor" | "second_model";
  title?: Localized;
  note?: Localized | null;
  n: number;
  n_ai: number;
  base: Localized;
  themes: { model: Prf; keywords: Prf };
  main_theme?: { model: Accuracy | null };
  tonality: { model: Accuracy; keywords: Accuracy };
  language?: { model: Accuracy; keywords: Accuracy };
  location?: { located: number; correct: number; wrong: number; not_located: number };
};
export type Evaluation = {
  provisional: EvaluationResult | null;
  reference: EvaluationResult | null;
  anonymisation: { rate: number; masked: number; traps: number; base: Localized } | null;
};
export type Dashboard = {
  territory: string;
  taxonomy: {
    label: Localized;
    themes: { code: string; label: Localized; indicators: string[] }[];
    tonalities: Record<string, Localized>;
  };
  languages: Record<string, Localized>;
  consultations: { id: number; code: string; title: string; badge: string }[];
  fictitious: boolean;
  banner: Localized | null;
  summary: Summary;
  evaluation: Evaluation;
};
export type Verbatim = {
  id: string;
  original: string;
  translation_fr: string | null;
  translation_note: Localized | null;
  language: string;
  language_note: Localized | null;
  themes: string[];
  tonality: string;
  place: string | null;
  unit: { id: number; name_fr: string; name_ar: string | null } | null;
  sure: { language: boolean; theme: boolean };
  badge: string;
};
export type UnitCitizens = {
  fictitious: boolean;
  banner: Localized | null;
  summary: Summary;
  verbatims: Verbatim[];
};
export type CrossingIndicator = {
  code: string;
  label: Localized | null;
  value: number | null;
  unit: Localized | null;
  decimals: number;
  status: string | null;
  status_label: Localized | null;
  unfavourable?: boolean;
  aggregate?: {
    unfavourable_units: { name_fr: string; name_ar: string | null }[];
    units: number;
    population_share: number | null;
  };
};
export type CrossingRow = {
  theme: string;
  label: Localized;
  count: number;
  share: number | null;
  indicators: CrossingIndicator[];
  verdict: string;
  verdict_label: Localized | null;
  data_request: { data: Localized; holder: Localized } | null;
};
export type Scale = "unit" | "commune";
export type Crossing = {
  unit: { id: number; name_fr: string; name_ar: string | null };
  scale: Scale;
  members: string[];
  fictitious: boolean;
  banner: Localized | null;
  evaluation_label: Localized;
  total: number;
  secondary_included: boolean;
  secondary_note: Localized | null;
  rows: CrossingRow[];
  rules: { min_contributions: number; percent_min_total: number; strong_share: number };
};
export type Filters = {
  scale?: Scale;
  theme?: string;
  unit?: number;
  language?: string;
  tonality?: string;
  secondary?: boolean;
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

function query(filters: Filters): string {
  const params = new URLSearchParams();
  if (filters.theme) params.set("theme", filters.theme);
  if (filters.unit !== undefined) params.set("unit", String(filters.unit));
  if (filters.language) params.set("language", filters.language);
  if (filters.tonality) params.set("tonality", filters.tonality);
  if (filters.secondary) params.set("secondary", "true");
  if (filters.scale && filters.scale !== "unit") params.set("scale", filters.scale);
  const text = params.toString();
  return text ? `?${text}` : "";
}

export const fetchCitizens = (code: string, filters: Filters = {}) =>
  call<Dashboard>(`/api/territories/${code}/citizens${query(filters)}`);
export const fetchVerbatims = (code: string, filters: Filters = {}) =>
  call<Record<string, Verbatim[]>>(
    `/api/territories/${code}/citizens/verbatims${query({ ...filters, secondary: false, scale: undefined, unit: filters.scale === "commune" ? undefined : filters.unit })}`,
  );
export const fetchUnitCitizens = (code: string, unitId: number) =>
  call<UnitCitizens>(`/api/territories/${code}/units/${unitId}/citizens`);
export const fetchCrossing = (
  code: string,
  unitId: number,
  secondary = false,
  scale: Scale = "unit",
) =>
  call<Crossing>(`/api/territories/${code}/units/${unitId}/crossing${query({ secondary, scale })}`);
export const importContributions = (code: string, file: File) =>
  file
    .arrayBuffer()
    .then((body) =>
      call<{ consultation_id: number; rows: number; processing: string }>(
        `/api/territories/${code}/citizens/import?filename=${encodeURIComponent(file.name)}`,
        { method: "POST", body, headers: { "Content-Type": "application/octet-stream" } },
      ),
    );
export const fetchImportProgress = (id: number) =>
  call<{ total: number; analysed: number }>(`/api/citizens/consultations/${id}/progress`);

/** Percentage only when allowed by the rules; otherwise null (show counts). */
export function percent(value: number | null): string | null {
  return value === null ? null : `${Math.round(value * 100)} %`;
}
