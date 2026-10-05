import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { HomeView } from "@/components/HomeView";
import { LocaleProvider } from "@/i18n/LocaleProvider";

const health = {
  status: "degraded",
  version: "0.0.1",
  database: { ok: false, postgis: null, pgvector: null, message: "injoignable" },
  config: { ok: true, territories: 2, message: "Configuration valide" },
};

const territories = [
  {
    code: "rabat",
    name: { fr: "Rabat", ar: "الرباط" },
    region: { fr: "Rabat-Salé-Kénitra", ar: "جهة الرباط سلا القنيطرة" },
    study_area: { fr: "Préfecture de Rabat", ar: "عمالة الرباط" },
    profiles: { indicators: "urbain", taxonomy: "urbain" },
    scopes: [
      {
        code: "agglomeration",
        label: { fr: "Agglomération Rabat-Salé-Skhirate-Témara", ar: "تجمع" },
        default: true,
      },
    ],
  },
];

function mockFetch(ok: boolean) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      if (!ok) throw new TypeError("Failed to fetch");
      const body = url.endsWith("/health") ? health : territories;
      return new Response(JSON.stringify(body), { status: 200 });
    }),
  );
}

function renderHome() {
  return render(
    <LocaleProvider>
      <HomeView />
    </LocaleProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  document.documentElement.dir = "ltr";
  window.localStorage.clear();
});

describe("HomeView", () => {
  it("shows the MAJAL identity and the demo territories from the API", async () => {
    mockFetch(true);
    renderHome();
    expect(screen.getByText("MAJAL")).toBeInTheDocument();
    expect(screen.getByText("Copilote d'intelligence territoriale")).toBeInTheDocument();
    expect(await screen.findByText("Rabat")).toBeInTheDocument();
    expect(screen.getByText("Agglomération Rabat-Salé-Skhirate-Témara")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("base de données non disponible");
  });

  it("says plainly when the server cannot be reached", async () => {
    mockFetch(false);
    renderHome();
    expect(await screen.findByText("Serveur non joignable")).toBeInTheDocument();
  });

  it("switches to Arabic with a right-to-left layout", async () => {
    mockFetch(true);
    renderHome();
    await screen.findByText("Rabat");
    fireEvent.click(screen.getByRole("button", { name: "العربية" }));
    expect(screen.getByText("مساعد ذكي في الذكاء الترابي")).toBeInTheDocument();
    expect(screen.getByText("الرباط")).toBeInTheDocument();
    expect(document.documentElement.dir).toBe("rtl");
  });
});
