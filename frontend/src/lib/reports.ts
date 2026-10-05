import { ApiError } from "./api";

export type ReportFact = {
  id: string;
  kind: string;
  label: Record<"fr" | "ar", string>;
  text: Record<"fr" | "ar", string>;
  source: string | null;
  year: number | null;
  badge: string | null;
};

export type ReportSection = {
  number: number;
  code: string;
  title: string;
  mode: "ai" | "fallback" | "auto";
  attempts: number;
  duration_s: number;
  paragraphs: { text: string; facts: string[] }[];
  raw: string[];
  issues: string[];
  error: string | null;
  verification: string[];
  sources?: string[];
  notes?: string[];
};

export type Report = {
  id: number;
  language: "fr" | "ar";
  provider: string;
  model: string;
  state: "pending" | "running" | "done" | "failed" | "blocked";
  status: "brouillon" | "relu" | "valide";
  writing_mode: "ai" | "mixed" | "fallback" | null;
  progress: { section?: number; total?: number; title?: string };
  content: {
    title?: string;
    sections?: ReportSection[];
    verification?: { ok: boolean; issues: string[] };
    typology?: string | null;
    grid_label?: string;
    evaluation_label?: string;
  };
  history: { status: string; by: string; at: string }[];
  error: string | null;
  duration_s: number | null;
  created_at: string | null;
  finished_at: string | null;
  cached: boolean;
  /** Written with older data, outline, controls or model. */
  outdated?: boolean;
  fact_sheet?: { facts: ReportFact[] };
};

export type LlmStatus = {
  sovereign_mode: boolean;
  provider: string;
  model: string;
  reachable: boolean;
  model_installed?: boolean;
  error?: string;
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

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const requestReport = (code: string, unitId: number, language: "fr" | "ar", force = false) =>
  call<Report>(`/api/territories/${code}/units/${unitId}/reports`, json({ language, force }));
export const fetchReport = (id: number) => call<Report>(`/api/reports/${id}`);
export const fetchUnitReports = (code: string, unitId: number) =>
  call<Report[]>(`/api/territories/${code}/units/${unitId}/reports`);
export const changeReportStatus = (id: number, status: Report["status"]) =>
  call<Report>(`/api/reports/${id}/status`, json({ status }));
export const fetchLlmStatus = () => call<LlmStatus>("/api/llm/status");
export const exportUrl = (id: number, format: "docx" | "pdf") =>
  `/api/reports/${id}/export.${format}`;
