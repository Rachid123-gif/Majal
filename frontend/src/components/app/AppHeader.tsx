"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useEmbedded } from "@/components/app/Embedded";
import { Logo } from "@/components/Logo";
import { LanguageToggle } from "@/components/landing/SiteHeader";
import { useLocale } from "@/i18n/LocaleProvider";
import { fetchMe, fetchTerritories, logout, type Me, type TerritorySummary } from "@/lib/api";

/** Header of the logged-in app: logo, territory selector, user, language, logout. */
export function AppHeader({ territory }: { territory?: string }) {
  // In the presentation mode the slides have no app header.
  return useEmbedded() ? null : <Header territory={territory} />;
}

function Header({ territory }: { territory?: string }) {
  const { locale, t } = useLocale();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [territories, setTerritories] = useState<TerritorySummary[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetchMe()
      .then((value) => !cancelled && setMe(value))
      .catch(() => !cancelled && router.replace("/connexion"));
    fetchTerritories()
      .then((value) => !cancelled && setTerritories(value))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function onLogout() {
    try {
      await logout();
    } finally {
      router.replace("/");
    }
  }

  return (
    <header className="border-petrol/10 relative z-20 border-b bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-5 gap-y-2 px-5 py-3 sm:px-6">
        <Link href="/tableau-de-bord" aria-label={t("app.dashboard")}>
          <Logo size="sm" />
        </Link>
        {territory && territories.length > 0 && (
          <nav aria-label={t("app.territory")} className="bg-cream flex rounded-full p-1">
            {territories.map((item) => {
              const active = item.code === territory;
              return (
                <Link
                  key={item.code}
                  href={`/territoire/${item.code}`}
                  aria-current={active ? "page" : undefined}
                  className={`rounded-full px-4 py-1.5 text-sm transition-colors ${
                    active ? "bg-petrol text-cream" : "text-petrol hover:bg-petrol/5"
                  }`}
                >
                  {item.name[locale]}
                </Link>
              );
            })}
          </nav>
        )}
        {territory && (
          <nav aria-label={t("citizens.nav")} className="flex gap-4 text-sm">
            <Link href={`/territoire/${territory}`} className="text-petrol hover:underline">
              {t("citizens.navMap")}
            </Link>
            <Link
              href={`/territoire/${territory}/citoyens`}
              className="text-petrol hover:underline"
            >
              {t("citizens.nav")}
            </Link>
            <Link
              href={`/territoire/${territory}/besoins-donnees`}
              className="text-petrol hover:underline"
            >
              {t("dataNeeds.nav")}
            </Link>
          </nav>
        )}
        <div className="ms-auto flex items-center gap-3">
          <Link
            href="/tableau-de-bord"
            className="text-slate hover:text-petrol hidden text-sm md:inline"
          >
            {t("app.dashboard")}
          </Link>
          {me && (
            <span className="text-slate hidden text-sm lg:inline">{me.display_name[locale]}</span>
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
  );
}
