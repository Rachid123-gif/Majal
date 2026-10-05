"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppHeader } from "@/components/app/AppHeader";
import { ConfidenceBadge } from "@/components/app/ConfidenceBadge";
import { GridBanner } from "@/components/app/GridBanner";
import { ReportPanel } from "@/components/app/ReportPanel";
import { StatusChip } from "@/components/app/StatusChip";
import { useLocale } from "@/i18n/LocaleProvider";
import {
  attentionPoints,
  fetchDiagnostic,
  formatValue,
  unitName,
  type DiagnosticData,
  type DiagnosticUnit,
  type IndicatorMeta,
  type IndicatorValue,
} from "@/lib/diagnostic";
import { formatNumber } from "@/lib/format";
import {
  fetchFacilities,
  fetchUnits,
  type FacilityCollection,
  type UnitCollection,
} from "@/lib/maps";

type Loaded = { diag: DiagnosticData; units: UnitCollection; facilities: FacilityCollection };

function useT() {
  const { locale, t } = useLocale();
  return { locale, t };
}

function RankLine({ value, neutral }: { value: IndicatorValue; neutral: boolean }) {
  const { t } = useT();
  if (value.excluded_from_ranking) return <span>{t("diag.excluded")}</span>;
  if (!value.rank || !value.rank_of) return null;
  const of = String(value.rank_of);
  const rank = String(value.rank);
  // Context indicators are not judged: the rank only orders values from the highest.
  if (neutral) {
    return (
      <span>
        {value.rank === 1 ? t("diag.rankValueFirst", { of }) : t("diag.rankValue", { rank, of })}
      </span>
    );
  }
  return (
    <span>{value.rank === 1 ? t("diag.rankFirst", { of }) : t("diag.rank", { rank, of })}</span>
  );
}

function GapLine({ value, data }: { value: IndicatorValue; data: DiagnosticData }) {
  const { locale, t } = useT();
  if (value.gap_pct === undefined || value.gap_pct === null) return null;
  const gap = formatNumber(Math.abs(value.gap_pct), locale, 0);
  const ref = data.evaluation.reference_label[locale];
  return (
    <span>
      {value.gap_pct >= 0 ? t("diag.gapAbove", { gap, ref }) : t("diag.gapBelow", { gap, ref })}
    </span>
  );
}

function IndicatorCard({
  meta,
  value,
  data,
}: {
  meta: IndicatorMeta;
  value: IndicatorValue;
  data: DiagnosticData;
}) {
  const { locale, t } = useT();
  const [open, setOpen] = useState(false);
  const available = value.value !== null;
  const trend =
    available && (meta.formula === "cagr" || meta.formula === "change")
      ? value.value! > 0
        ? { symbol: "↗", label: t("diag.trendUp") }
        : { symbol: "↘", label: t("diag.trendDown") }
      : null;
  return (
    <article
      className={`flex flex-col rounded-2xl border bg-white p-5 ${
        meta.highlight
          ? "border-terracotta/50 shadow-[0_10px_30px_-20px_rgba(168,70,31,0.6)]"
          : "border-petrol/10"
      }`}
    >
      <h4 className="text-petrol text-sm font-medium leading-snug">{meta.label[locale]}</h4>
      {available ? (
        <p className="font-heading text-petrol mt-3 text-4xl leading-none">
          {formatValue(value.value, meta, locale)}
          <span className="text-slate ms-1.5 font-sans text-sm">{meta.unit[locale]}</span>
          {trend && (
            <span className="text-slate ms-2 align-middle font-sans text-base" title={trend.label}>
              <span aria-hidden>{trend.symbol}</span>
              <span className="sr-only">{trend.label}</span>
            </span>
          )}
        </p>
      ) : (
        <p className="text-slate mt-3 text-lg">{data.evaluation.statuses[value.status][locale]}</p>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        <StatusChip status={value.status} data={data} />
        {value.badge && <ConfidenceBadge kind={value.badge} />}
        {value.provisional && (
          <span className="border-petrol/20 text-slate rounded-full border px-2 py-0.5 text-[11px]">
            {t("diag.provisional")}
          </span>
        )}
      </div>
      <div className="text-slate mt-3 space-y-0.5 text-xs">
        {available && <RankLine value={value} neutral={meta.direction === "neutral"} />}
        {available && (
          <p>
            <GapLine value={value} data={data} />
          </p>
        )}
        {value.extra?.share_of_area_pct !== undefined && (
          <p>
            {t("diag.shareOfArea", {
              share: formatNumber(value.extra.share_of_area_pct, locale, 1),
            })}
          </p>
        )}
        {!available && value.reason && <p className="text-petrol/80">{value.reason}</p>}
        {!available && meta.requested_from && (
          <p className="text-terracotta">{t("diag.requested", { holder: meta.requested_from })}</p>
        )}
      </div>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="text-petrol mt-auto self-start pt-3 text-xs underline"
      >
        {t("diag.source")} · {t("diag.method")}
      </button>
      {open && (
        <dl className="bg-cream text-slate mt-2 space-y-1 rounded-lg p-3 text-xs">
          <div>
            <dt className="inline font-medium">{t("diag.source")} : </dt>
            <dd className="inline">{value.sources?.join(" ; ") || meta.source_expected}</dd>
          </div>
          {value.method && (
            <div>
              <dt className="inline font-medium">{t("diag.method")} : </dt>
              <dd className="inline">{t(`diag.methods.${value.method}`)}</dd>
            </div>
          )}
          {value.year && (
            <div>
              <dt className="inline font-medium">{t("diag.year")} : </dt>
              <dd className="inline">{value.year}</dd>
            </div>
          )}
          {value.reliability !== undefined && (
            <div>
              <dt className="inline font-medium">{t("diag.reliability")} : </dt>
              <dd className="inline">{value.reliability} / 100</dd>
            </div>
          )}
          {meta.threshold_note && (
            <div>
              <dt className="inline font-medium">{t("diag.threshold")} : </dt>
              <dd className="inline">{meta.threshold_note}</dd>
            </div>
          )}
          {meta.note && <p>{meta.note}</p>}
        </dl>
      )}
    </article>
  );
}

function MiniMap({ unitId, loaded }: { unitId: number; loaded: Loaded }) {
  const feature = loaded.units.features.find((f) => f.properties.id === unitId);
  const categories = loaded.facilities.meta.categories;
  const colors = Object.fromEntries(categories.map((c) => [c.code, c.color]));
  const points = loaded.facilities.features.filter(
    (f) => (f.properties as { territory_id?: number }).territory_id === unitId,
  );
  const rings = useMemo(() => {
    if (!feature) return [];
    const geometry = feature.geometry as GeoJSON.MultiPolygon | GeoJSON.Polygon;
    const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
    return polygons.flatMap((polygon) => polygon);
  }, [feature]);
  if (!feature || !rings.length) return null;
  const all = rings.flat();
  const xs = all.map((p) => p[0]);
  const ys = all.map((p) => p[1]);
  const [minX, maxX, minY, maxY] = [
    Math.min(...xs),
    Math.max(...xs),
    Math.min(...ys),
    Math.max(...ys),
  ];
  const k = Math.cos(((minY + maxY) / 2) * (Math.PI / 180));
  const w = (maxX - minX) * k || 0.01;
  const h = maxY - minY || 0.01;
  const size = 300;
  const scale = size / Math.max(w, h);
  const px = (x: number) => (x - minX) * k * scale + 10;
  const py = (y: number) => (maxY - y) * scale + 10;
  const d = rings
    .map(
      (ring) =>
        "M" + ring.map((p) => `${px(p[0]).toFixed(1)},${py(p[1]).toFixed(1)}`).join("L") + "Z",
    )
    .join("");
  return (
    <svg
      viewBox={`0 0 ${w * scale + 20} ${h * scale + 20}`}
      className="h-auto w-full"
      role="img"
      aria-hidden
    >
      <path d={d} className="fill-cream stroke-petrol" strokeWidth={1.5} fillRule="evenodd" />
      {points.map((p) => (
        <circle
          key={p.properties.id}
          cx={px(p.geometry.coordinates[0])}
          cy={py(p.geometry.coordinates[1])}
          r={2.6}
          fill={colors[p.properties.category] ?? "#12343b"}
          stroke="#fff"
          strokeWidth={0.6}
        />
      ))}
    </svg>
  );
}

export function UnitSheetView({ code, unitId }: { code: string; unitId: number }) {
  const { locale, t } = useLocale();
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchDiagnostic(code), fetchUnits(code), fetchFacilities(code)])
      .then(([diag, units, facilities]) => !cancelled && setLoaded({ diag, units, facilities }))
      .catch((exc: Error) => !cancelled && setError(exc.message));
    return () => {
      cancelled = true;
    };
  }, [code]);

  const unit: DiagnosticUnit | undefined = loaded?.diag.units.find((u) => u.id === unitId);
  const props = loaded?.units.features.find((f) => f.properties.id === unitId)?.properties;

  return (
    <div className="min-h-screen">
      <AppHeader territory={code} />
      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8 print:py-0">
        <Link
          href={`/territoire/${code}`}
          className="text-slate hover:text-petrol text-sm print:hidden"
        >
          <span aria-hidden className="inline-block rtl:rotate-180">
            ←
          </span>{" "}
          {t("diag.back")}
        </Link>
        {error && (
          <p role="alert" className="bg-terracotta/10 text-terracotta-dark mt-6 rounded-xl p-4">
            {t("diag.loadError")} {error}
          </p>
        )}
        {!loaded && !error && <p className="text-slate mt-10">{t("map.loading")}</p>}
        {loaded && unit && (
          <SheetBody
            loaded={loaded}
            unit={unit}
            code={code}
            parent={props ? (locale === "ar" && props.parent_ar) || props.parent_fr : null}
            term={props?.term?.[locale] ?? null}
          />
        )}
      </main>
    </div>
  );
}

function SheetBody({
  loaded,
  unit,
  code,
  parent,
  term,
}: {
  loaded: Loaded;
  unit: DiagnosticUnit;
  code: string;
  parent: string | null;
  term: string | null;
}) {
  const { locale, t } = useLocale();
  const { diag } = loaded;
  const population = unit.values.DEM_POP;
  const popMeta = diag.indicators.find((i) => i.code === "DEM_POP");
  const values = diag.indicators.map((i) => unit.values[i.code]);
  const available = values.filter((v) => v && v.value !== null).length;
  const attention = attentionPoints(unit, diag.indicators);
  const built = unit.values.URB_BATI;
  const growth = unit.values.URB_CROIS;

  return (
    <>
      <header className="mt-4 flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="text-terracotta text-sm font-medium">
            {term}
            {parent ? ` · ${parent}` : ""}
          </p>
          <h1 className="font-heading text-petrol text-5xl sm:text-6xl">
            {unitName(unit, locale)}
          </h1>
          {locale === "fr" && unit.name_ar && (
            <p lang="ar" dir="rtl" className="font-arabic text-petrol text-2xl">
              {unit.name_ar}
            </p>
          )}
          {unit.official_code && (
            <p className="text-slate mt-1 text-xs">
              {t("map.officialCode")} HCP : {unit.official_code} <ConfidenceBadge kind="official" />
            </p>
          )}
        </div>
        <dl className="grid grid-cols-3 gap-6 text-sm">
          <div>
            <dt className="text-slate">{t("diag.population")}</dt>
            <dd className="text-petrol mt-1 text-2xl font-semibold tabular-nums">
              {population?.value != null && popMeta
                ? formatValue(population.value, popMeta, locale)
                : "—"}
            </dd>
            <dd className="mt-1">
              <ConfidenceBadge kind="official" /> <span className="text-slate text-xs">2024</span>
            </dd>
          </div>
          <div>
            <dt className="text-slate">{t("diag.area")}</dt>
            <dd className="text-petrol mt-1 text-2xl font-semibold tabular-nums">
              {unit.area_km2 != null ? `${formatNumber(unit.area_km2, locale, 1)} km²` : "—"}
            </dd>
            <dd className="mt-1">
              <ConfidenceBadge kind="estimated" />
            </dd>
          </div>
          <div>
            <dt className="text-slate">{t("diag.completeness")}</dt>
            <dd className="text-petrol mt-1 text-2xl font-semibold tabular-nums">
              {available}/{values.length}
            </dd>
            <dd className="text-slate mt-1 text-xs">
              {t("diag.indicatorsAvailable", {
                n: String(available),
                total: String(values.length),
              })}
            </dd>
          </div>
        </dl>
      </header>

      {unit.warning && (
        <p
          role="alert"
          className="bg-terracotta/10 text-terracotta-dark mt-6 rounded-xl p-4 text-sm"
        >
          <span aria-hidden>▲ </span>
          {unit.warning[locale]}
        </p>
      )}

      <div className="mt-6">
        <GridBanner data={diag} />
      </div>

      <section className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="border-petrol/10 rounded-2xl border bg-white p-6">
          <h2 className="font-heading text-petrol text-3xl">{t("diag.attention")}</h2>
          {attention.length ? (
            <ol className="mt-4 space-y-3">
              {attention.map(({ meta, value }) => (
                <li
                  key={meta.code}
                  className="border-petrol/10 flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b pb-3 last:border-0"
                >
                  <StatusChip status={value.status} data={diag} />
                  <span className="text-petrol font-medium">{meta.label[locale]}</span>
                  <span className="text-petrol tabular-nums">
                    {formatValue(value.value, meta, locale)} {meta.unit[locale]}
                  </span>
                  <span className="text-slate text-xs">
                    <GapLine value={value} data={diag} />
                  </span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-slate mt-4">{t("diag.attentionNone")}</p>
          )}
          <p className="text-slate mt-4 text-xs">{t("diag.attentionRule")}</p>
        </div>
        <div className="border-petrol/10 rounded-2xl border bg-white p-6">
          <h2 className="text-petrol text-sm font-semibold">{t("diag.minimap")}</h2>
          <div className="mt-3">
            <MiniMap unitId={unit.id} loaded={loaded} />
          </div>
          {built?.value != null && growth?.extra?.absolute !== undefined && (
            <p className="text-slate mt-4 text-sm">
              <strong className="text-petrol">{t("diag.builtUp")}</strong> —{" "}
              {t("diag.builtUpEvolution", { from: "2015", to: "2020" })} :{" "}
              <span className="text-petrol tabular-nums">
                {formatNumber(built.value - growth.extra.absolute, locale, 2)} →{" "}
                {formatNumber(built.value, locale, 2)} km²
              </span>{" "}
              <ConfidenceBadge kind="open" />
            </p>
          )}
          <TypologyLine data={diag} unitId={unit.id} />
          <Link
            href={`/territoire/${code}/comparer?ids=${unit.id}`}
            className="border-petrol/30 text-petrol hover:bg-petrol/5 mt-5 inline-flex rounded-lg border px-4 py-2 text-sm print:hidden"
          >
            {t("diag.compare")}
          </Link>
        </div>
      </section>

      {diag.grid.axes.map((axis) => {
        const metas = diag.indicators.filter((i) => i.axis === axis.code);
        if (!metas.length) return null;
        return (
          <section key={axis.code} className="mt-10 break-inside-avoid">
            <h3 className="font-heading text-petrol text-2xl">
              <span className="text-terracotta">{axis.number}.</span> {axis.label[locale]}
            </h3>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {metas.map((meta) => (
                <IndicatorCard
                  key={meta.code}
                  meta={meta}
                  value={unit.values[meta.code]}
                  data={diag}
                />
              ))}
            </div>
          </section>
        );
      })}

      <ReportPanel code={code} unitId={unit.id} />
    </>
  );
}

function TypologyLine({ data, unitId }: { data: DiagnosticData; unitId: number }) {
  const { locale, t } = useLocale();
  const typology = data.typology;
  if (!typology?.available) return null;
  const entry = typology.units[String(unitId)];
  return (
    <div className="border-petrol/10 mt-4 border-t pt-4 text-sm">
      <p className="text-slate text-xs">{typology.label[locale]}</p>
      {entry ? (
        <>
          <p className="text-petrol mt-1 font-medium">{entry.label[locale]}</p>
          {entry.traits.length > 0 && (
            <p className="text-slate mt-1 text-xs">
              {entry.traits.map((trait) => trait[locale]).join(" · ")}
            </p>
          )}
        </>
      ) : (
        <p className="text-slate mt-1">{t("diag.typologyUnclassified")}</p>
      )}
    </div>
  );
}
