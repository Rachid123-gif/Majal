"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useSyncExternalStore } from "react";
import { Logo } from "@/components/Logo";
import { LanguageToggle } from "@/components/landing/SiteHeader";
import { TerritoryCloseUp } from "@/components/landing/MoroccoMap";
import { features } from "@/content/features";
import { useLocale } from "@/i18n/LocaleProvider";
import {
  fetchHealth,
  fetchMe,
  fetchTerritories,
  logout,
  type Health,
  type Me,
  type TerritorySummary,
} from "@/lib/api";

const TERRITORY_KEY = "majal.territory";
const territoryListeners = new Set<() => void>();
let memoryTerritory: string | null = null;

function readTerritory(): string | null {
  try {
    return window.localStorage.getItem(TERRITORY_KEY) ?? memoryTerritory;
  } catch {
    return memoryTerritory;
  }
}

function writeTerritory(code: string) {
  memoryTerritory = code;
  try {
    window.localStorage.setItem(TERRITORY_KEY, code);
  } catch {
    // Not remembered across visits; the choice still applies for this session.
  }
  territoryListeners.forEach((listener) => listener());
}

function useChosenTerritory(): string | null {
  return useSyncExternalStore(
    (listener) => {
      territoryListeners.add(listener);
      return () => territoryListeners.delete(listener);
    },
    readTerritory,
    () => null,
  );
}

type ServerState = { kind: "checking" } | { kind: "unreachable" } | { kind: "ok"; health: Health };

function statusKey(state: ServerState): string {
  if (state.kind !== "ok") return `status.${state.kind}`;
  if (!state.health.config.ok) return "status.configError";
  return state.health.database.ok ? "status.ok" : "status.noDatabase";
}

export function DashboardView() {
  const { locale, t } = useLocale();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [territories, setTerritories] = useState<TerritorySummary[] | null>(null);
  const [server, setServer] = useState<ServerState>({ kind: "checking" });
  const stored = useChosenTerritory();

  useEffect(() => {
    let cancelled = false;
    fetchMe()
      .then((value) => !cancelled && setMe(value))
      .catch(() => !cancelled && router.replace("/connexion?suite=/tableau-de-bord"));
    fetchTerritories()
      .then((value) => !cancelled && setTerritories(value))
      .catch(() => !cancelled && setTerritories(null));
    fetchHealth()
      .then((health) => !cancelled && setServer({ kind: "ok", health }))
      .catch(() => !cancelled && setServer({ kind: "unreachable" }));
    return () => {
      cancelled = true;
    };
  }, [router]);

  const selected =
    territories?.find((territory) => territory.code === stored)?.code ?? territories?.[0]?.code;

  async function onLogout() {
    try {
      await logout();
    } finally {
      router.replace("/");
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-petrol/10 border-b bg-white/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-5 py-4 sm:px-8">
          <Link href="/" aria-label="MAJAL">
            <Logo size="sm" />
          </Link>
          <div className="ms-auto flex items-center gap-3">
            {me && (
              <span className="text-slate hidden text-sm sm:inline">{me.display_name[locale]}</span>
            )}
            <LanguageToggle />
            <button
              type="button"
              onClick={onLogout}
              className="border-petrol/30 text-petrol hover:bg-petrol/5 rounded-full border px-4 py-1.5 text-sm"
            >
              {t("dashboard.logout")}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-12 sm:px-8">
        <p className="text-terracotta text-sm font-semibold">{t("demoBanner")}</p>
        <h1 className="font-heading text-petrol mt-2 text-4xl sm:text-6xl">
          {t("dashboard.greeting")}
          {me ? `, ${me.display_name[locale]}` : ""}
        </h1>

        <section className="mt-12">
          <h2 className="font-heading text-petrol text-3xl">{t("dashboard.chooseTerritory")}</h2>
          {territories ? (
            <div role="radiogroup" className="mt-6 grid gap-5 sm:grid-cols-2">
              {territories.map((territory) => {
                const active = territory.code === selected;
                const scope = territory.scopes.find((s) => s.default);
                const profileKey = `dashboard.profiles.${territory.profiles.indicators}`;
                const profile = t(profileKey);
                return (
                  <button
                    key={territory.code}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    onClick={() => writeTerritory(territory.code)}
                    className={`overflow-hidden rounded-2xl border-2 text-start transition-all ${
                      active
                        ? "border-terracotta shadow-[0_20px_50px_-25px_rgba(168,70,31,0.6)]"
                        : "border-petrol/10 hover:border-petrol/30"
                    }`}
                  >
                    {(territory.code === "rabat" || territory.code === "tetouan") && (
                      <div className="aspect-[3/1] overflow-hidden">
                        <TerritoryCloseUp code={territory.code} name={territory.name[locale]} />
                      </div>
                    )}
                    <div className="bg-white p-6">
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="font-heading text-petrol text-4xl">
                          {territory.name[locale]}
                        </h3>
                        {active && (
                          <span className="bg-terracotta rounded-full px-3 py-1 text-xs font-medium text-white">
                            ✓ {t("dashboard.selected")}
                          </span>
                        )}
                      </div>
                      <p className="text-slate mt-1">{territory.region[locale]}</p>
                      <p className="text-petrol mt-4 text-sm">
                        <span className="text-slate">{t("dashboard.defaultScope")} : </span>
                        {scope?.label[locale]}
                      </p>
                      <p className="text-petrol mt-1 text-sm">
                        <span className="text-slate">{t("dashboard.profile")} : </span>
                        {profile === profileKey ? territory.profiles.indicators : profile}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="text-slate mt-6">{t("dashboard.territoriesUnavailable")}</p>
          )}

          <Link
            href={selected ? `/presentation?territoire=${selected}` : "/presentation"}
            className="bg-petrol text-cream hover:bg-petrol-dark mt-8 flex items-center justify-center gap-3 rounded-2xl px-8 py-6 text-xl font-medium transition-colors sm:text-2xl"
          >
            <svg
              width="26"
              height="26"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              aria-hidden
            >
              <rect x="3" y="4" width="18" height="12" rx="1.5" />
              <path d="M10 8l4 2-4 2V8zM12 16v4M8 20h8" />
            </svg>
            {t("dashboard.launch")}
          </Link>
        </section>

        <section className="mt-16">
          <h2 className="font-heading text-petrol text-3xl">{t("dashboard.progressTitle")}</h2>
          <p className="text-slate mt-2">{t("dashboard.progressIntro")}</p>
          <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const available = feature.status === "available";
              return (
                <li
                  key={feature.id}
                  className={`rounded-2xl border p-5 ${
                    available ? "border-petrol/20 bg-white" : "border-petrol/10 bg-white/50"
                  }`}
                >
                  <p className={`font-medium ${available ? "text-petrol" : "text-petrol/70"}`}>
                    {feature.title[locale]}
                  </p>
                  <p className="mt-3 flex flex-wrap items-center gap-2 text-sm">
                    <span
                      className={`rounded-full px-2.5 py-0.5 ${
                        available ? "bg-petrol text-cream" : "bg-petrol/5 text-slate"
                      }`}
                    >
                      {available ? t("dashboard.available") : t("dashboard.comingSoon")}
                    </span>
                    <span className="text-slate">{feature.stage[locale]}</span>
                  </p>
                </li>
              );
            })}
          </ul>
        </section>
      </main>

      <footer className="border-petrol/10 border-t px-5 py-4 sm:px-8">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2">
          <p role="status" className="text-slate flex items-center gap-2 text-sm">
            <span
              aria-hidden
              className={server.kind === "ok" && server.health.status === "ok" ? "text-petrol" : ""}
            >
              {server.kind === "checking"
                ? "…"
                : server.kind === "ok" && server.health.status === "ok"
                  ? "●"
                  : "▲"}
            </span>
            {t(statusKey(server))}
          </p>
          <p className="text-slate text-sm">
            {t("footer", { version: server.kind === "ok" ? server.health.version : "—" })}
          </p>
        </div>
      </footer>
    </div>
  );
}
