"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Logo } from "@/components/Logo";
import { MoroccoMap } from "@/components/landing/MoroccoMap";
import { landing } from "@/content/landing";
import { useLocale } from "@/i18n/LocaleProvider";
import { fetchTerritories, type TerritorySummary } from "@/lib/api";

/** Placeholder for the presentation mode (delivered at stage 7). */
export function PresentationView() {
  const { locale, setLocale, t } = useLocale();
  const router = useRouter();
  const code = useSearchParams().get("territoire");
  const [territory, setTerritory] = useState<TerritorySummary | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchTerritories()
      .then((list) => {
        if (!cancelled) setTerritory(list.find((item) => item.code === code) ?? list[0] ?? null);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [code]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !document.fullscreenElement) router.push("/tableau-de-bord");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [router]);

  function toggleFullscreen() {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void document.documentElement.requestFullscreen?.();
  }

  return (
    <div className="bg-petrol text-cream flex min-h-screen flex-col">
      <div className="flex items-center justify-between gap-4 px-6 py-4 text-sm">
        <span className="text-cream/70">
          {territory ? territory.name[locale] : ""} · {t("demoBanner")}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setLocale(locale === "fr" ? "ar" : "fr")}
            className="border-cream/30 hover:bg-cream/10 rounded-full border px-3 py-1"
          >
            {t("switchLanguage")}
          </button>
          <button
            type="button"
            onClick={toggleFullscreen}
            className="border-cream/30 hover:bg-cream/10 rounded-full border px-3 py-1"
          >
            {t("presentation.fullscreen")}
          </button>
          <button
            type="button"
            onClick={() => router.push("/tableau-de-bord")}
            className="bg-cream text-petrol rounded-full px-3 py-1"
          >
            {t("presentation.exit")}
          </button>
        </div>
      </div>
      <main className="mx-auto grid w-full max-w-6xl flex-1 items-center gap-10 px-6 pb-16 lg:grid-cols-2">
        <div>
          <Logo size="lg" tone="light" />
          <p className="text-terracotta-light mt-10 text-sm font-semibold uppercase">
            {t("presentation.territory")}
          </p>
          <h1 className="font-heading mt-2 text-6xl sm:text-8xl">
            {territory ? territory.name[locale] : "…"}
          </h1>
          {territory && <p className="text-cream/70 mt-3 text-xl">{territory.region[locale]}</p>}
          <p className="border-cream/20 text-cream/85 mt-10 max-w-lg rounded-2xl border p-6 text-lg">
            <span className="bg-terracotta-light/20 text-terracotta-light me-2 rounded-full px-2.5 py-0.5 text-sm">
              {t("dashboard.comingSoon")}
            </span>
            {t("presentation.soon")}
          </p>
        </div>
        <div className="mx-auto w-full max-w-md">
          <MoroccoMap label={landing[locale].hero.mapLabel} cities={landing[locale].hero.cities} />
        </div>
      </main>
    </div>
  );
}
