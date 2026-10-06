"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CitizenBanner } from "@/components/app/CitizenBanner";
import { CitizenCrossing } from "@/components/app/CitizenCrossing";
import { VerbatimCard } from "@/components/app/CitizensView";
import { useLocale } from "@/i18n/LocaleProvider";
import { fetchUnitCitizens, percent, type UnitCitizens } from "@/lib/citizens";

/** « Ce que disent les citoyens » on the unit sheet: main themes only, two verbatims. */
export function CitizenUnitCard({ code, unitId }: { code: string; unitId: number }) {
  const { locale, t } = useLocale();
  const [data, setData] = useState<UnitCitizens | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchUnitCitizens(code, unitId)
      .then((d) => !cancelled && setData(d))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [code, unitId]);

  if (!data) return null;
  const { summary } = data;
  return (
    <section className="border-petrol/10 mt-10 rounded-2xl border bg-white p-6">
      <h2 className="font-heading text-petrol text-3xl">{t("citizens.unitTitle")}</h2>
      {data.banner && (
        <div className="mt-3">
          <CitizenBanner text={data.banner} compact />
        </div>
      )}
      {summary.total === 0 ? (
        <p className="text-slate mt-4 text-sm">{t("citizens.unitNone")}</p>
      ) : (
        <>
          <p className="text-petrol mt-4 text-sm">
            {t("citizens.count", { n: String(summary.total) })}
            {summary.total < summary.rules.min_contributions && ` — ${t("citizens.tooFew")}`}
          </p>
          <ul className="text-petrol mt-2 flex flex-wrap gap-2 text-xs">
            {summary.themes.map((th) => (
              <li key={th.code} className="bg-cream rounded-full px-3 py-1">
                {th.label[locale]} : {th.count}
                {percent(th.share) ? ` (${percent(th.share)})` : ""}
              </li>
            ))}
          </ul>
          <div className="mt-4 grid gap-3">
            {data.verbatims.map((v) => (
              <VerbatimCard key={v.id} verbatim={v} />
            ))}
          </div>
        </>
      )}
      <div className="mt-6">
        <CitizenCrossing code={code} unitId={unitId} />
      </div>
      <Link
        href={`/territoire/${code}/citoyens`}
        className="text-petrol mt-4 inline-block text-sm underline"
      >
        {t("citizens.seeAll")}
      </Link>
    </section>
  );
}
