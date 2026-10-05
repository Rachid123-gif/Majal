import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ReportPanel } from "@/components/app/ReportPanel";
import { LocaleProvider } from "@/i18n/LocaleProvider";

function report(overrides: Record<string, unknown>) {
  return {
    id: 7,
    language: "fr",
    provider: "ollama",
    model: "qwen3:8b",
    state: "done",
    status: "brouillon",
    writing_mode: "ai",
    progress: {},
    content: {
      sections: [
        {
          number: 1,
          code: "presentation",
          title: "Présentation du territoire",
          mode: "fallback",
          attempts: 3,
          duration_s: 1,
          paragraphs: [{ text: "Texte de la section.", facts: [] }],
          raw: [],
          issues: [],
          error: null,
          verification: [],
        },
      ],
      verification: { ok: true, issues: [] },
    },
    history: [],
    error: null,
    duration_s: 61,
    created_at: null,
    finished_at: "2026-10-05T18:00:00+00:00",
    cached: true,
    ...overrides,
  };
}

function mockApi(reports: unknown[], roles: string[] = []) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const body = url.includes("/llm/status")
        ? { sovereign_mode: true, provider: "ollama", model: "qwen3:8b", reachable: true }
        : url.includes("/auth/me")
          ? { username: "presentateur", display_name: {}, roles }
          : reports;
      return new Response(JSON.stringify(body), { status: 200 });
    }),
  );
}

function renderPanel() {
  return render(
    <LocaleProvider>
      <ReportPanel code="rabat" unitId={3} />
    </LocaleProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ReportPanel", () => {
  it("shows the report, the AI notice, the fallback sections and the watermark", async () => {
    mockApi([report({})]);
    renderPanel();
    expect(await screen.findByText("Texte de la section.")).toBeTruthy();
    expect(screen.getByText(/Rédigé par l'IA locale \(qwen3:8b\)/)).toBeTruthy();
    expect(screen.getByText("Section rédigée automatiquement sans IA")).toBeTruthy();
    expect(screen.getByText(/Document de travail généré par MAJAL/)).toBeTruthy();
    expect(screen.getByText(/aucune donnée ne quitte cet ordinateur/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Télécharger (PDF)" }).getAttribute("href")).toBe(
      "/api/reports/7/export.pdf",
    );
  });

  it("only the referent can validate, and a blocked report cannot be exported", async () => {
    mockApi([
      report({
        state: "blocked",
        content: { sections: [], verification: { ok: false, issues: ["nombre non tracé : 12"] } },
      }),
    ]);
    renderPanel();
    expect(await screen.findByText(/Publication bloquée/)).toBeTruthy();
    expect(screen.getByText("nombre non tracé : 12")).toBeTruthy();
    expect(screen.queryByRole("link", { name: /Télécharger/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Valider" })).toBeNull();
  });

  it("says when a stored report predates the current data or instructions", async () => {
    mockApi([report({ outdated: true })]);
    renderPanel();
    expect(await screen.findByText(/régénérez-le pour en tenir compte/)).toBeTruthy();
  });

  it("offers validation to the referent", async () => {
    mockApi([report({})], ["referent"]);
    renderPanel();
    expect(await screen.findByRole("button", { name: "Valider" })).toBeTruthy();
  });
});
