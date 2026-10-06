"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppHeader } from "@/components/app/AppHeader";
import { CitizenBanner } from "@/components/app/CitizenBanner";
import { CitizenCrossing } from "@/components/app/CitizenCrossing";
import { TerritoryMap } from "@/components/app/TerritoryMap";
import type { Localized } from "@/content/types";
import { useLocale } from "@/i18n/LocaleProvider";
import { fetchMe } from "@/lib/api";
import {
  fetchCitizens,
  fetchImportProgress,
  fetchVerbatims,
  importContributions,
  percent,
  type Dashboard,
  type EvaluationResult,
  type Filters,
  type Verbatim,
} from "@/lib/citizens";
import { NO_DATA, SEQUENTIAL, classOf, quantileBreaks } from "@/lib/diagnostic";
import { formatNumber } from "@/lib/format";
import { fetchUnits, type FacilityCollection, type UnitCollection } from "@/lib/maps";

const EMPTY_FACILITIES: FacilityCollection = {
  type: "FeatureCollection",
  features: [],
  meta: { categories: [], source: null },
} as FacilityCollection;

const RTL_LANGUAGES = new Set(["ar", "darija_ar"]);

function pct(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${Math.round(value * 100)} %`;
}

export function VerbatimCard({
  verbatim,
  themeLabel,
}: {
  verbatim: Verbatim;
  themeLabel?: string;
}) {
  const { locale, t } = useLocale();
  const rtl = RTL_LANGUAGES.has(verbatim.language);
  const sure = verbatim.sure.language && verbatim.sure.theme;
  return (
    <figure className="border-petrol/10 rounded-xl border bg-white p-4 text-sm">
      <div className="text-slate flex flex-wrap items-center gap-2 text-xs">
        {themeLabel && <span className="text-petrol font-medium">{themeLabel}</span>}
        <span>
          {verbatim.unit
            ? (locale === "ar" && verbatim.unit.name_ar) || verbatim.unit.name_fr
            : t("citizens.unknownPlace")}
        </span>
        <span aria-hidden>·</span>
        <span>{sure ? `✓ ${t("citizens.sure")}` : `? ${t("citizens.unsure")}`}</span>
      </div>
      <div className={`mt-3 grid gap-3 ${verbatim.translation_fr ? "md:grid-cols-2" : ""}`}>
        <blockquote>
          <p className="text-slate text-[11px] font-medium uppercase tracking-wide">
            {t("citizens.original")}
          </p>
          <p
            lang={rtl ? "ar" : undefined}
            dir={rtl ? "rtl" : "ltr"}
            className={`text-petrol mt-1 ${rtl ? "font-arabic text-base" : ""}`}
          >
            {verbatim.original}
          </p>
          {verbatim.language_note && (
            <p className="text-terracotta-dark mt-1 text-[11px]">
              {verbatim.language_note[locale]}
            </p>
          )}
        </blockquote>
        {verbatim.translation_fr && (
          <div>
            <p className="text-slate text-[11px] font-medium uppercase tracking-wide">
              {t("citizens.translation")} — {verbatim.translation_note?.[locale]}
            </p>
            <p lang="fr" dir="ltr" className="text-petrol mt-1">
              {verbatim.translation_fr}
            </p>
          </div>
        )}
      </div>
    </figure>
  );
}

function EvaluationBlock({
  title,
  result,
  pending,
}: {
  title: string;
  result: EvaluationResult | null;
  pending?: string;
}) {
  const { locale, t } = useLocale();
  return (
    <div className="border-petrol/10 rounded-xl border bg-white p-4 text-sm">
      <h3 className="text-petrol font-semibold">{title}</h3>
      {!result ? (
        <p className="text-slate mt-2">{pending}</p>
      ) : (
        <>
          <p className="text-slate mt-1 text-xs">
            {t("citizens.base")} {result.base[locale]}
          </p>
          {result.note && (
            <p className="text-terracotta-dark mt-1 text-xs">⚠ {result.note[locale]}</p>
          )}
          <table className="mt-3 w-full text-xs">
            <thead>
              <tr className="text-slate text-start">
                <th className="py-1 text-start font-normal" />
                <th className="py-1 text-start font-normal">{t("citizens.model")}</th>
                <th className="py-1 text-start font-normal">{t("citizens.keywords")}</th>
              </tr>
            </thead>
            <tbody className="text-petrol tabular-nums">
              {result.main_theme?.model && (
                <tr>
                  <td className="py-1">{t("citizens.mainTheme")}</td>
                  <td>{pct(result.main_theme.model.accuracy)}</td>
                  <td>—</td>
                </tr>
              )}
              <tr>
                <td className="py-1">{t("citizens.precision")}</td>
                <td>{pct(result.themes.model.precision)}</td>
                <td>{pct(result.themes.keywords.precision)}</td>
              </tr>
              <tr>
                <td className="py-1">{t("citizens.recall")}</td>
                <td>{pct(result.themes.model.recall)}</td>
                <td>{pct(result.themes.keywords.recall)}</td>
              </tr>
              <tr>
                <td className="py-1">{t("citizens.tonality")}</td>
                <td>{pct(result.tonality.model.accuracy)}</td>
                <td>{pct(result.tonality.keywords.accuracy)}</td>
              </tr>
              {result.language && (
                <tr>
                  <td className="py-1">{t("citizens.language")}</td>
                  <td>{pct(result.language.model.accuracy)}</td>
                  <td>{pct(result.language.keywords.accuracy)}</td>
                </tr>
              )}
            </tbody>
          </table>
          {result.location && (
            <p className="text-slate mt-2 text-xs">
              {t("citizens.location", {
                correct: String(result.location.correct),
                wrong: String(result.location.wrong),
                none: String(result.location.not_located),
                n: String(result.n),
              })}
            </p>
          )}
        </>
      )}
    </div>
  );
}

function ImportPanel({ code, onDone }: { code: string; onDone: () => void }) {
  const { t } = useLocale();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<number | null>(null);

  useEffect(() => {
    if (job === null) return;
    const timer = setInterval(() => {
      fetchImportProgress(job)
        .then((p) => {
          setMessage(t("citizens.importing", { done: String(p.analysed), total: String(p.total) }));
          if (p.analysed >= p.total) {
            setJob(null);
            onDone();
          }
        })
        .catch(() => setJob(null));
    }, 3000);
    return () => clearInterval(timer);
  }, [job, onDone, t]);

  return (
    <div className="border-petrol/10 rounded-xl border bg-white p-4 text-sm">
      <h3 className="text-petrol font-semibold">{t("citizens.import")}</h3>
      <p className="text-slate mt-1 text-xs">{t("citizens.importHint")}</p>
      <input
        type="file"
        accept=".csv,.xlsx"
        aria-label={t("citizens.import")}
        className="mt-3 text-xs"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (!file) return;
          setError(null);
          importContributions(code, file)
            .then((r) => {
              setMessage(t("citizens.imported", { n: String(r.rows) }));
              setJob(r.consultation_id);
            })
            .catch((exc: Error) => setError(exc.message));
        }}
      />
      {message && <p className="text-petrol mt-2 text-xs">{message}</p>}
      {error && (
        <p role="alert" className="text-terracotta-dark mt-2 text-xs">
          {error}
        </p>
      )}
    </div>
  );
}

export function CitizensView({ code }: { code: string }) {
  const { locale, t } = useLocale();
  const [filters, setFilters] = useState<Filters>({});
  const [data, setData] = useState<Dashboard | null>(null);
  const [verbatims, setVerbatims] = useState<Record<string, Verbatim[]>>({});
  const [units, setUnits] = useState<UnitCollection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetchCitizens(code, filters)
      .then((d) => !cancelled && setData(d))
      .catch((exc: Error) => !cancelled && setError(exc.message));
    fetchVerbatims(code, filters)
      .then((v) => !cancelled && setVerbatims(v))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [code, filters, reload]);

  useEffect(() => {
    fetchUnits(code)
      .then(setUnits)
      .catch(() => undefined);
    fetchMe()
      .then((me) => setRoles(me.roles))
      .catch(() => undefined);
  }, [code]);

  const themeLabel = (codeTheme: string): string => {
    const found = data?.taxonomy.themes.find((th) => th.code === codeTheme);
    return found ? found.label[locale] : codeTheme;
  };
  const label = (value: Localized | undefined, fallback: string) =>
    value ? value[locale] : fallback;

  const unitColors = useMemo(() => {
    if (!data) return null;
    const values = data.summary.units.map((u) => u.per_10k ?? 0);
    const breaks = quantileBreaks(values.filter((v) => v > 0));
    const colors: Record<number, string> = {};
    for (const u of data.summary.units) {
      const color =
        !u.count || u.per_10k === null ? NO_DATA : SEQUENTIAL[classOf(u.per_10k, breaks)];
      for (const member of u.members ?? [u.id]) colors[member] = color; // commune: its units
    }
    return colors;
  }, [data]);

  const summary = data?.summary;
  const maxCount = summary ? Math.max(1, ...summary.themes.map((th) => th.count)) : 1;
  const canImport = roles.includes("referent") || roles.includes("admin");
  const select = "border-petrol/20 rounded-lg border bg-white px-3 py-1.5 text-sm";

  return (
    <div className="min-h-screen">
      <AppHeader territory={code} />
      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <Link href={`/territoire/${code}`} className="text-slate hover:text-petrol text-sm">
          <span aria-hidden className="inline-block rtl:rotate-180">
            ←
          </span>{" "}
          {t("citizens.navMap")}
        </Link>
        <h1 className="font-heading text-petrol mt-3 text-5xl">{t("citizens.title")}</h1>
        {data?.banner && (
          <div className="mt-4">
            <CitizenBanner text={data.banner} />
          </div>
        )}
        {error && (
          <p role="alert" className="bg-terracotta/10 text-terracotta-dark mt-6 rounded-xl p-4">
            {error}
          </p>
        )}
        {!data && !error && <p className="text-slate mt-10">{t("map.loading")}</p>}

        {data && summary && (
          <>
            {/* Scale */}
            <div
              className="mt-6 flex flex-wrap items-center gap-2 text-sm"
              role="radiogroup"
              aria-label={t("citizens.scale")}
            >
              <span className="text-slate">{t("citizens.scale")} :</span>
              {(["unit", "commune"] as const).map((value) => (
                <button
                  key={value}
                  type="button"
                  role="radio"
                  aria-checked={(filters.scale ?? "unit") === value}
                  onClick={() => setFilters({ ...filters, scale: value, unit: undefined })}
                  className={`rounded-full px-3 py-1 ${
                    (filters.scale ?? "unit") === value
                      ? "bg-petrol text-cream"
                      : "bg-cream text-petrol"
                  }`}
                >
                  {value === "unit" ? t("citizens.scaleUnit") : t("citizens.scaleCommune")}
                </button>
              ))}
            </div>

            {/* Filters */}
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <select
                aria-label={t("citizens.allThemes")}
                className={select}
                value={filters.theme ?? ""}
                onChange={(e) => setFilters({ ...filters, theme: e.target.value || undefined })}
              >
                <option value="">{t("citizens.allThemes")}</option>
                {data.taxonomy.themes.map((th) => (
                  <option key={th.code} value={th.code}>
                    {th.label[locale]}
                  </option>
                ))}
              </select>
              <select
                aria-label={t("citizens.allUnits")}
                className={select}
                value={filters.unit ?? ""}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    unit: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
              >
                <option value="">{t("citizens.allUnits")}</option>
                {[...summary.units]
                  .sort((a, b) => a.name_fr.localeCompare(b.name_fr))
                  .map((u) => (
                    <option key={u.id} value={u.id}>
                      {(locale === "ar" && u.name_ar) || u.name_fr}
                    </option>
                  ))}
              </select>
              <select
                aria-label={t("citizens.allLanguages")}
                className={select}
                value={filters.language ?? ""}
                onChange={(e) => setFilters({ ...filters, language: e.target.value || undefined })}
              >
                <option value="">{t("citizens.allLanguages")}</option>
                {Object.entries(data.languages).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v[locale]}
                  </option>
                ))}
              </select>
              <select
                aria-label={t("citizens.allTonalities")}
                className={select}
                value={filters.tonality ?? ""}
                onChange={(e) => setFilters({ ...filters, tonality: e.target.value || undefined })}
              >
                <option value="">{t("citizens.allTonalities")}</option>
                {Object.entries(data.taxonomy.tonalities).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v[locale]}
                  </option>
                ))}
              </select>
              <label className="text-petrol flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!filters.secondary}
                  onChange={(e) =>
                    setFilters({ ...filters, secondary: e.target.checked || undefined })
                  }
                />
                {t("citizens.secondary")}
              </label>
            </div>
            {summary.secondary_note && (
              <p className="text-terracotta-dark mt-2 text-xs">
                ⚠ {summary.secondary_note[locale]}
              </p>
            )}

            {/* Key figures */}
            <dl className="mt-6 grid gap-4 sm:grid-cols-3">
              {[
                [t("citizens.total"), summary.total],
                [t("citizens.located"), summary.located],
                [t("citizens.analysed"), summary.analysed_by_ai],
              ].map(([name, value]) => (
                <div key={String(name)} className="border-petrol/10 rounded-xl border bg-white p-4">
                  <dt className="text-slate text-sm">{name}</dt>
                  <dd className="text-petrol mt-1 text-3xl font-semibold tabular-nums">
                    {formatNumber(Number(value), locale, 0)}
                  </dd>
                </div>
              ))}
            </dl>
            {summary.total === 0 && <p className="text-slate mt-6">{t("citizens.noData")}</p>}

            <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
              {/* Themes */}
              <div className="border-petrol/10 rounded-2xl border bg-white p-6">
                <h2 className="font-heading text-petrol text-2xl">{t("citizens.themes")}</h2>
                {summary.total < summary.rules.percent_min_total && (
                  <p className="text-slate mt-1 text-xs">
                    {t("citizens.countsOnly", { n: String(summary.rules.percent_min_total) })}
                  </p>
                )}
                <ul className="mt-4 space-y-2">
                  {summary.themes.map((th) => (
                    <li key={th.code} className="text-sm">
                      <div className="flex justify-between gap-3">
                        <span className="text-petrol">{th.label[locale]}</span>
                        <span className="text-slate tabular-nums">
                          {th.count}
                          {percent(th.share) ? ` · ${percent(th.share)}` : ""}
                        </span>
                      </div>
                      <div className="bg-cream mt-1 h-2 rounded-full">
                        <div
                          className="bg-petrol h-2 rounded-full"
                          style={{ width: `${(th.count / maxCount) * 100}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
                <div className="mt-6 grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <h3 className="text-petrol font-semibold">{t("citizens.languages")}</h3>
                    <ul className="text-slate mt-1 space-y-0.5">
                      {summary.languages.map(([k, n]) => (
                        <li key={k}>
                          {label(data.languages[k], k)} : {n}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-petrol font-semibold">{t("citizens.tonalities")}</h3>
                    <ul className="text-slate mt-1 space-y-0.5">
                      {summary.tonalities.map(([k, n]) => (
                        <li key={k}>
                          {label(data.taxonomy.tonalities[k], k)} : {n}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Map and units */}
              <div className="border-petrol/10 rounded-2xl border bg-white p-6">
                <h2 className="font-heading text-petrol text-2xl">{t("citizens.byUnit")}</h2>
                <p className="text-slate text-xs">{t("citizens.per10k")}</p>
                <div className="relative mt-3 h-72 overflow-hidden rounded-xl">
                  {units && (
                    <TerritoryMap
                      key={`${code}-${locale}-citizens`}
                      code={code}
                      locale={locale}
                      units={units}
                      facilities={EMPTY_FACILITIES}
                      visibleCategories={[]}
                      colors={{}}
                      unitColors={unitColors}
                      selectedId={filters.scale === "commune" ? null : (filters.unit ?? null)}
                      onHover={() => undefined}
                      onSelect={(id) => {
                        const row = summary.units.find(
                          (u) => id !== null && u.members.includes(id),
                        );
                        setFilters({ ...filters, unit: row?.id ?? undefined });
                      }}
                    />
                  )}
                </div>
                <table className="mt-4 w-full text-xs">
                  <tbody>
                    {summary.units
                      .filter((u) => u.count > 0)
                      .slice(0, 12)
                      .map((u) => (
                        <tr key={u.id} className="border-petrol/10 border-b last:border-0">
                          <td className="text-petrol py-1.5">
                            {(locale === "ar" && u.name_ar) || u.name_fr}
                          </td>
                          <td className="text-slate tabular-nums">
                            {t("citizens.count", { n: String(u.count) })}
                          </td>
                          <td className="text-slate tabular-nums">
                            {u.per_10k !== null ? formatNumber(u.per_10k, locale, 1) : "—"}
                          </td>
                          <td className="text-slate">
                            {u.main_theme ? themeLabel(u.main_theme) : t("citizens.tooFew")}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </section>

            {/* Crossing (one unit) */}
            <section className="border-petrol/10 mt-10 rounded-2xl border bg-white p-6">
              {filters.unit !== undefined ? (
                <CitizenCrossing
                  code={code}
                  unitId={filters.unit}
                  scale={filters.scale ?? "unit"}
                />
              ) : (
                <>
                  <h2 className="font-heading text-petrol text-2xl">{t("citizens.crossing")}</h2>
                  <p className="text-slate mt-2 text-sm">{t("citizens.chooseUnit")}</p>
                </>
              )}
            </section>

            {/* Verbatims */}
            <section className="mt-10">
              <h2 className="font-heading text-petrol text-3xl">{t("citizens.verbatims")}</h2>
              <div className="mt-4 space-y-8">
                {summary.themes.slice(0, 6).map((th) =>
                  verbatims[th.code]?.length ? (
                    <div key={th.code}>
                      <h3 className="text-petrol font-semibold">{th.label[locale]}</h3>
                      <div className="mt-2 grid gap-3">
                        {verbatims[th.code].map((v) => (
                          <VerbatimCard key={v.id} verbatim={v} />
                        ))}
                      </div>
                    </div>
                  ) : null,
                )}
              </div>
            </section>

            {/* Reliability */}
            <section className="mt-10">
              <h2 className="font-heading text-petrol text-3xl">{t("citizens.evaluation")}</h2>
              <p className="text-slate mt-2 text-sm">{t("citizens.tonalityMethod")}</p>
              {data.evaluation.anonymisation && (
                <p className="text-petrol mt-2 text-sm">
                  {t("citizens.anonymisation", { rate: pct(data.evaluation.anonymisation.rate) })}{" "}
                  <span className="text-slate">{data.evaluation.anonymisation.base[locale]}</span>
                </p>
              )}
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <EvaluationBlock
                  title={t("citizens.provisional")}
                  result={data.evaluation.provisional}
                />
                <EvaluationBlock
                  title={data.evaluation.reference?.title?.[locale] ?? t("citizens.reference")}
                  result={data.evaluation.reference}
                  pending={t("citizens.referencePending")}
                />
              </div>
            </section>

            {canImport && (
              <section className="mt-10 max-w-xl">
                <ImportPanel code={code} onDone={() => setReload((n) => n + 1)} />
              </section>
            )}
            {data.banner && (
              <div className="mt-10">
                <CitizenBanner text={data.banner} compact />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
