import type { Localized } from "@/content/types";

export type { Localized };

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

export type Me = { username: string; display_name: Localized; roles: string[] };

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

// Same-origin calls: /api/* is forwarded to the backend by next.config.ts.
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { cache: "no-store", credentials: "same-origin", ...init });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Non-JSON error body.
    }
    throw new ApiError(response.status, detail);
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}

export const fetchHealth = () => request<Health>("/api/health");
export const fetchTerritories = () => request<TerritorySummary[]>("/api/territories");
export const fetchMe = () => request<Me>("/api/auth/me");
export const login = (username: string, password: string) =>
  request<Me>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
export const logout = () => request<void>("/api/auth/logout", { method: "POST" });

/** Only same-site relative paths are accepted as a post-login destination. */
export function safeNextPath(value: string | null, fallback = "/tableau-de-bord"): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.startsWith("/\\")) {
    return fallback;
  }
  return value;
}
