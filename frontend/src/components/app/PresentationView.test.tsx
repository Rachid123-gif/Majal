import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PresentationView } from "@/components/app/PresentationView";
import { LocaleProvider } from "@/i18n/LocaleProvider";

const replace = vi.fn();
let search = "territoire=rabat";
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(search),
}));
// The slides are the app's real screens, tested on their own: stubs here.
vi.mock("@/components/app/TerritoryMapView", () => ({ TerritoryMapView: () => <p>slide-map</p> }));
vi.mock("@/components/app/UnitSheetView", () => ({ UnitSheetView: () => <p>slide-sheet</p> }));
vi.mock("@/components/app/CompareView", () => ({ CompareView: () => <p>slide-compare</p> }));
vi.mock("@/components/app/CitizensView", () => ({ CitizensView: () => <p>slide-citizens</p> }));
vi.mock("@/components/app/ReportPanel", () => ({ ReportPanel: () => <p>slide-report</p> }));
vi.mock("@/components/app/DataNeedsView", () => ({ DataNeedsView: () => <p>slide-needs</p> }));
vi.mock("@/components/landing/MoroccoMap", () => ({ MoroccoMap: () => null }));

const scenario = {
  territory: "rabat",
  data_note: { fr: "Données : RGPH 2024 (HCP), OpenStreetMap, GHSL" },
  steps: [
    "home",
    "stakes",
    "map",
    "sheet",
    "compare",
    "citizens",
    "report",
    "data_needs",
    "proposal",
  ],
  map: { indicator: "ENV_VERT" },
  sheet: { unit: 27, name: "Layayda" },
  compare: { units: [27, 18, 21] },
  citizens: { scale: "commune", unit: 26, name: "Salé" },
  report: { unit: 27, name: "Layayda" },
  data_needs: { suggested: ["sante_dr_rsk"] },
  stakes: { sentence: { fr: "Chaque territoire doit produire un diagnostic." } },
  proposal: {
    title: { fr: "Ce que nous vous proposons" },
    items: [{ fr: "Un pilote sur votre territoire" }],
    contact: ["[Nom et titre du professeur]"],
  },
};
const requested: string[] = [];

beforeEach(() => {
  search = "territoire=rabat";
  requested.length = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      requested.push(url);
      const body = url.startsWith("/api/presentation/")
        ? scenario
        : url.includes("/citizens?")
          ? { fictitious: true }
          : url.endsWith("/data-needs")
            ? { institutions: [{ code: "sante_dr_rsk", name: { fr: "Santé", ar: "الصحة" } }] }
            : url === "/api/territories"
              ? []
              : {};
      return new Response(JSON.stringify(body), { status: 200 });
    }),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function renderView() {
  render(
    <LocaleProvider>
      <PresentationView />
    </LocaleProvider>,
  );
}

const current = () => screen.getByText(/^Étape \d sur 9/).textContent;

describe("PresentationView", () => {
  it("navigates with the arrows and the number keys, and keeps the step in the address", async () => {
    renderView();
    expect(await screen.findByText(/Étape 1 sur 9/)).toBeTruthy();
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(current()).toContain("Étape 2 sur 9 — L'enjeu");
    fireEvent.keyDown(window, { key: "PageDown" }); // presenter remotes
    expect(current()).toContain("Étape 3 sur 9 — Carte");
    fireEvent.keyDown(window, { key: "9" });
    expect(current()).toContain("Ce que nous vous proposons");
    fireEvent.keyDown(window, { key: "ArrowLeft" });
    expect(current()).toContain("Étape 8 sur 9");
    expect(replace).toHaveBeenLastCalledWith("/presentation?territoire=rabat&etape=8", {
      scroll: false,
    });
  });

  it("shows « Démonstrateur » always and « Données fictives » on the citizens step only", async () => {
    search = "territoire=rabat&etape=6";
    renderView();
    expect(await screen.findByText("✓ Prêt hors ligne")).toBeTruthy();
    expect(screen.getByText("Démonstrateur")).toBeTruthy();
    expect(screen.getByText(/Données fictives/)).toBeTruthy();
    fireEvent.keyDown(window, { key: "2" });
    expect(screen.queryByText(/Données fictives/)).toBeNull();
    expect(screen.getByText("Chaque territoire doit produire un diagnostic.")).toBeTruthy();
  });

  it("only calls the local server (offline)", async () => {
    renderView();
    await screen.findByText("✓ Prêt hors ligne");
    expect(requested.length).toBeGreaterThan(5);
    expect(requested.every((url) => url.startsWith("/api/"))).toBe(true);
  });
});
