export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Localized = { fr: string; ar: string };

export type Health = {
  status: "ok" | "degraded";
  version: string;
  database: { ok: boolean; postgis: string | null; pgvector: string | null; message: string };
  config: { ok: boolean; territories: number; message: string };
};

export type TerritorySummary = {
  code: string;
  name: Localized;
  region: Localized;
  study_area: Localized;
  profiles: { indicators: string; taxonomy: string };
  scopes: { code: string; label: Localized; default: boolean }[];
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path} → HTTP ${response.status}`);
  return (await response.json()) as T;
}

export const fetchHealth = () => getJson<Health>("/health");
export const fetchTerritories = () => getJson<TerritorySummary[]>("/api/territories");
