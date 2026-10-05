"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { type FormEvent, useState } from "react";
import { Logo } from "@/components/Logo";
import { LanguageToggle } from "@/components/landing/SiteHeader";
import outline from "@/content/morocco-outline.json";
import { useLocale } from "@/i18n/LocaleProvider";
import { ApiError, login, safeNextPath } from "@/lib/api";

export function LoginView() {
  const { t } = useLocale();
  const router = useRouter();
  const params = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await login(username, password);
      router.replace(safeNextPath(params.get("suite")));
    } catch (exc) {
      const status = exc instanceof ApiError ? exc.status : 0;
      setError(
        t(status === 401 ? "login.invalid" : status === 429 ? "login.locked" : "login.unreachable"),
      );
      setPending(false);
    }
  }

  const [, , w, h] = outline.viewBox;
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <aside className="bg-petrol text-cream relative hidden overflow-hidden p-12 lg:flex lg:flex-col lg:justify-between">
        <Link href="/" aria-label={t("backHome")}>
          <Logo size="sm" tone="light" />
        </Link>
        <svg
          viewBox={`0 0 ${w} ${h}`}
          aria-hidden
          className="pointer-events-none absolute -end-24 top-1/2 h-[80%] -translate-y-1/2 opacity-25"
        >
          <path d={outline.path} fill="none" stroke="currentColor" strokeWidth={1.4} />
        </svg>
        <p className="font-heading relative max-w-md text-5xl leading-tight italic">
          {t("login.motto")}
        </p>
        <p className="text-cream/60 relative text-sm">{t("demoBanner")}</p>
      </aside>

      <main className="flex flex-col px-6 py-8 sm:px-12">
        <div className="flex items-center justify-between">
          <Link href="/" className="text-slate hover:text-petrol text-sm">
            <span aria-hidden className="inline-block rtl:rotate-180">
              ←
            </span>{" "}
            {t("backHome")}
          </Link>
          <LanguageToggle />
        </div>

        <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-12">
          <span className="lg:hidden">
            <Logo size="sm" />
          </span>
          <h1 className="font-heading text-petrol mt-8 text-5xl lg:mt-0">{t("login.title")}</h1>
          <p className="text-slate mt-3">{t("login.intro")}</p>

          <form onSubmit={onSubmit} className="mt-10 space-y-5" noValidate>
            <div>
              <label htmlFor="username" className="text-petrol block text-sm font-medium">
                {t("login.username")}
              </label>
              <input
                id="username"
                name="username"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="border-petrol/20 focus:border-petrol focus:ring-petrol/15 mt-2 w-full rounded-xl border bg-white px-4 py-3 text-lg outline-none focus:ring-4"
              />
            </div>
            <div>
              <label htmlFor="password" className="text-petrol block text-sm font-medium">
                {t("login.password")}
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="border-petrol/20 focus:border-petrol focus:ring-petrol/15 mt-2 w-full rounded-xl border bg-white px-4 py-3 text-lg outline-none focus:ring-4"
              />
            </div>
            {error && (
              <p
                role="alert"
                className="bg-terracotta/10 text-terracotta-dark rounded-xl px-4 py-3 text-sm"
              >
                <span aria-hidden>▲ </span>
                {error}
              </p>
            )}
            <button
              type="submit"
              disabled={pending || !username || !password}
              className="bg-terracotta hover:bg-terracotta-dark w-full rounded-xl px-5 py-3.5 text-lg font-medium text-white transition-colors disabled:opacity-50"
            >
              {pending ? t("login.submitting") : t("login.submit")}
            </button>
          </form>
          <p className="text-slate mt-8 text-sm leading-relaxed">{t("login.hint")}</p>
        </div>
      </main>
    </div>
  );
}
