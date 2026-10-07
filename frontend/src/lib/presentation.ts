import { ApiError } from "./api";

export type Text = { fr: string; ar?: string | null };
export type StepCode =
  | "home"
  | "stakes"
  | "map"
  | "sheet"
  | "compare"
  | "citizens"
  | "report"
  | "data_needs"
  | "proposal";

export type Scenario = {
  territory: string;
  data_note: Text;
  steps: StepCode[];
  map: { indicator: string };
  sheet: { unit: number; name: string };
  compare: { units: number[] };
  citizens: { scale: "unit" | "commune"; unit: number; name: string };
  report: { unit: number; name: string };
  data_needs: { suggested: string[] };
  stakes: { sentence: Text };
  proposal: { title: Text; items: Text[]; contact: string[] };
};

/** French until the Arabic texts are written (later stage). */
export const text = (value: Text, locale: "fr" | "ar") => (locale === "ar" && value.ar) || value.fr;

export async function fetchScenario(code: string): Promise<Scenario> {
  const response = await fetch(`/api/presentation/${code}`, { cache: "no-store" });
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
  return (await response.json()) as Scenario;
}

/**
 * Everything the slides need, fetched at launch (BRIEF §9.9: preloading for an offline demo).
 * Every address is local: the presentation never calls an outside service.
 */
export function preloadUrls(s: Scenario): string[] {
  const code = s.territory;
  return [
    `/api/territories/${code}/diagnostic`,
    `/api/territories/${code}/units`,
    `/api/territories/${code}/facilities`,
    `/api/tiles/${code}/info`,
    `/api/territories/${code}/citizens?scale=${s.citizens.scale}`,
    `/api/territories/${code}/units/${s.citizens.unit}/crossing?scale=${s.citizens.scale}`,
    `/api/territories/${code}/units/${s.report.unit}/reports`,
    `/api/territories/${code}/data-needs`,
  ];
}

export type Preload = {
  ready: boolean;
  failed: string[];
  fictitious: boolean;
  /** Names of the institutions to tick in the simulator, in the scenario's order. */
  suggested: { fr: string; ar: string }[];
};

export async function preload(s: Scenario): Promise<Preload> {
  const failed: string[] = [];
  let fictitious = false;
  let suggested: Preload["suggested"] = [];
  await Promise.all(
    preloadUrls(s).map(async (url) => {
      try {
        const response = await fetch(url, { credentials: "same-origin" });
        if (!response.ok) failed.push(url);
        else if (url.includes("/citizens?")) {
          const body = (await response.json()) as { fictitious?: boolean };
          fictitious = Boolean(body.fictitious);
        } else if (url.endsWith("/data-needs")) {
          const body = (await response.json()) as {
            institutions: { code: string; name: { fr: string; ar: string } }[];
          };
          suggested = s.data_needs.suggested
            .map((code) => body.institutions.find((i) => i.code === code)?.name)
            .filter((name): name is { fr: string; ar: string } => name !== undefined);
        }
      } catch {
        failed.push(url);
      }
    }),
  );
  return { ready: failed.length === 0, failed, fictitious, suggested };
}

/** Steps showing citizen contributions (the « Données fictives » banner applies there). */
export const CITIZEN_STEPS: StepCode[] = ["citizens", "report"];
