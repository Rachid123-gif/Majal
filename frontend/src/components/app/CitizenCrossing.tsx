"use client";

import { useEffect, useState } from "react";
import { CitizenBanner } from "@/components/app/CitizenBanner";
import { useLocale } from "@/i18n/LocaleProvider";
import { fetchCrossing, percent, type Crossing } from "@/lib/citizens";
import { formatNumber } from "@/lib/format";

const VERDICT_TONE: Record<string, string> = {
  convergence: "bg-terracotta/15 text-terracotta-dark",
  demand_only: "bg-petrol/10 text-petrol",
  data_only: "bg-amber-100 text-amber-900",
  moderate: "bg-cream text-slate",
  too_few: "bg-cream text-slate",
  no_indicator: "bg-cream text-petrol",
  no_indicator_planned: "bg-cream text-slate",
};

/** « Ce que disent les citoyens / ce que montrent les données » for one unit. */
export function CitizenCrossing({ code, unitId }: { code: string; unitId: number }) {
  const { locale, t } = useLocale();
  const [secondary, setSecondary] = useState(false);
  const [data, setData] = useState<Crossing | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCrossing(code, unitId, secondary)
      .then((d) => !cancelled && setData(d))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [code, unitId, secondary]);

  if (!data) return null;
  return (
    <div>
      <h3 className="font-heading text-petrol text-2xl">{t("citizens.crossing")}</h3>
      <p className="text-slate mt-1 text-xs">
        {t("citizens.crossingRules", {
          min: String(data.rules.min_contributions),
          pct: String(data.rules.percent_min_total),
        })}{" "}
        {data.evaluation_label[locale]}
      </p>
      {data.banner && (
        <div className="mt-2">
          <CitizenBanner text={data.banner} compact />
        </div>
      )}
      <label className="text-petrol mt-3 flex items-center gap-2 text-xs">
        <input
          type="checkbox"
          checked={secondary}
          onChange={(e) => setSecondary(e.target.checked)}
        />
        {t("citizens.secondary")}
      </label>
      {data.secondary_note && (
        <p className="text-terracotta-dark mt-1 text-xs">⚠ {data.secondary_note[locale]}</p>
      )}
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-slate border-petrol/10 border-b text-start">
              <th className="py-2 text-start font-normal">{t("citizens.theme")}</th>
              <th className="py-2 text-start font-normal">{t("citizens.total")}</th>
              <th className="py-2 text-start font-normal">{t("citizens.data")}</th>
              <th className="py-2 text-start font-normal">{t("citizens.verdict")}</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row) => (
              <tr key={row.theme} className="border-petrol/10 border-b align-top last:border-0">
                <td className="text-petrol py-2 pe-3 font-medium">{row.label[locale]}</td>
                <td className="text-petrol py-2 pe-3 tabular-nums">
                  {row.count}
                  {percent(row.share) ? ` (${percent(row.share)})` : ""}
                </td>
                <td className="py-2 pe-3">
                  {row.indicators.length > 0 ? (
                    <ul className="space-y-1">
                      {row.indicators.map((ind) => (
                        <li key={ind.code} className="text-slate">
                          {ind.label?.[locale] ?? ind.code} :{" "}
                          <span className="text-petrol tabular-nums">
                            {ind.value === null
                              ? t("badge.not_available")
                              : `${formatNumber(ind.value, locale, ind.decimals)} ${ind.unit?.[locale] ?? ""}`}
                          </span>
                          {ind.status_label && <> — {ind.status_label[locale]}</>}
                        </li>
                      ))}
                    </ul>
                  ) : row.data_request ? (
                    <span className="text-slate">
                      {row.data_request.data[locale]} —{" "}
                      <span className="text-petrol">
                        {t("citizens.askTo")} {row.data_request.holder[locale]}
                      </span>
                    </span>
                  ) : (
                    <span className="text-slate">—</span>
                  )}
                </td>
                <td className="py-2">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 ${VERDICT_TONE[row.verdict] ?? ""}`}
                  >
                    {row.verdict_label?.[locale] ?? row.verdict}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
