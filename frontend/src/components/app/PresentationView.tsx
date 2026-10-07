"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { CitizensView } from "@/components/app/CitizensView";
import { CompareView } from "@/components/app/CompareView";
import { DataNeedsView } from "@/components/app/DataNeedsView";
import { EmbeddedContext } from "@/components/app/Embedded";
import { ReportPanel } from "@/components/app/ReportPanel";
import { TerritoryMapView } from "@/components/app/TerritoryMapView";
import { UnitSheetView } from "@/components/app/UnitSheetView";
import { MoroccoMap } from "@/components/landing/MoroccoMap";
import { Logo } from "@/components/Logo";
import { landing } from "@/content/landing";
import { useLocale } from "@/i18n/LocaleProvider";
import { fetchTerritories, type TerritorySummary } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import {
  CITIZEN_STEPS,
  fetchScenario,
  preload,
  text,
  type Preload,
  type Scenario,
  type StepCode,
} from "@/lib/presentation";

const NEXT_KEYS = new Set(["ArrowRight", "PageDown"]);
const PREVIOUS_KEYS = new Set(["ArrowLeft", "PageUp"]);

/** Keys typed in a field (indicator selector, checkbox…) are left to the field. */
function inField(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return target.isContentEditable || ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName);
}

function SlideFrame({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mx-auto max-w-6xl px-8 py-10">
      <h1 className="font-heading text-petrol text-6xl">{title}</h1>
      <div className="mt-8">{children}</div>
    </div>
  );
}

/**
 * Presentation mode (BRIEF §8, §9.9): the demonstration scenario in full screen, step by step,
 * from config/presentation/<territory>.yaml. The slides are the app's real screens, shown
 * without their header (EmbeddedContext), all mounted at launch so that their data is loaded
 * before the demonstration starts (offline). Keyboard: ← → (and presenter remotes), 1 to 9,
 * F for full screen, Escape to leave.
 */
export function PresentationView() {
  const { locale, t } = useLocale();
  const router = useRouter();
  const params = useSearchParams();
  const code = params.get("territoire") ?? "rabat";
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [territory, setTerritory] = useState<TerritorySummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<Preload | null>(null);
  const [index, setIndex] = useState(() => Math.max(0, Number(params.get("etape") ?? 1) - 1));

  useEffect(() => {
    let cancelled = false;
    fetchTerritories()
      .then((list) => !cancelled && setTerritory(list.find((i) => i.code === code) ?? null))
      .catch(() => undefined);
    fetchScenario(code)
      .then((value) => {
        if (cancelled) return;
        setScenario(value);
        void preload(value).then((result) => !cancelled && setStatus(result));
      })
      .catch((exc: Error) => !cancelled && setError(exc.message));
    return () => {
      cancelled = true;
    };
  }, [code]);

  // Larger type for a room: every size of the app is in rem.
  useEffect(() => {
    const root = document.documentElement;
    const previous = root.style.fontSize;
    root.style.fontSize = "112.5%";
    return () => {
      root.style.fontSize = previous;
    };
  }, []);

  const steps = scenario?.steps ?? [];
  const go = useCallback(
    (next: number) => {
      if (!steps.length) return;
      const bounded = Math.min(Math.max(next, 0), steps.length - 1);
      setIndex(bounded);
      router.replace(`/presentation?territoire=${code}&etape=${bounded + 1}`, { scroll: false });
    },
    [code, router, steps.length],
  );

  // A slide shown after being hidden: maps must measure their new size.
  useEffect(() => {
    const timer = window.setTimeout(() => window.dispatchEvent(new Event("resize")), 60);
    return () => window.clearTimeout(timer);
  }, [index]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (inField(event.target)) return;
      let handled = true;
      if (NEXT_KEYS.has(event.key)) go(index + 1);
      else if (PREVIOUS_KEYS.has(event.key)) go(index - 1);
      else if (event.key === "Home") go(0);
      else if (event.key === "End") go(steps.length - 1);
      else if (/^[1-9]$/.test(event.key)) go(Number(event.key) - 1);
      else if (event.key === "f" || event.key === "F") toggleFullscreen();
      else if (event.key === "Escape" && !document.fullscreenElement)
        router.push("/tableau-de-bord");
      else handled = false;
      if (handled) {
        // Capture phase: the map must not also pan with the arrows.
        event.preventDefault();
        event.stopPropagation();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [go, index, router, steps.length]);

  function toggleFullscreen() {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void document.documentElement.requestFullscreen?.();
  }

  const step = steps[index];
  const fictitious = Boolean(status?.fictitious && step && CITIZEN_STEPS.includes(step));
  const hero = landing[locale].hero;
  const stakes = landing[locale].stakes;

  function slide(stepCode: StepCode): ReactNode {
    if (!scenario) return null;
    switch (stepCode) {
      case "home":
        return (
          <div className="bg-petrol text-cream flex min-h-full items-center">
            <div className="mx-auto grid w-full max-w-6xl items-center gap-10 px-8 py-12 lg:grid-cols-2">
              <div>
                <Logo size="lg" tone="light" />
                <h1 className="font-heading mt-10 text-6xl leading-tight">{hero.title}</h1>
                <p className="text-cream/80 mt-6 text-2xl">{hero.subtitle}</p>
                <p className="text-terracotta-light mt-10 text-sm font-semibold uppercase">
                  {t("presentation.territory")}
                </p>
                <p className="font-heading mt-1 text-5xl">{territory?.name[locale] ?? code}</p>
                {territory && <p className="text-cream/70 mt-1">{territory.region[locale]}</p>}
                <button
                  type="button"
                  onClick={() => go(1)}
                  className="bg-cream text-petrol mt-10 rounded-full px-6 py-3 text-lg font-medium"
                >
                  {t("presentation.start")} →
                </button>
              </div>
              <div className="mx-auto w-full max-w-md">
                <MoroccoMap label={hero.mapLabel} cities={hero.cities} />
              </div>
            </div>
          </div>
        );
      case "stakes":
        return (
          <SlideFrame title={stakes.title}>
            <ul className="grid gap-6 md:grid-cols-3">
              {stakes.figures.slice(0, 3).map((figure) => (
                <li key={figure.unit} className="border-petrol/10 rounded-2xl border bg-white p-6">
                  <p className="text-petrol font-heading text-6xl tabular-nums">
                    {formatNumber(figure.value, locale, 0)}
                  </p>
                  <p className="text-petrol mt-1 text-xl font-medium">{figure.unit}</p>
                  <p className="text-slate mt-2">{figure.detail}</p>
                  <p className="text-slate mt-4 text-xs">
                    {t("presentation.source")} : {figure.source}
                  </p>
                </li>
              ))}
            </ul>
            <p className="font-heading text-petrol mt-12 max-w-4xl text-4xl leading-snug">
              {text(scenario.stakes.sentence, locale)}
            </p>
          </SlideFrame>
        );
      case "map":
        return <TerritoryMapView code={code} initialIndicator={scenario.map.indicator} />;
      case "sheet":
        return <UnitSheetView code={code} unitId={scenario.sheet.unit} />;
      case "compare":
        return <CompareView code={code} initialIds={scenario.compare.units} />;
      case "citizens":
        return (
          <CitizensView
            code={code}
            initialFilters={{ scale: scenario.citizens.scale }}
            initialCrossing={{ unit: scenario.citizens.unit, scale: scenario.citizens.scale }}
          />
        );
      case "report":
        return (
          <SlideFrame title={`${t("presentation.step_report")} — ${scenario.report.name}`}>
            <p className="text-slate">{t("presentation.reportHint")}</p>
            <ReportPanel code={code} unitId={scenario.report.unit} />
          </SlideFrame>
        );
      case "data_needs":
        return (
          <div>
            {status?.suggested.length ? (
              <p className="bg-cream text-petrol mx-auto mt-6 max-w-6xl rounded-xl px-8 py-3 text-sm">
                {t("presentation.suggested", {
                  names: status.suggested.map((name) => name[locale]).join(" → "),
                })}
              </p>
            ) : null}
            <DataNeedsView code={code} />
          </div>
        );
      case "proposal":
        return (
          <SlideFrame title={text(scenario.proposal.title, locale)}>
            <ol className="grid gap-6 md:grid-cols-3">
              {scenario.proposal.items.map((item, i) => (
                <li key={i} className="border-petrol/10 rounded-2xl border bg-white p-6">
                  <span className="bg-terracotta text-cream inline-flex h-10 w-10 items-center justify-center rounded-full text-lg font-semibold">
                    {i + 1}
                  </span>
                  <p className="text-petrol mt-4 text-2xl leading-snug">{text(item, locale)}</p>
                </li>
              ))}
            </ol>
            <div className="border-petrol/10 mt-12 rounded-2xl border bg-white p-6">
              <p className="text-terracotta text-sm font-semibold uppercase">
                {t("presentation.contact")}
              </p>
              {scenario.proposal.contact.map((line) => (
                <p key={line} className="text-petrol mt-1 text-xl">
                  {line}
                </p>
              ))}
            </div>
          </SlideFrame>
        );
    }
  }

  return (
    <EmbeddedContext.Provider value={true}>
      <div className="bg-cream flex h-screen flex-col">
        <header className="bg-petrol text-cream flex flex-wrap items-center gap-3 px-5 py-2 text-sm">
          <Logo size="sm" tone="light" />
          <span className="font-medium">{territory?.name[locale] ?? code}</span>
          {scenario && <span className="text-cream/70">· {text(scenario.data_note, locale)}</span>}
          <span className="border-cream/40 rounded-full border px-2 py-0.5 text-xs">
            {t("presentation.demonstrator")}
          </span>
          {fictitious && (
            <span className="bg-terracotta-light text-petrol rounded-full px-2 py-0.5 text-xs font-semibold">
              ◆ {t("presentation.fictitious")}
            </span>
          )}
          <span className="text-cream/70 ms-auto text-xs" aria-live="polite">
            {status
              ? status.ready
                ? `✓ ${t("presentation.ready")}`
                : `⚠ ${t("presentation.notReady")}`
              : t("presentation.loading")}
          </span>
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
        </header>

        <main className="relative flex-1 overflow-hidden">
          {error && (
            <p role="alert" className="bg-terracotta/10 text-terracotta-dark m-8 rounded-xl p-4">
              {error}
            </p>
          )}
          {steps.map((stepCode, i) => (
            <section
              key={stepCode}
              aria-hidden={i !== index}
              aria-label={t(`presentation.step_${stepCode}`)}
              className={`absolute inset-0 overflow-auto ${i === index ? "z-10" : "pointer-events-none invisible opacity-0"}`}
            >
              {slide(stepCode)}
            </section>
          ))}
        </main>

        <nav
          aria-label={t("presentation.title")}
          className="border-petrol/10 flex items-center gap-4 border-t bg-white px-5 py-2 text-sm"
        >
          <button
            type="button"
            onClick={() => go(index - 1)}
            disabled={index === 0}
            aria-label={t("presentation.previous")}
            className="text-petrol rounded-full px-3 py-1 text-lg disabled:opacity-30"
          >
            <span aria-hidden className="inline-block rtl:rotate-180">
              ←
            </span>
          </button>
          <ol className="flex items-center gap-1.5">
            {steps.map((stepCode, i) => (
              <li key={stepCode}>
                <button
                  type="button"
                  onClick={() => go(i)}
                  aria-current={i === index ? "step" : undefined}
                  title={`${i + 1}. ${t(`presentation.step_${stepCode}`)}`}
                  className={`h-2.5 rounded-full transition-all ${
                    i === index ? "bg-terracotta w-8" : "bg-petrol/25 w-2.5"
                  }`}
                >
                  <span className="sr-only">{t(`presentation.step_${stepCode}`)}</span>
                </button>
              </li>
            ))}
          </ol>
          {step && (
            <span className="text-petrol font-medium">
              {t("presentation.stepOf", { n: String(index + 1), total: String(steps.length) })} —{" "}
              {t(`presentation.step_${step}`)}
            </span>
          )}
          <span className="text-slate ms-auto hidden text-xs lg:inline">
            {t("presentation.keys")}
          </span>
          <button
            type="button"
            onClick={() => go(index + 1)}
            disabled={index >= steps.length - 1}
            aria-label={t("presentation.next")}
            className="text-petrol rounded-full px-3 py-1 text-lg disabled:opacity-30"
          >
            <span aria-hidden className="inline-block rtl:rotate-180">
              →
            </span>
          </button>
        </nav>
      </div>
    </EmbeddedContext.Provider>
  );
}
