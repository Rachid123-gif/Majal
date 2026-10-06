import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ReviewView } from "@/components/app/ReviewView";
import { LocaleProvider } from "@/i18n/LocaleProvider";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));

const item = {
  id: 60,
  external_id: "RBT-060",
  original: "البالوعات مفتوحة",
  translation_fr: "Les bouches d'égout sont ouvertes.",
  translation_note: { fr: "Traduction automatique", ar: "ترجمة آلية" },
  language: "darija_ar",
  language_note: null,
  reasons: [
    {
      code: "theme",
      label: { fr: "L'IA et les mots-clés ne donnent pas le même thème principal", ar: "" },
    },
  ],
  proposal: { themes: ["securite"], tonality: "plainte", unit: null, place: null },
  keywords: { themes: ["eau_assainissement"], tonality: "plainte" },
  current: { themes: ["securite"], tonality: "plainte", unit: null },
  validated_by: null,
  validated_at: null,
  badge: "fictitious",
};
const queue = {
  status: "pending",
  fictitious: true,
  banner: { fr: "Contributions fictives — illustration", ar: "" },
  counts: { pending: 1, validated: 0 },
  themes: [
    { code: "securite", label: { fr: "Sécurité", ar: "" } },
    { code: "eau_assainissement", label: { fr: "Eau et assainissement", ar: "" } },
  ],
  tonalities: { plainte: { fr: "Plainte", ar: "" }, proposition: { fr: "Proposition", ar: "" } },
  units: [{ id: 27, name_fr: "Layayda", name_ar: null }],
  items: [item],
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ReviewView", () => {
  it("shows original, translation and proposals, and records a correction signed by the account", async () => {
    const posted: unknown[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (init?.method === "POST") {
          posted.push(JSON.parse(String(init.body)));
          return new Response(
            JSON.stringify({ ...item, validated_by: "professeur", validated_at: "2026-10-06" }),
            { status: 200 },
          );
        }
        const body = url.includes("/review")
          ? queue
          : url.includes("/auth/me")
            ? { username: "professeur", display_name: {}, roles: ["referent"] }
            : [];
        return new Response(JSON.stringify(body), {
          status: 200,
        });
      }),
    );
    render(
      <LocaleProvider>
        <ReviewView code="rabat" />
      </LocaleProvider>,
    );
    expect(await screen.findByText("البالوعات مفتوحة")).toBeTruthy();
    expect(screen.getByText(/Traduction — Traduction automatique/)).toBeTruthy();
    expect(screen.getByText(/Mots-clés : Eau et assainissement/)).toBeTruthy();
    expect(screen.getByText("Contributions fictives — illustration")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Thème principal"), {
      target: { value: "eau_assainissement" },
    });
    fireEvent.change(screen.getByLabelText("Lieu (unité)"), { target: { value: "27" } });
    fireEvent.click(screen.getByText("Enregistrer la correction"));
    expect(await screen.findByText(/Enregistré — validé par professeur/)).toBeTruthy();
    expect(posted).toEqual([
      { themes: ["eau_assainissement"], tonality: "plainte", territory_id: 27 },
    ]);
    expect(screen.getByText("Déjà validées (1)")).toBeTruthy();
  });
});
