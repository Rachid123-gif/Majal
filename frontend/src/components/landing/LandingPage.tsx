"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { Logo } from "@/components/Logo";
import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { useReducedMotion } from "@/components/motion/useReducedMotion";
import { features } from "@/content/features";
import { landing } from "@/content/landing";
import { isPlaceholder, site } from "@/content/site";
import { useLocale } from "@/i18n/LocaleProvider";
import { FeatureMockup } from "./Mockups";
import { MoroccoMap, TerritoryCloseUp } from "./MoroccoMap";
import { SiteHeader } from "./SiteHeader";

function Eyebrow({ children, light = false }: { children: React.ReactNode; light?: boolean }) {
  return (
    <p
      className={`eyebrow mb-5 text-[13px] font-semibold uppercase ${
        light ? "text-terracotta-light" : "text-terracotta"
      }`}
    >
      {children}
    </p>
  );
}

function Hero() {
  const { locale } = useLocale();
  const t = landing[locale];
  const mapRef = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();

  // Gentle depth: the map drifts slower than the page while scrolling.
  useEffect(() => {
    if (reduced) return;
    let frame = 0;
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        if (mapRef.current) {
          mapRef.current.style.transform = `translate3d(0, ${window.scrollY * 0.18}px, 0)`;
        }
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(frame);
    };
  }, [reduced]);

  return (
    <section className="hero bg-petrol text-cream relative isolate overflow-hidden">
      <div className="hero-glow pointer-events-none absolute inset-0 -z-10" aria-hidden />
      <div className="mx-auto grid min-h-[100svh] max-w-7xl items-center gap-10 px-5 pt-28 pb-16 sm:px-8 lg:grid-cols-[1.1fr_0.9fr] lg:pt-24">
        <div className="hero-copy relative z-10">
          <p className="eyebrow text-terracotta-light mb-6 text-[13px] font-semibold uppercase">
            {t.hero.eyebrow}
          </p>
          <h1 className="font-heading text-[2.9rem] leading-[1.02] font-medium sm:text-7xl lg:text-[5.4rem]">
            {t.hero.title}
          </h1>
          <p className="text-cream/80 mt-7 max-w-xl text-lg leading-relaxed sm:text-xl">
            {t.hero.subtitle}
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <a
              href="#projet"
              className="bg-cream text-petrol hover:bg-white inline-flex items-center gap-2 rounded-full px-6 py-3.5 font-medium transition-colors"
            >
              {t.hero.discover}
              <span aria-hidden className="discover-arrow">
                ↓
              </span>
            </a>
            <Link
              href="/connexion"
              className="border-cream/40 hover:bg-cream/10 rounded-full border px-6 py-3.5 font-medium transition-colors"
            >
              {t.login}
            </Link>
          </div>
        </div>
        <div
          ref={mapRef}
          className="hero-map relative mx-auto w-full max-w-[520px] will-change-transform"
        >
          <MoroccoMap label={t.hero.mapLabel} cities={t.hero.cities} />
        </div>
      </div>
    </section>
  );
}

function Stakes() {
  const { locale } = useLocale();
  const t = landing[locale].stakes;
  return (
    <section id="projet" className="scroll-mt-20 px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto max-w-7xl">
        <Reveal className="max-w-3xl">
          <Eyebrow>{t.eyebrow}</Eyebrow>
          <h2 className="font-heading text-petrol text-4xl leading-tight sm:text-6xl">{t.title}</h2>
          <p className="text-slate mt-6 text-lg leading-relaxed">{t.intro}</p>
        </Reveal>
        <div className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {t.figures.map((figure, index) => (
            <Reveal
              key={figure.unit}
              delay={index * 120}
              className="border-petrol/10 flex flex-col rounded-2xl border bg-white/50 p-8"
            >
              <p className="font-heading text-terracotta text-7xl leading-none sm:text-8xl">
                <CountUp value={figure.value} locale={locale} />
              </p>
              <p className="text-petrol mt-3 text-xl font-medium">{figure.unit}</p>
              <p className="text-slate mt-2 flex-1 leading-relaxed">{figure.detail}</p>
              <p className="text-slate/80 border-petrol/10 mt-6 border-t pt-3 text-xs">
                <span aria-hidden>↗ </span>
                {figure.source}
              </p>
            </Reveal>
          ))}
        </div>
        <p className="text-slate mt-6 text-sm">{t.note}</p>
      </div>
    </section>
  );
}

function BeforeAfter() {
  const { locale } = useLocale();
  const t = landing[locale].problem;
  return (
    <section className="bg-white/60 px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto max-w-7xl">
        <Reveal className="max-w-4xl">
          <Eyebrow>{t.eyebrow}</Eyebrow>
          <h2 className="font-heading text-petrol text-4xl leading-tight sm:text-6xl">{t.title}</h2>
        </Reveal>
        <div className="mt-16 grid gap-6 lg:grid-cols-2">
          <Reveal className="border-petrol/10 rounded-2xl border p-8 sm:p-10">
            <h3 className="text-slate text-sm font-semibold tracking-wider uppercase">
              {t.before.title}
            </h3>
            <ul className="mt-6 space-y-5">
              {t.before.items.map((item) => (
                <li key={item} className="text-slate flex gap-4 text-lg">
                  <span
                    aria-hidden
                    className="bg-slate/10 grid h-7 w-7 shrink-0 place-items-center rounded-full text-sm"
                  >
                    ✕
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </Reveal>
          <Reveal delay={150} className="bg-petrol text-cream rounded-2xl p-8 sm:p-10">
            <h3 className="text-terracotta-light text-sm font-semibold tracking-wider uppercase">
              {t.after.title}
            </h3>
            <ul className="mt-6 space-y-5">
              {t.after.items.map((item) => (
                <li key={item} className="flex gap-4 text-lg">
                  <span
                    aria-hidden
                    className="bg-terracotta-light/20 text-terracotta-light grid h-7 w-7 shrink-0 place-items-center rounded-full text-sm"
                  >
                    ✓
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function Features() {
  const { locale } = useLocale();
  const t = landing[locale].featuresSection;
  return (
    <section id="fonctionnalites" className="scroll-mt-20 px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto max-w-7xl">
        <Reveal className="max-w-3xl">
          <Eyebrow>{t.eyebrow}</Eyebrow>
          <h2 className="font-heading text-petrol text-4xl leading-tight sm:text-6xl">{t.title}</h2>
          <p className="text-slate mt-6 text-lg leading-relaxed">{t.intro}</p>
        </Reveal>
        <ol className="mt-20 space-y-24 lg:space-y-32">
          {features.map((feature, index) => {
            const flip = index % 2 === 1;
            return (
              <li key={feature.id} className="grid items-center gap-10 lg:grid-cols-2 lg:gap-20">
                <Reveal className={flip ? "lg:order-2" : ""}>
                  <p className="font-heading text-terracotta text-2xl">
                    {String(index + 1).padStart(2, "0")}
                  </p>
                  <h3 className="font-heading text-petrol mt-2 text-3xl leading-tight sm:text-5xl">
                    {feature.title[locale]}
                  </h3>
                  <p className="text-slate mt-5 text-lg leading-relaxed">
                    {feature.summary[locale]}
                  </p>
                  <ul className="mt-6 space-y-3">
                    {feature.points[locale].map((point) => (
                      <li key={point} className="text-petrol flex gap-3">
                        <span
                          aria-hidden
                          className="bg-terracotta mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full"
                        />
                        {point}
                      </li>
                    ))}
                  </ul>
                  <p
                    className={`mt-7 inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm ${
                      feature.status === "available"
                        ? "bg-petrol text-cream"
                        : "border-petrol/20 text-petrol border"
                    }`}
                  >
                    <span aria-hidden>{feature.status === "available" ? "●" : "◐"}</span>
                    {feature.status === "available" ? t.available : t.inDevelopment} ·{" "}
                    {feature.stage[locale]}
                  </p>
                </Reveal>
                <Reveal delay={120} className={`feature-visual ${flip ? "lg:order-1" : ""}`}>
                  <figure>
                    <FeatureMockup id={feature.id} locale={locale} />
                    <figcaption className="text-slate mt-3 text-center text-xs">
                      {t.mockup}
                    </figcaption>
                  </figure>
                </Reveal>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}

function Territories() {
  const { locale } = useLocale();
  const t = landing[locale].territories;
  return (
    <section
      id="territoires"
      className="bg-petrol text-cream scroll-mt-20 px-5 py-28 sm:px-8 lg:py-36"
    >
      <div className="mx-auto max-w-7xl">
        <Reveal className="max-w-3xl">
          <Eyebrow light>{t.eyebrow}</Eyebrow>
          <h2 className="font-heading text-4xl leading-tight sm:text-6xl">{t.title}</h2>
          <p className="text-cream/75 mt-6 text-lg leading-relaxed">{t.intro}</p>
        </Reveal>
        <div className="mt-16 grid gap-6 lg:grid-cols-2">
          {t.items.map((item, index) => (
            <Reveal
              key={item.code}
              delay={index * 150}
              className="territory-card bg-cream text-petrol overflow-hidden rounded-2xl"
            >
              <div className="aspect-[16/9] overflow-hidden">
                <TerritoryCloseUp code={item.code} name={item.name} />
              </div>
              <div className="p-8">
                <h3 className="font-heading text-5xl">{item.name}</h3>
                <p className="text-terracotta mt-2 font-medium">{item.kind}</p>
                <p className="text-slate mt-1 text-sm">{item.region}</p>
                <dl className="mt-6 space-y-4">
                  <div>
                    <dt className="text-slate text-xs font-semibold tracking-wider uppercase">
                      {t.unitsLabel}
                    </dt>
                    <dd className="mt-1">{item.units}</dd>
                  </div>
                  <div>
                    <dt className="text-slate text-xs font-semibold tracking-wider uppercase">
                      {t.themesLabel}
                    </dt>
                    <dd className="mt-2 flex flex-wrap gap-2">
                      {item.themes.map((theme) => (
                        <span
                          key={theme}
                          className="border-petrol/15 rounded-full border px-3 py-1 text-sm"
                        >
                          {theme}
                        </span>
                      ))}
                    </dd>
                  </div>
                </dl>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

const STEP_ICONS = [
  // Data: stacked layers
  <path key="d" d="M12 3l9 5-9 5-9-5 9-5zm-9 9l9 5 9-5M3 16l9 5 9-5" />,
  // AI: spark
  <path
    key="a"
    d="M12 2v5M12 17v5M2 12h5M17 12h5M5 5l3.5 3.5M15.5 15.5L19 19M19 5l-3.5 3.5M8.5 15.5L5 19"
  />,
  // Decision: check in a circle
  <path key="c" d="M8 12.5l2.5 2.5L16 9.5M12 21a9 9 0 110-18 9 9 0 010 18z" />,
];

function HowItWorks() {
  const { locale } = useLocale();
  const t = landing[locale].how;
  return (
    <section className="px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto max-w-7xl">
        <Reveal className="max-w-3xl">
          <Eyebrow>{t.eyebrow}</Eyebrow>
          <h2 className="font-heading text-petrol text-4xl leading-tight sm:text-6xl">{t.title}</h2>
        </Reveal>
        <Reveal as="ol" className="how-flow relative mt-16 grid gap-6 lg:grid-cols-3 lg:gap-0">
          {t.steps.map((step, index) => (
            <li
              key={step.title}
              className="how-step relative flex flex-col items-start lg:px-8 lg:first:ps-0"
            >
              <div
                className="how-node bg-petrol text-cream relative z-10 grid h-16 w-16 place-items-center rounded-2xl"
                style={{ animationDelay: `${index * 0.5}s` }}
              >
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden
                >
                  {STEP_ICONS[index]}
                </svg>
              </div>
              {index < t.steps.length - 1 && <span aria-hidden className="how-connector" />}
              <p className="text-terracotta mt-6 text-sm font-semibold">0{index + 1}</p>
              <h3 className="font-heading text-petrol mt-1 text-3xl">{step.title}</h3>
              <p className="text-slate mt-3 max-w-sm text-lg leading-relaxed">{step.text}</p>
            </li>
          ))}
        </Reveal>
        <Reveal className="bg-terracotta mt-20 rounded-2xl px-8 py-12 text-center sm:py-16">
          <p className="font-heading text-cream text-3xl italic sm:text-5xl">{t.motto}</p>
        </Reveal>
      </div>
    </section>
  );
}

const GUARANTEE_ICONS = [
  <path key="1" d="M4 19V5h11l5 5v9H4zm11-14v5h5M8 14h8M8 17h5" />,
  <path key="2" d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6l8-3zm-3.5 9l2.5 2.5 4.5-5" />,
  <path key="3" d="M6 10V8a6 6 0 1112 0v2M5 10h14v11H5V10zm7 4v3" />,
  <path
    key="4"
    d="M12 21s-7-5.5-7-11a7 7 0 1114 0c0 5.5-7 11-7 11zm0-8.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z"
  />,
];

function Guarantees() {
  const { locale } = useLocale();
  const t = landing[locale].guarantees;
  return (
    <section id="garanties" className="bg-white/60 scroll-mt-20 px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto max-w-7xl">
        <Reveal className="max-w-3xl">
          <Eyebrow>{t.eyebrow}</Eyebrow>
          <h2 className="font-heading text-petrol text-4xl leading-tight sm:text-6xl">{t.title}</h2>
        </Reveal>
        <div className="mt-16 grid gap-6 sm:grid-cols-2">
          {t.items.map((item, index) => (
            <Reveal
              key={item.title}
              delay={index * 100}
              className="border-petrol/10 bg-cream rounded-2xl border p-8"
            >
              <svg
                width="34"
                height="34"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-terracotta"
                aria-hidden
              >
                {GUARANTEE_ICONS[index]}
              </svg>
              <h3 className="font-heading text-petrol mt-5 text-3xl">{item.title}</h3>
              <p className="text-slate mt-3 text-lg leading-relaxed">{item.text}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function Project() {
  const { locale } = useLocale();
  const t = landing[locale].project;
  const emailReady = !isPlaceholder(site.contactEmail);
  return (
    <section id="contact" className="scroll-mt-20 px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[1.2fr_1fr]">
        <Reveal>
          <Eyebrow>{t.eyebrow}</Eyebrow>
          <h2 className="font-heading text-petrol text-4xl leading-tight sm:text-6xl">{t.title}</h2>
          <p className="text-slate mt-6 text-lg leading-relaxed">{t.text}</p>
        </Reveal>
        <Reveal delay={150} className="border-petrol/10 rounded-2xl border bg-white/70 p-8 sm:p-10">
          <div className="flex items-center gap-5">
            {site.professorPhoto ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={site.professorPhoto}
                alt={site.professorName}
                className="h-24 w-24 rounded-full object-cover"
              />
            ) : (
              <div className="border-petrol/25 text-slate grid h-24 w-24 shrink-0 place-items-center rounded-full border-2 border-dashed text-sm">
                {t.photo}
              </div>
            )}
            <div>
              <p className="text-terracotta text-sm font-semibold">{t.role}</p>
              <p className="font-heading text-petrol mt-1 text-3xl">{site.professorName}</p>
              <p className="text-slate mt-1">{t.affiliation}</p>
            </div>
          </div>
          {emailReady ? (
            <a
              href={`mailto:${site.contactEmail}`}
              className="bg-petrol text-cream hover:bg-petrol-dark mt-8 inline-flex rounded-full px-6 py-3 font-medium transition-colors"
            >
              {t.contact}
            </a>
          ) : (
            <p className="mt-8 flex flex-wrap items-center gap-3">
              <span className="bg-petrol/40 text-cream inline-flex cursor-not-allowed rounded-full px-6 py-3 font-medium">
                {t.contact}
              </span>
              <span className="text-slate text-sm">
                {t.contactPending} ({site.contactEmail})
              </span>
            </p>
          )}
        </Reveal>
      </div>
    </section>
  );
}

function SiteFooter() {
  const { locale } = useLocale();
  const t = landing[locale].footer;
  return (
    <footer className="bg-petrol-dark text-cream/80 px-5 py-14 sm:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Logo size="sm" tone="light" />
          <p className="mt-3 text-sm">{t.tagline}</p>
        </div>
        <ul className="space-y-1 text-sm lg:text-end">
          <li className="text-terracotta-light font-medium">{t.demo}</li>
          <li>{t.legal}</li>
          <li>{t.map}</li>
          <li>{t.rights}</li>
        </ul>
      </div>
    </footer>
  );
}

export function LandingPage() {
  return (
    <>
      <SiteHeader />
      <main>
        <Hero />
        <Stakes />
        <BeforeAfter />
        <Features />
        <Territories />
        <HowItWorks />
        <Guarantees />
        <Project />
      </main>
      <SiteFooter />
    </>
  );
}
