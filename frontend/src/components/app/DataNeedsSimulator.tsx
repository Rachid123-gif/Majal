"use client";

import { useMemo, useState } from "react";
import { useLocale } from "@/i18n/LocaleProvider";
import { simulate, type DataNeeds } from "@/lib/dataNeeds";

/** Colours of the completeness bars: each status also has a text label (never colour alone). */
const SEGMENTS = [
  { key: "official", className: "bg-petrol", darkClassName: "bg-cream" },
  { key: "open", className: "bg-petrol/60", darkClassName: "bg-cream/60" },
  { key: "estimated", className: "bg-petrol/30", darkClassName: "bg-cream/30" },
] as const;

/**
 * Completeness bars and the simulator « Si nous obtenons les données de… »: ticking an
 * institution updates the bars and the counter live, distinguishing computed, made reliable
 * and refined indicators. Nothing is added: the notice says so. Used on the module's screen and
 * in the presentation mode (`tone="dark"`).
 */
export function DataNeedsSimulator({
  data,
  tone = "light",
}: {
  data: DataNeeds;
  tone?: "light" | "dark";
}) {
  const { locale, t } = useLocale();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const sim = useMemo(() => simulate(data, selected), [data, selected]);
  const dark = tone === "dark";
  const muted = dark ? "text-cream/70" : "text-slate";
  const strong = dark ? "text-cream" : "text-petrol";
  const card = dark ? "border-cream/20 bg-cream/5" : "border-petrol/10 bg-white";
  const effect = (key: "computed" | "reliable" | "finer") => data.effects[key].label[locale];
  const active = selected.size > 0;

  const toggle = (code: string) =>
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });

  return (
    <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
      <section aria-labelledby="completeness-title" className={`rounded-2xl border p-6 ${card}`}>
        <h2 id="completeness-title" className={`font-heading text-2xl ${strong}`}>
          {t("dataNeeds.byAxis")}
        </h2>
        <p className={`mt-2 text-3xl font-semibold tabular-nums ${strong}`} aria-live="polite">
          {active && sim.computed.size > 0
            ? t("dataNeeds.availableSimulated", {
                n: String(sim.available),
                total: String(sim.total),
                computed: String(sim.computed.size),
              })
            : t("dataNeeds.available", { n: String(sim.available), total: String(sim.total) })}
        </p>
        {active && (
          <p className={`mt-1 text-sm ${strong}`}>
            {t("dataNeeds.simulatedSummary", {
              computed: String(sim.computed.size),
              reliable: String(sim.reliable.size),
              finer: String(sim.finer.size),
            })}
          </p>
        )}
        <ul className="mt-5 grid gap-3">
          {data.axes.map((axis) => {
            const s = sim.axes[axis.code];
            const width = (n: number) => `${(n / axis.total) * 100}%`;
            return (
              <li key={axis.code}>
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className={strong}>{axis.label[locale]}</span>
                  <span className={`tabular-nums ${muted}`}>
                    {s.available} / {axis.total}
                    {s.reliable + s.finer > 0 && (
                      <>
                        {" "}
                        ·{" "}
                        {[
                          s.reliable ? `${effect("reliable").toLowerCase()} : ${s.reliable}` : "",
                          s.finer ? `${effect("finer").toLowerCase()} : ${s.finer}` : "",
                        ]
                          .filter(Boolean)
                          .join(", ")}
                      </>
                    )}
                  </span>
                </div>
                <div
                  className={`mt-1 flex h-3 overflow-hidden rounded-full ${dark ? "bg-cream/15" : "bg-cream"}`}
                  role="img"
                  aria-label={`${axis.label[locale]} : ${s.available} / ${axis.total}`}
                >
                  {SEGMENTS.map(({ key, className, darkClassName }) =>
                    axis.counts[key] ? (
                      <span
                        key={key}
                        className={`${dark ? darkClassName : className} h-full`}
                        style={{ width: width(axis.counts[key]) }}
                      />
                    ) : null,
                  )}
                  {s.computed > 0 && (
                    <span
                      className="bg-terracotta h-full bg-[repeating-linear-gradient(45deg,transparent_0_4px,rgba(255,255,255,0.35)_4px_8px)]"
                      style={{ width: width(s.computed) }}
                    />
                  )}
                </div>
              </li>
            );
          })}
        </ul>
        <ul className={`mt-4 flex flex-wrap gap-x-4 gap-y-1 text-xs ${muted}`}>
          {SEGMENTS.map(({ key, className, darkClassName }) => (
            <li key={key} className="flex items-center gap-1.5">
              <span
                aria-hidden
                className={`${dark ? darkClassName : className} inline-block h-2.5 w-4 rounded-sm`}
              />
              {data.statuses[key][locale]}
            </li>
          ))}
          <li className="flex items-center gap-1.5">
            <span
              aria-hidden
              className={`${dark ? "bg-cream/15" : "bg-cream"} inline-block h-2.5 w-4 rounded-sm border`}
            />
            {data.statuses.missing[locale]}
          </li>
          <li className="flex items-center gap-1.5">
            <span aria-hidden className="bg-terracotta inline-block h-2.5 w-4 rounded-sm" />
            {t("dataNeeds.simulatedComputed")}
          </li>
        </ul>
      </section>

      <section aria-labelledby="simulator-title" className={`rounded-2xl border p-6 ${card}`}>
        <div className="flex items-start justify-between gap-3">
          <h2 id="simulator-title" className={`font-heading text-2xl ${strong}`}>
            {t("dataNeeds.simulatorTitle")}
          </h2>
          {active && (
            <button
              type="button"
              onClick={() => setSelected(new Set())}
              className={`shrink-0 text-xs underline ${muted}`}
            >
              {t("dataNeeds.reset")}
            </button>
          )}
        </div>
        <p
          role="note"
          className={`mt-3 rounded-lg border border-dashed px-3 py-2 text-xs font-medium ${
            dark
              ? "border-terracotta-light bg-terracotta-light/15 text-terracotta-light"
              : "border-terracotta bg-terracotta/10 text-terracotta-dark"
          }`}
        >
          ◆ {t("dataNeeds.simulationNotice")}
        </p>
        <ul className="mt-4 grid gap-1.5">
          {data.institutions.map((institution) => (
            <li key={institution.code}>
              <label className={`flex cursor-pointer items-start gap-2 text-sm ${strong}`}>
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={selected.has(institution.code)}
                  onChange={() => toggle(institution.code)}
                />
                <span>{institution.name[locale]}</span>
              </label>
            </li>
          ))}
        </ul>
        <p className={`mt-3 text-xs ${muted}`}>{t("dataNeeds.communesHint")}</p>
      </section>
    </div>
  );
}
