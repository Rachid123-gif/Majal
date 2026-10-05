"use client";

import { useEffect, useState } from "react";
import { Logo } from "@/components/Logo";
import { useLocale } from "@/i18n/LocaleProvider";
import { fetchHealth, fetchTerritories, type Health, type TerritorySummary } from "@/lib/api";

type ServerState =
  { kind: "checking" } | { kind: "unreachable" } | { kind: "reachable"; health: Health };

function statusKey(state: ServerState): string {
  if (state.kind !== "reachable") return `status.${state.kind}`;
  if (!state.health.config.ok) return "status.configError";
  return state.health.database.ok ? "status.ok" : "status.noDatabase";
}

function StatusLine({ state }: { state: ServerState }) {
  const { t } = useLocale();
  const ok = state.kind === "reachable" && state.health.status === "ok";
  const symbol = state.kind === "checking" ? "…" : ok ? "●" : "▲";
  return (
    <p role="status" className="text-slate flex items-center gap-2 text-sm">
      <span aria-hidden className={ok ? "text-petrol" : "text-slate"}>
        {symbol}
      </span>
      {t(statusKey(state))}
    </p>
  );
}

function TerritoryCard({ territory }: { territory: TerritorySummary }) {
  const { locale, t } = useLocale();
  const scope = territory.scopes.find((s) => s.default);
  const profile = territory.profiles.indicators;
  const profileLabel = t(`profiles.${profile}`);
  return (
    <li className="border-petrol/15 rounded-lg border bg-white/70 p-6">
      <h3 className="font-heading text-petrol text-3xl">{territory.name[locale]}</h3>
      <p className="text-slate mt-1">{territory.region[locale]}</p>
      <dl className="mt-4 space-y-1 text-sm">
        {scope && (
          <div className="flex gap-2">
            <dt className="text-slate">{t("defaultScope")} :</dt>
            <dd>{scope.label[locale]}</dd>
          </div>
        )}
        <div className="flex gap-2">
          <dt className="text-slate">{t("profile")} :</dt>
          <dd>{profileLabel.startsWith("profiles.") ? profile : profileLabel}</dd>
        </div>
      </dl>
    </li>
  );
}

export function HomeView() {
  const { locale, setLocale, t } = useLocale();
  const [server, setServer] = useState<ServerState>({ kind: "checking" });
  const [territories, setTerritories] = useState<TerritorySummary[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchHealth(), fetchTerritories()])
      .then(([health, list]) => {
        if (cancelled) return;
        setServer({ kind: "reachable", health });
        setTerritories(list);
      })
      .catch(() => {
        if (!cancelled) setServer({ kind: "unreachable" });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex justify-end px-6 py-4">
        <button
          type="button"
          onClick={() => setLocale(locale === "fr" ? "ar" : "fr")}
          className="border-petrol/30 text-petrol hover:bg-petrol/5 rounded border px-3 py-1 text-sm"
        >
          {t("switchLanguage")}
        </button>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-12 px-6 py-10">
        <section className="flex flex-col gap-6">
          <h1>
            <Logo />
          </h1>
          <p className="font-heading text-petrol text-2xl sm:text-3xl">{t("tagline")}</p>
          <p className="text-slate max-w-2xl text-lg">{t("lead")}</p>
          <div className="flex flex-wrap items-center gap-4">
            <button
              type="button"
              disabled
              title={t("startSoon")}
              className="bg-terracotta rounded px-5 py-3 font-medium text-white disabled:opacity-60"
            >
              {t("start")}
            </button>
            <span className="text-slate text-sm">{t("startSoon")}</span>
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <h2 className="font-heading text-petrol text-2xl">{t("demoTerritories")}</h2>
          {territories ? (
            <ul className="grid gap-4 sm:grid-cols-2">
              {territories.map((territory) => (
                <TerritoryCard key={territory.code} territory={territory} />
              ))}
            </ul>
          ) : (
            <p className="text-slate">{t("territoriesUnavailable")}</p>
          )}
        </section>

        <p className="font-heading text-petrol text-xl italic">{t("principle")}</p>
      </main>

      <footer className="border-petrol/10 flex flex-wrap items-center justify-between gap-2 border-t px-6 py-4">
        <StatusLine state={server} />
        <p className="text-slate text-sm">
          {t("footer", {
            version: server.kind === "reachable" ? server.health.version : "—",
          })}
        </p>
      </footer>
    </div>
  );
}
