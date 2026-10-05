import type { Localized } from "@/content/types";
import { ApiError } from "./api";

export type SourceInfo = {
  name: string;
  producer: string;
  license: string | null;
  badge: "official" | "open" | "estimated" | "fictitious";
  retrieved_at: string | null;
  data_date: string | null;
  notes: string | null;
};

export type UnitProperties = {
  id: number;
  name_fr: string;
  name_ar: string | null;
  level: string;
  term: Localized | null;
  parent_fr: string | null;
  parent_ar: string | null;
  area_km2: number | null;
  official_code: string | null;
  facilities: Record<string, number>;
  label: [number, number];
};

export type UnitCollection = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    id: number;
    geometry: GeoJSON.Geometry;
    properties: UnitProperties;
  }[];
  meta: {
    imported: boolean;
    scope: string;
    scopes: { code: string; label: Localized; default: boolean }[];
    bbox: number[] | null;
    source: SourceInfo | null;
  };
};

export type FacilityCategory = {
  code: string;
  label: Localized;
  color: string;
  group: string;
  count: number;
};

export type FacilityCollection = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    geometry: GeoJSON.Point;
    properties: { id: number; category: string; name: string | null; name_ar: string | null };
  }[];
  meta: { categories: FacilityCategory[]; source: SourceInfo | null };
};

export type TilesInfo =
  | { available: false }
  | { available: true; build: string | null; retrieved_at: string | null; attribution: string };

async function get<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store", credentials: "same-origin" });
  if (!response.ok) throw new ApiError(response.status, `HTTP ${response.status}`);
  return (await response.json()) as T;
}

export const fetchUnits = (code: string, scope?: string) =>
  get<UnitCollection>(`/api/territories/${code}/units${scope ? `?scope=${scope}` : ""}`);
export const fetchFacilities = (code: string, scope?: string) =>
  get<FacilityCollection>(`/api/territories/${code}/facilities${scope ? `?scope=${scope}` : ""}`);
export const fetchTilesInfo = (code: string) => get<TilesInfo>(`/api/tiles/${code}/info`);
