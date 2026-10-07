import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { LandingPage } from "@/components/landing/LandingPage";
import { LocaleProvider } from "@/i18n/LocaleProvider";

function renderLanding() {
  return render(
    <LocaleProvider>
      <LandingPage />
    </LocaleProvider>,
  );
}

afterEach(() => {
  cleanup();
  document.documentElement.dir = "ltr";
  window.localStorage.clear();
});

describe("LandingPage", () => {
  it("presents MAJAL with its title, login buttons and sections", () => {
    renderLanding();
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Le copilote IA de l'intelligence territoriale",
      }),
    ).toBeInTheDocument();
    const logins = screen.getAllByRole("link", { name: "Se connecter" });
    expect(logins.length).toBeGreaterThanOrEqual(2);
    for (const link of logins) expect(link).toHaveAttribute("href", "/connexion");
    for (const id of ["projet", "fonctionnalites", "territoires", "garanties", "contact"]) {
      expect(document.getElementById(id)).not.toBeNull();
    }
  });

  it("shows each key figure with its source", () => {
    renderLanding();
    const stakes = document.getElementById("projet")!;
    expect(within(stakes).getByLabelText("210")).toBeInTheDocument();
    expect(within(stakes).getByText("milliards de dirhams")).toBeInTheDocument();
    expect(within(stakes).getAllByText(/Conseil des ministres du 9 avril 2026/)).toHaveLength(2);
    expect(within(stakes).getByText(/FNH/)).toBeInTheDocument();
  });

  it("marks features honestly as in development and mockups as illustrations", () => {
    renderLanding();
    expect(screen.getAllByText(/En cours de développement/)).toHaveLength(2);
    expect(screen.getAllByText(/^Disponible/)).toHaveLength(5);
    expect(screen.getAllByText("Maquette d'illustration — aucune donnée réelle")).toHaveLength(7);
  });

  it("keeps the professor placeholders until they are filled in", () => {
    renderLanding();
    expect(screen.getByText("[Nom du professeur]")).toBeInTheDocument();
    expect(screen.getByText("[Photo]")).toBeInTheDocument();
  });

  it("switches entirely to Arabic, right to left", () => {
    renderLanding();
    fireEvent.click(screen.getAllByRole("button", { name: "العربية" })[0]);
    expect(document.documentElement.dir).toBe("rtl");
    expect(
      screen.getByRole("heading", { level: 1, name: "المساعد الذكي للذكاء الترابي" }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "تسجيل الدخول" }).length).toBeGreaterThan(0);
  });
});
