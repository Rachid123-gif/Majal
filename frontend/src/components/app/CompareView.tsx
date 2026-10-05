"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppHeader } from "@/components/app/AppHeader";
import { GridBanner } from "@/components/app/GridBanner";
import { useLocale } from "@/i18n/LocaleProvider";
import {
  STATUS_STYLE,
  fetchDiagnostic,
  formatValue,
  unitName,
  type DiagnosticData,
  type IndicatorMeta,
} from "@/lib/diagnostic";

const MAX = 4;
const SERIES = ["#12343b", "#a8461f", "#3f8580", "#8a6d1e"];

function csvCell(value: string): string {
  return /[",;\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

export function CompareView({ code }: { code: string }) {
  const { locale, t } = useLocale();
  const router = useRouter();
  const params = useSearchParams();
  const [diag, setDiag] = useState<DiagnosticData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [chartCode, setChartCode] = useState<string | null>(null);
  const chartRef = useRef<SVGSVGElement>(null);

  const ids = useMemo(
    () =>
      (params.get("ids") ?? "")
        .split(",")
        .map(Number)
        .filter((n) => Number.isInteger(n) && n > 0)
        .slice(0, MAX),
    [params],
  );

  useEffect(() => {
    let cancelled = false;
    fetchDiagnostic(code)
      .then((value) => {
        if (cancelled) return;
        setDiag(value);
        setChartCode(
          (c) => c ?? value.indicators.find((i) => i.direction !== "neutral")?.code ?? null,
        );
      })
      .catch((exc: Error) => !cancelled && setError(exc.message));
    return () => {
      cancelled = true;
    };
  }, [code]);

  const selected = diag
    ? ids.map((id) => diag.units.find((u) => u.id === id)).filter((u) => u !== undefined)
    : [];

  function toggle(id: number) {
    const next = ids.includes(id)
      ? ids.filter((x) => x !== id)
      : ids.length < MAX
        ? [...ids, id]
        : ids;
    router.replace(`/territoire/${code}/comparer?ids=${next.join(",")}`);
  }

  function exportCsv() {
    if (!diag) return;
    const header = [
      t("diag.indicator"),
      "Unité",
      ...selected.map((u) => u.name_fr),
      t("diag.reference", { ref: diag.evaluation.reference_label.fr }),
      "Source",
    ];
    const lines = [header.map(csvCell).join(";")];
    for (const meta of diag.indicators) {
      lines.push(
        [
          meta.label.fr,
          meta.unit.fr,
          ...selected.map((u) => {
            const v = u.values[meta.code];
            return v.value === null
              ? diag.evaluation.statuses[v.status].fr
              : formatValue(v.value, meta, "fr");
          }),
          meta.reference ? formatValue(meta.reference.value, meta, "fr") : "",
          meta.source_expected,
        ]
          .map(csvCell)
          .join(";"),
      );
    }
    lines.push(csvCell(`${diag.grid.label.fr} — ${diag.evaluation.label.fr}`));
    const blob = new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.download = `majal-${code}-comparaison.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function exportPng() {
    const svg = chartRef.current;
    if (!svg) return;
    const source = new XMLSerializer().serializeToString(svg);
    const image = new Image();
    const { width, height } = svg.viewBox.baseVal;
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = width * 2;
      canvas.height = height * 2;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      const link = document.createElement("a");
      link.download = `majal-${code}-${chartCode}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    };
    image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(source)}`;
  }

  const chartMeta: IndicatorMeta | undefined = diag?.indicators.find((i) => i.code === chartCode);

  return (
    <div className="min-h-screen">
      <AppHeader territory={code} />
      <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        <Link href={`/territoire/${code}`} className="text-slate hover:text-petrol text-sm">
          <span aria-hidden className="inline-block rtl:rotate-180">
            ←
          </span>{" "}
          {t("diag.back")}
        </Link>
        <h1 className="font-heading text-petrol mt-3 text-5xl">{t("diag.compareTitle")}</h1>
        {error && (
          <p className="bg-terracotta/10 text-terracotta-dark mt-4 rounded-xl p-4">{error}</p>
        )}
        {diag && (
          <>
            <div className="mt-4">
              <GridBanner data={diag} />
            </div>
            <fieldset className="mt-6">
              <legend className="text-slate text-sm">
                {t("diag.compareHint")} {ids.length >= MAX && t("diag.compareMax")}
              </legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {diag.units.map((u) => {
                  const on = ids.includes(u.id);
                  return (
                    <button
                      key={u.id}
                      type="button"
                      aria-pressed={on}
                      onClick={() => toggle(u.id)}
                      disabled={!on && ids.length >= MAX}
                      className={`rounded-full border px-3 py-1.5 text-sm disabled:opacity-40 ${
                        on
                          ? "border-petrol bg-petrol text-cream"
                          : "border-petrol/20 text-petrol hover:bg-petrol/5"
                      }`}
                    >
                      {unitName(u, locale)}
                    </button>
                  );
                })}
              </div>
            </fieldset>

            {selected.length >= 1 && (
              <>
                <div className="mt-6 flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={exportCsv}
                    className="border-petrol/30 text-petrol hover:bg-petrol/5 rounded-lg border px-4 py-2 text-sm"
                  >
                    {t("diag.exportCsv")}
                  </button>
                </div>
                <div className="mt-4 overflow-x-auto rounded-2xl border border-petrol/10 bg-white">
                  <table className="w-full min-w-[720px] text-sm">
                    <thead>
                      <tr className="bg-petrol text-cream text-start">
                        <th className="px-4 py-3 text-start font-medium">{t("diag.indicator")}</th>
                        {selected.map((u, i) => (
                          <th key={u.id} className="px-4 py-3 text-end font-medium">
                            <span
                              aria-hidden
                              className="ring-cream me-1.5 inline-block h-2.5 w-2.5 rounded-full ring-2"
                              style={{ background: SERIES[i] }}
                            />
                            {unitName(u, locale)}
                          </th>
                        ))}
                        <th className="px-4 py-3 text-end font-medium">
                          {t("diag.reference", { ref: diag.evaluation.reference_label[locale] })}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {diag.grid.axes.map((axis) => {
                        const metas = diag.indicators.filter((i) => i.axis === axis.code);
                        if (!metas.length) return null;
                        return [
                          <tr key={axis.code} className="bg-cream">
                            <th
                              colSpan={selected.length + 2}
                              className="text-petrol px-4 py-2 text-start font-semibold"
                            >
                              {axis.number}. {axis.label[locale]}
                            </th>
                          </tr>,
                          ...metas.map((meta) => (
                            <tr key={meta.code} className="border-petrol/5 border-t">
                              <td className="text-petrol px-4 py-2.5">
                                {meta.label[locale]}{" "}
                                <span className="text-slate text-xs">({meta.unit[locale]})</span>
                              </td>
                              {selected.map((u) => {
                                const v = u.values[meta.code];
                                const style = STATUS_STYLE[v.status];
                                return (
                                  <td key={u.id} className="px-4 py-2.5 text-end tabular-nums">
                                    {v.value === null ? (
                                      <span className="text-slate text-xs">
                                        {diag.evaluation.statuses[v.status][locale]}
                                      </span>
                                    ) : (
                                      <span className="inline-flex items-center gap-1.5">
                                        {formatValue(v.value, meta, locale)}
                                        {meta.direction !== "neutral" && (
                                          <span
                                            title={diag.evaluation.statuses[v.status][locale]}
                                            className="inline-grid h-4 w-4 place-items-center rounded-full text-[9px]"
                                            style={{
                                              background: style.color,
                                              color: v.status === "watch" ? "#12343b" : "#fff",
                                            }}
                                          >
                                            {style.symbol}
                                          </span>
                                        )}
                                      </span>
                                    )}
                                  </td>
                                );
                              })}
                              <td className="text-slate px-4 py-2.5 text-end tabular-nums">
                                {meta.reference
                                  ? formatValue(meta.reference.value, meta, locale)
                                  : "—"}
                              </td>
                            </tr>
                          )),
                        ];
                      })}
                    </tbody>
                  </table>
                </div>

                <section className="mt-10">
                  <div className="flex flex-wrap items-end gap-4">
                    <label className="block">
                      <span className="text-slate text-sm">{t("diag.chart")}</span>
                      <select
                        value={chartCode ?? ""}
                        onChange={(e) => setChartCode(e.target.value)}
                        className="border-petrol/20 text-petrol mt-1 block rounded-lg border bg-white px-2 py-2 text-sm"
                      >
                        {diag.indicators.map((i) => (
                          <option key={i.code} value={i.code}>
                            {i.label[locale]}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      type="button"
                      onClick={exportPng}
                      className="border-petrol/30 text-petrol hover:bg-petrol/5 rounded-lg border px-4 py-2 text-sm"
                    >
                      {t("diag.exportPng")}
                    </button>
                  </div>
                  {chartMeta && (
                    <BarChart svgRef={chartRef} meta={chartMeta} diag={diag} units={selected} />
                  )}
                </section>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function BarChart({
  svgRef,
  meta,
  diag,
  units,
}: {
  svgRef: React.RefObject<SVGSVGElement | null>;
  meta: IndicatorMeta;
  diag: DiagnosticData;
  units: DiagnosticData["units"];
}) {
  const { locale } = useLocale();
  const rows = units.map((u, i) => ({
    unit: u,
    value: u.values[meta.code]?.value ?? null,
    color: SERIES[i],
  }));
  const ref = meta.reference?.value ?? null;
  const max = Math.max(...rows.map((r) => r.value ?? 0), ref ?? 0) || 1;
  const width = 760;
  const rowH = 44;
  const left = 220;
  const top = 64;
  const height = top + rows.length * rowH + 70;
  const x = (v: number) => left + (v / max) * (width - left - 90);
  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${width} ${height}`}
      className="mt-4 w-full rounded-2xl border border-petrol/10 bg-white"
      role="img"
      aria-label={meta.label[locale]}
      direction="ltr"
      fontFamily="IBM Plex Sans, IBM Plex Sans Arabic, sans-serif"
    >
      <text x={20} y={30} fontSize={16} fontWeight={600} fill="#12343b">
        {meta.label[locale]} ({meta.unit[locale]})
      </text>
      <text x={20} y={50} fontSize={11} fill="#4a5560">
        {diag.grid.label[locale]}
      </text>
      {rows.map((row, i) => (
        <g key={row.unit.id} transform={`translate(0, ${top + i * rowH})`}>
          <text x={left - 10} y={rowH / 2 + 4} fontSize={13} textAnchor="end" fill="#12343b">
            {unitName(row.unit, locale)}
          </text>
          {row.value === null ? (
            <text x={left} y={rowH / 2 + 4} fontSize={12} fill="#4a5560">
              {diag.evaluation.statuses[row.unit.values[meta.code].status][locale]}
            </text>
          ) : (
            <>
              <rect
                x={left}
                y={10}
                width={Math.max(2, x(row.value) - left)}
                height={rowH - 20}
                rx={4}
                fill={row.color}
              />
              <text x={x(row.value) + 6} y={rowH / 2 + 4} fontSize={12} fill="#12343b">
                {formatValue(row.value, meta, locale)}
              </text>
            </>
          )}
        </g>
      ))}
      {ref !== null && (
        <g>
          <line
            x1={x(ref)}
            x2={x(ref)}
            y1={top - 6}
            y2={top + rows.length * rowH}
            stroke="#a8461f"
            strokeDasharray="4 4"
            strokeWidth={1.5}
          />
          <text
            x={x(ref)}
            y={top + rows.length * rowH + 18}
            fontSize={11}
            textAnchor="middle"
            fill="#a8461f"
          >
            {diag.evaluation.reference_label[locale]} : {formatValue(ref, meta, locale)}
          </text>
        </g>
      )}
      <text x={20} y={height - 14} fontSize={10} fill="#4a5560">
        {meta.source_expected} · MAJAL
      </text>
    </svg>
  );
}
