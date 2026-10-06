import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CitizensView } from "@/components/app/CitizensView";
import { LocaleProvider } from "@/i18n/LocaleProvider";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));
vi.mock("@/components/app/TerritoryMap", () => ({ TerritoryMap: () => null }));

const BANNER = {
  fr: "Contributions fictives — illustration du fonctionnement de l'outil. Elles ne reflètent pas l'opinion réelle des habitants.",
  ar: "مساهمات افتراضية",
};

const dashboard = {
  territory: "rabat",
  taxonomy: {
    label: { fr: "Taxonomie", ar: "تصنيف" },
    themes: [{ code: "voirie", label: { fr: "Voirie et trottoirs", ar: "الطرق" }, indicators: [] }],
    tonalities: { plainte: { fr: "Plainte", ar: "شكاية" } },
  },
  languages: { darija_ar: { fr: "Darija (alphabet arabe)", ar: "الدارجة" } },
  consultations: [{ id: 1, code: "rabat-fictif-v0", title: "x", badge: "fictitious" }],
  fictitious: true,
  banner: BANNER,
  summary: {
    total: 12,
    located: 10,
    analysed_by_ai: 12,
    secondary_included: false,
    secondary_note: null,
    themes: [
      { code: "voirie", label: { fr: "Voirie et trottoirs", ar: "الطرق" }, count: 12, share: null },
    ],
    units: [],
    languages: [["darija_ar", 12]],
    tonalities: [["plainte", 12]],
    rules: { min_contributions: 5, percent_min_total: 20 },
  },
  evaluation: {
    provisional: null,
    reference: null,
    anonymisation: {
      rate: 1,
      masked: 22,
      traps: 22,
      base: { fr: "sur le jeu de test fictif (22 pièges)", ar: "" },
    },
  },
};

const verbatims = {
  voirie: [
    {
      id: "RBT-003",
      original: "الطريق كلها حفاري",
      translation_fr: "La route est pleine de nids-de-poule.",
      translation_note: { fr: "Traduction automatique", ar: "ترجمة آلية" },
      language: "darija_ar",
      language_note: null,
      themes: ["voirie"],
      tonality: "plainte",
      place: null,
      unit: null,
      sure: { language: true, theme: true },
      badge: "fictitious",
    },
  ],
};

function mockApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const body = url.includes("/verbatims")
        ? verbatims
        : url.includes("/citizens")
          ? dashboard
          : url.includes("/auth/me")
            ? { username: "presentateur", display_name: {}, roles: [] }
            : url.includes("/units")
              ? { type: "FeatureCollection", features: [], meta: {} }
              : [];
      return new Response(JSON.stringify(body), { status: 200 });
    }),
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("CitizensView", () => {
  it("always shows the fictitious banner, counts without percentages, original and translation", async () => {
    mockApi();
    render(
      <LocaleProvider>
        <CitizensView code="rabat" />
      </LocaleProvider>,
    );
    expect((await screen.findAllByText(BANNER.fr)).length).toBe(2); // top and bottom
    expect(screen.getByText(/Moins de 20 contributions : nombres seulement/)).toBeTruthy();
    expect(screen.queryByText(/%/, { selector: "li span" })).toBeNull();
    expect(screen.getByText("الطريق كلها حفاري")).toBeTruthy();
    expect(screen.getByText(/Traduction — Traduction automatique/)).toBeTruthy();
    expect(screen.getByText(/sur le jeu de test fictif \(22 pièges\)/)).toBeTruthy();
    expect(screen.getByText("En attente du classement par le professeur.")).toBeTruthy();
    expect(screen.queryByText("Importer des contributions")).toBeNull(); // presenter: no import
  });
});
