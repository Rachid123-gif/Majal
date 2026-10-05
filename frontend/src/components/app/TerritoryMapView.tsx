"use client";

import dynamic from "next/dynamic";
import type { Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppHeader } from "@/components/app/AppHeader";
import { ConfidenceBadge } from "@/components/app/ConfidenceBadge";
import type { HoverInfo } from "@/components/app/TerritoryMap";
import { useLocale } from "@/i18n/LocaleProvider";
import { formatDate, formatNumber } from "@/lib/format";
import {
  fetchFacilities,
  fetchTilesInfo,
  fetchUnits,
  type FacilityCollection,
  type TilesInfo,
  type UnitCollection,
  type UnitProperties,
} from "@/lib/maps";

const TerritoryMap = dynamic(
  () => import("@/components/app/TerritoryMap").then((m) => m.TerritoryMap),
  { ssr: false },
);

type Data = { units: UnitCollection; facilities: FacilityCollection; tiles: TilesInfo };

export function TerritoryMapView({ code }: { code: string }) {
  const { locale, t } = useLocale();
  const [scope, setScope] = useState<string | undefined>(undefined);
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);
  const [hidden, setHidden] = useState<string[]>([]);
  const [hover, setHover] = useState<HoverInfo>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchUnits(code, scope), fetchFacilities(code, scope), fetchTilesInfo(code)])
      .then(([units, facilities, tiles]) => {
        if (!cancelled) {
          setData({ units, facilities, tiles });
          setError(false);
        }
      })
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
    };
  }, [code, scope]);

  const categories = useMemo(() => data?.facilities.meta.categories ?? [], [data]);
  const colors = useMemo(
    () => Object.fromEntries(categories.map((c) => [c.code, c.color])),
    [categories],
  );
  const visible = useMemo(
    () => categories.map((c) => c.code).filter((c) => !hidden.includes(c)),
    [categories, hidden],
  );
  const selected = data?.units.features.find((f) => f.properties.id === selectedId)?.properties;
  const name = (unit: UnitProperties) => (locale === "ar" && unit.name_ar) || unit.name_fr;

  /** PNG export of the displayed map, with title and sources burnt in (BRIEF §9.1). */
  function exportPng() {
    const map = mapRef.current;
    if (!map || !data) return;
    map.once("render", () => {
      const source = map.getCanvas();
      const band = Math.round(source.height * 0.09);
      const canvas = document.createElement("canvas");
      canvas.width = source.width;
      canvas.height = source.height + band;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(source, 0, 0);
      ctx.fillStyle = "#f6f3ec";
      ctx.fillRect(0, source.height, canvas.width, band);
      const scope = data.units.meta.scopes.find((s) => s.code === data.units.meta.scope);
      const size = Math.round(band * 0.28);
      ctx.fillStyle = "#12343b";
      ctx.font = `600 ${size}px "IBM Plex Sans", sans-serif`;
      ctx.textBaseline = "middle";
      ctx.fillText(
        `MAJAL — ${t("map.title")} — ${scope?.label.fr ?? ""}`,
        size,
        source.height + band * 0.33,
      );
      ctx.font = `${Math.round(size * 0.75)}px "IBM Plex Sans", sans-serif`;
      ctx.fillStyle = "#4a5560";
      const src = data.units.meta.source;
      ctx.fillText(
        `${t("map.boundaries")} : ${src?.producer ?? ""}, ${t("map.dataOf")} ${formatDate(src?.data_date, "fr")} (${src?.license ?? ""}, ${t("map.toVerify")}) · ${t("map.basemap")} : © OpenStreetMap, Protomaps · ${t("demoBanner")}`,
        size,
        source.height + band * 0.72,
      );
      const link = document.createElement("a");
      link.download = `majal-${code}-${data.units.meta.scope}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    });
    map.triggerRepaint();
  }

  return (
    <div className="flex h-screen flex-col">
      <AppHeader territory={code} />
      {error && (
        <p role="alert" className="bg-terracotta/10 text-terracotta-dark px-6 py-3 text-sm">
          {t("map.error")}
        </p>
      )}
      {data && !data.units.meta.imported ? (
        <div className="grid flex-1 place-items-center p-8">
          <p className="border-petrol/15 text-petrol max-w-lg rounded-2xl border bg-white p-8 text-center text-lg">
            {t("map.notImported")}
          </p>
        </div>
      ) : (
        <div className="relative flex min-h-0 flex-1">
          {/* Side panel: perimeter, facility layers */}
          <aside className="border-petrol/10 hidden w-80 shrink-0 flex-col overflow-y-auto border-e bg-white/85 p-5 md:flex">
            <h1 className="font-heading text-petrol text-3xl">{t("map.title")}</h1>
            {data && (
              <p className="text-slate mt-1 text-sm">
                {data.units.features.length} {t("map.units")}
              </p>
            )}
            {data && data.units.meta.scopes.length > 1 && (
              <fieldset className="mt-5">
                <legend className="text-slate text-xs font-semibold tracking-wider uppercase">
                  {t("map.scope")}
                </legend>
                <div className="mt-2 flex flex-col gap-1.5">
                  {data.units.meta.scopes.map((s) => {
                    const active = s.code === data.units.meta.scope;
                    return (
                      <button
                        key={s.code}
                        type="button"
                        aria-pressed={active}
                        onClick={() => {
                          setScope(s.code);
                          setSelectedId(null);
                        }}
                        className={`rounded-lg border px-3 py-2 text-start text-sm ${
                          active
                            ? "border-petrol bg-petrol text-cream"
                            : "border-petrol/15 text-petrol hover:bg-petrol/5"
                        }`}
                      >
                        {s.label[locale]}
                      </button>
                    );
                  })}
                </div>
              </fieldset>
            )}

            <div className="mt-6 flex items-center justify-between">
              <h2 className="text-slate text-xs font-semibold tracking-wider uppercase">
                {t("map.facilities")}
              </h2>
              <button
                type="button"
                className="text-petrol text-xs underline"
                onClick={() => setHidden(hidden.length ? [] : categories.map((c) => c.code))}
              >
                {hidden.length ? t("map.showAll") : t("map.hideAll")}
              </button>
            </div>
            <ul className="mt-2 space-y-1">
              {categories.map((category) => {
                const on = !hidden.includes(category.code);
                return (
                  <li key={category.code}>
                    <label className="hover:bg-petrol/5 flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-1.5 text-sm">
                      <input
                        type="checkbox"
                        checked={on}
                        onChange={() =>
                          setHidden(
                            on
                              ? [...hidden, category.code]
                              : hidden.filter((c) => c !== category.code),
                          )
                        }
                        className="accent-petrol"
                      />
                      <span
                        aria-hidden
                        className="h-3 w-3 shrink-0 rounded-full border border-white shadow"
                        style={{ background: category.color }}
                      />
                      <span className="text-petrol flex-1">{category.label[locale]}</span>
                      <span className="text-slate tabular-nums">
                        {formatNumber(category.count, locale)}
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
            {data?.facilities.meta.source && (
              <p className="text-slate mt-3 flex flex-wrap items-center gap-2 text-xs">
                <ConfidenceBadge kind={data.facilities.meta.source.badge} />
                OpenStreetMap, {t("map.dataOf")}{" "}
                {formatDate(data.facilities.meta.source.data_date, locale)}
              </p>
            )}
            <button
              type="button"
              onClick={exportPng}
              disabled={!data}
              className="border-petrol/30 text-petrol hover:bg-petrol/5 mt-6 rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
            >
              {t("map.exportPng")}
            </button>
            <p className="text-slate mt-auto pt-6 text-xs leading-relaxed">{t("map.hint")}</p>
          </aside>

          {/* Map */}
          <div className="relative min-w-0 flex-1">
            {data ? (
              <TerritoryMap
                key={`${code}-${locale}`}
                code={code}
                locale={locale}
                units={data.units}
                facilities={data.facilities}
                visibleCategories={visible}
                colors={colors}
                selectedId={selectedId}
                onHover={setHover}
                onSelect={(id) => {
                  setSelectedId(id);
                  setHover(null);
                }}
                onMap={(map) => {
                  mapRef.current = map;
                }}
              />
            ) : (
              !error && (
                <p className="text-slate grid h-full place-items-center">{t("map.loading")}</p>
              )
            )}

            {hover && (
              <div
                className="pointer-events-none absolute z-10 rounded-xl bg-white/95 px-3 py-2 shadow-lg"
                style={{ left: hover.x + 14, top: hover.y + 14 }}
              >
                <p className="text-petrol font-medium">{hover.unit.name_fr}</p>
                {hover.unit.name_ar && (
                  <p lang="ar" dir="rtl" className="font-arabic text-petrol">
                    {hover.unit.name_ar}
                  </p>
                )}
                <p className="text-slate mt-1 flex items-center gap-2 text-xs">
                  {hover.unit.term?.[locale]}
                  <ConfidenceBadge kind="open" />
                </p>
              </div>
            )}

            {data?.tiles.available === false && (
              <p className="bg-terracotta/10 text-terracotta-dark absolute top-3 start-3 rounded-lg px-3 py-2 text-sm">
                {t("map.noBasemap")}
              </p>
            )}

            {/* Sources, always visible */}
            {data && (
              <div className="text-slate absolute bottom-2 start-2 z-10 max-w-[70%] rounded-lg bg-white/90 px-3 py-2 text-[11px] leading-relaxed shadow">
                <p className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <strong className="text-petrol">{t("map.boundaries")} :</strong>
                  {data.units.meta.source?.producer}, {t("map.dataOf")}{" "}
                  {formatDate(data.units.meta.source?.data_date, locale)} ·{" "}
                  {data.units.meta.source?.license} · {t("map.toVerify")}
                  <ConfidenceBadge kind="open" />
                </p>
                {data.tiles.available && (
                  <p>
                    <strong className="text-petrol">{t("map.basemap")} :</strong>{" "}
                    {data.tiles.attribution} ({formatDate(data.tiles.retrieved_at, locale)})
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Detail of the selected unit */}
          {selected && (
            <aside className="border-petrol/10 absolute inset-y-0 end-0 z-20 w-full max-w-sm overflow-y-auto border-s bg-white p-6 shadow-2xl">
              <button
                type="button"
                onClick={() => setSelectedId(null)}
                className="text-slate hover:text-petrol float-end text-sm"
              >
                {t("map.close")} ✕
              </button>
              <p className="text-terracotta text-sm font-medium">{selected.term?.[locale]}</p>
              <h2 className="font-heading text-petrol mt-1 text-4xl">{name(selected)}</h2>
              {locale === "fr" && selected.name_ar && (
                <p lang="ar" dir="rtl" className="font-arabic text-petrol text-xl">
                  {selected.name_ar}
                </p>
              )}
              <dl className="mt-6 space-y-4 text-sm">
                <div>
                  <dt className="text-slate">{t("map.parent")}</dt>
                  <dd className="text-petrol">
                    {(locale === "ar" && selected.parent_ar) || selected.parent_fr || "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate">{t("map.area")}</dt>
                  <dd className="text-petrol flex flex-wrap items-center gap-2">
                    {selected.area_km2 !== null
                      ? `${formatNumber(selected.area_km2, locale, 1)} km²`
                      : t("map.notAvailable")}
                    <ConfidenceBadge kind="estimated" />
                    <span className="text-slate text-xs">({t("map.areaMethod")})</span>
                  </dd>
                </div>
                <div>
                  <dt className="text-slate">{t("map.officialCode")}</dt>
                  <dd className="text-petrol">{selected.official_code ?? t("map.notAvailable")}</dd>
                </div>
              </dl>
              <h3 className="text-petrol mt-6 flex items-center gap-2 text-sm font-semibold">
                {t("map.facilitiesTitle")} <ConfidenceBadge kind="open" />
              </h3>
              <ul className="mt-2 space-y-1.5 text-sm">
                {categories.map((category) => (
                  <li key={category.code} className="flex items-center gap-2">
                    <span
                      aria-hidden
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ background: category.color }}
                    />
                    <span className="text-petrol flex-1">{category.label[locale]}</span>
                    <span className="text-petrol tabular-nums font-medium">
                      {formatNumber(selected.facilities[category.code] ?? 0, locale)}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="bg-cream text-slate mt-6 rounded-lg p-3 text-xs leading-relaxed">
                {t("map.fullSheet")}
              </p>
            </aside>
          )}
        </div>
      )}
    </div>
  );
}
