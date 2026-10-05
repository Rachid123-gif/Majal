"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Logo } from "@/components/Logo";
import { landing } from "@/content/landing";
import { useLocale } from "@/i18n/LocaleProvider";

export function LanguageToggle({ tone = "light" }: { tone?: "light" | "dark" }) {
  const { locale, setLocale } = useLocale();
  const colors =
    tone === "dark"
      ? "border-cream/40 text-cream hover:bg-cream/10"
      : "border-petrol/30 text-petrol hover:bg-petrol/5";
  return (
    <button
      type="button"
      onClick={() => setLocale(locale === "fr" ? "ar" : "fr")}
      lang={locale === "fr" ? "ar" : "fr"}
      className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${colors}`}
    >
      {locale === "fr" ? "العربية" : "Français"}
    </button>
  );
}

export function SiteHeader() {
  const { locale } = useLocale();
  const t = landing[locale];
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const solid = scrolled || open;
  const links = [
    ["#projet", t.nav.project],
    ["#fonctionnalites", t.nav.features],
    ["#territoires", t.nav.territories],
    ["#garanties", t.nav.guarantees],
  ] as const;

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-[background-color,box-shadow,color] duration-300 ${
        solid
          ? "bg-cream/90 text-petrol shadow-[0_1px_0_rgba(18,52,59,0.08)] backdrop-blur-md"
          : "text-cream bg-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-5 py-4 sm:px-8">
        <Link href="/" aria-label="MAJAL — مجال" className="shrink-0">
          <Logo size="sm" tone={solid ? "dark" : "light"} />
        </Link>

        <nav aria-label={t.menu} className="hidden flex-1 justify-center gap-8 lg:flex">
          {links.map(([href, label]) => (
            <a key={href} href={href} className="nav-link text-[15px] opacity-90 hover:opacity-100">
              {label}
            </a>
          ))}
        </nav>

        <div className="ms-auto flex items-center gap-3 lg:ms-0">
          <span className="hidden sm:inline-flex">
            <LanguageToggle tone={solid ? "light" : "dark"} />
          </span>
          <Link
            href="/connexion"
            className="bg-terracotta hover:bg-terracotta-dark rounded-full px-4 py-2 text-sm font-medium whitespace-nowrap text-white transition-colors"
          >
            {t.login}
          </Link>
          <button
            type="button"
            className="rounded-full p-2 lg:hidden"
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? t.close : t.menu}
            onClick={() => setOpen((v) => !v)}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden>
              {open ? (
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="1.8" />
              ) : (
                <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="1.8" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {open && (
        <nav id="mobile-menu" className="border-petrol/10 border-t px-5 pb-6 lg:hidden">
          <ul className="flex flex-col gap-1 pt-3">
            {links.map(([href, label]) => (
              <li key={href}>
                <a
                  href={href}
                  onClick={() => setOpen(false)}
                  className="hover:bg-petrol/5 block rounded-lg px-3 py-3 text-lg"
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>
          <div className="mt-3 px-3">
            <LanguageToggle />
          </div>
        </nav>
      )}
    </header>
  );
}
