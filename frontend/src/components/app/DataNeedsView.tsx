"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/app/AppHeader";
import { DataNeedsSimulator } from "@/components/app/DataNeedsSimulator";
import { useLocale } from "@/i18n/LocaleProvider";
import { fetchMe } from "@/lib/api";
import {
  fetchDataNeeds,
  saveTracking,
  type DataNeeds,
  type DataRequestRow,
  type InstitutionRow,
  type Tracking,
} from "@/lib/dataNeeds";

const PRIORITY_TONE: Record<string, string> = {
  essential: "bg-terracotta/15 text-terracotta-dark",
  useful: "bg-petrol/10 text-petrol",
  context: "bg-cream text-slate",
};

function EffectsText({ request, data }: { request: DataRequestRow; data: DataNeeds }) {
  const { locale, t } = useLocale();
  const parts: string[] = [];
  for (const key of ["computed", "reliable", "finer"] as const) {
    const n = request.effects[key].length;
    if (!n) continue;
    const scale =
      key === "finer" && request.finer_scale
        ? locale === "fr"
          ? ` à l'échelle ${request.finer_scale.fr}`
          : ` على مستوى ${request.finer_scale.ar}`
        : "";
    parts.push(`${data.effects[key].verb[locale]} ${n}${scale}`);
  }
  if (request.themes.length)
    parts.push(t("dataNeeds.themesCount", { n: String(request.themes.length) }));
  if (request.context) parts.push(t("dataNeeds.contextEffect"));
  return <>{parts.join(" · ")}</>;
}

function TrackingControl({
  code,
  institution,
  statuses,
  canEdit,
}: {
  code: string;
  institution: InstitutionRow;
  statuses: DataNeeds["tracking_statuses"];
  canEdit: boolean;
}) {
  const { locale, t } = useLocale();
  const [tracking, setTracking] = useState<Tracking>(institution.tracking);
  const [status, setStatus] = useState(tracking.status);
  const [date, setDate] = useState(tracking.date ?? new Date().toISOString().slice(0, 10));
  const [error, setError] = useState<string | null>(null);
  const label = statuses[tracking.status]?.[locale] ?? tracking.status;
  if (!canEdit) {
    return (
      <p className="text-petrol text-sm">
        {label}
        {tracking.date ? ` · ${tracking.date}` : ""}
      </p>
    );
  }
  return (
    <div className="flex flex-wrap items-end gap-2 text-sm">
      <label className="text-slate grid gap-1 text-xs">
        {t("dataNeeds.tracking")}
        <select
          className="border-petrol/20 rounded-lg border bg-white px-2 py-1 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          {Object.entries(statuses).map(([key, value]) => (
            <option key={key} value={key}>
              {value[locale]}
            </option>
          ))}
        </select>
      </label>
      <label className="text-slate grid gap-1 text-xs">
        {t("dataNeeds.trackingDate")}
        <input
          type="date"
          className="border-petrol/20 rounded-lg border bg-white px-2 py-1 text-sm"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </label>
      <button
        type="button"
        onClick={() =>
          saveTracking(code, institution.code, status, date)
            .then((saved) => {
              setTracking(saved);
              setError(null);
            })
            .catch((exc: Error) => setError(exc.message))
        }
        className="bg-petrol rounded-full px-3 py-1 text-white"
      >
        {t("dataNeeds.trackingSave")}
      </button>
      {tracking.updated_by && (
        <span className="text-slate text-xs">
          {label} · {tracking.date} · {t("dataNeeds.trackingBy", { by: tracking.updated_by })}
        </span>
      )}
      {error && (
        <span role="alert" className="text-terracotta-dark text-xs">
          {error}
        </span>
      )}
    </div>
  );
}

/** « Ce que MAJAL pourrait faire avec vos données » (module « Besoins en données », stage 5). */
export function DataNeedsView({ code }: { code: string }) {
  const { locale, t } = useLocale();
  const [data, setData] = useState<DataNeeds | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [roles, setRoles] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetchDataNeeds(code)
      .then((d) => !cancelled && setData(d))
      .catch((exc: Error) => !cancelled && setError(exc.message));
    fetchMe()
      .then((me) => !cancelled && setRoles(me.roles))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [code]);

  const canEdit = roles.includes("referent") || roles.includes("admin");
  const name = (institution: string) =>
    data?.institutions.find((i) => i.code === institution)?.name[locale] ?? institution;
  const requestsOf = (institution: InstitutionRow) =>
    data?.requests.filter((r) => institution.requests.includes(r.code)) ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader territory={code} />
      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <h1 className="font-heading text-petrol text-5xl">{t("dataNeeds.title")}</h1>
        <p className="text-slate mt-3 max-w-3xl">{t("dataNeeds.intro")}</p>
        {data && (
          <p className="bg-cream text-petrol mt-4 inline-block rounded-full px-3 py-1 text-xs">
            {data.label[locale]}
          </p>
        )}
        {error && (
          <p role="alert" className="bg-terracotta/10 text-terracotta-dark mt-6 rounded-xl p-4">
            {error}
          </p>
        )}
        {data && (
          <>
            <div className="mt-8">
              <DataNeedsSimulator data={data} />
            </div>

            <section className="mt-12" aria-labelledby="start-title">
              <h2 id="start-title" className="font-heading text-petrol text-3xl">
                {t("dataNeeds.startTitle")}
              </h2>
              <p className="text-slate mt-2 text-sm">{t("dataNeeds.startIntro")}</p>
              <div className="border-petrol/10 mt-4 overflow-x-auto rounded-2xl border bg-white">
                <table className="w-full text-sm">
                  <thead className="text-slate text-xs">
                    <tr className="border-petrol/10 border-b">
                      <th className="px-3 py-2 text-start font-normal">#</th>
                      <th className="px-3 py-2 text-start font-normal">
                        {t("dataNeeds.priority")}
                      </th>
                      <th className="px-3 py-2 text-start font-normal">{t("dataNeeds.request")}</th>
                      <th className="px-3 py-2 text-start font-normal">
                        {t("dataNeeds.effectsCol")}
                      </th>
                      <th className="px-3 py-2 text-start font-normal">{t("dataNeeds.holders")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.requests.map((request, index) => (
                      <tr key={request.code} className="border-petrol/5 border-b align-top">
                        <td className="text-slate px-3 py-2 tabular-nums">{index + 1}</td>
                        <td className="px-3 py-2">
                          <span
                            className={`inline-block rounded-full px-2 py-0.5 text-xs ${PRIORITY_TONE[request.priority] ?? ""}`}
                          >
                            {request.priority_label[locale]}
                          </span>
                        </td>
                        <td className="text-petrol px-3 py-2">{request.data[locale]}</td>
                        <td className="text-petrol px-3 py-2">
                          <EffectsText request={request} data={data} />
                          {request.requires_also.length > 0 && (
                            <span className="text-slate block text-xs">
                              {t("dataNeeds.requiresAlso", {
                                names: request.requires_also
                                  .flatMap(
                                    (c) => data.requests.find((r) => r.code === c)?.holders ?? [],
                                  )
                                  .map(name)
                                  .join(", "),
                              })}
                            </span>
                          )}
                        </td>
                        <td className="text-slate px-3 py-2 text-xs">
                          {request.holders.map(name).join(" ; ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="mt-12" aria-labelledby="institutions-title">
              <h2 id="institutions-title" className="font-heading text-petrol text-3xl">
                {t("dataNeeds.institutionsTitle")}
              </h2>
              <div className="mt-4 grid gap-4">
                {data.institutions.map((institution) => (
                  <article
                    key={institution.code}
                    className="border-petrol/10 rounded-2xl border bg-white p-5"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      {institution.priority_label && (
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs ${PRIORITY_TONE[institution.priority ?? ""] ?? ""}`}
                        >
                          {institution.priority_label[locale]}
                        </span>
                      )}
                      <h3 className="text-petrol font-semibold">{institution.name[locale]}</h3>
                    </div>
                    {institution.to_verify && (
                      <p className="text-terracotta-dark mt-1 text-xs">
                        ⚠ {t("dataNeeds.toVerify")}
                      </p>
                    )}
                    <p className="text-petrol mt-3">{institution.sentence[locale]}</p>
                    <ul className="mt-3 grid gap-2 text-sm">
                      {requestsOf(institution).map((request) => (
                        <li key={request.code} className="bg-cream/50 rounded-xl p-3">
                          <p className="text-petrol font-medium">{request.data[locale]}</p>
                          <p className="text-slate mt-1 text-xs">
                            {t("dataNeeds.detail")} : {request.detail[locale]} ·{" "}
                            {t("dataNeeds.format")} : {request.format[locale]} ·{" "}
                            {t("dataNeeds.frequency")} : {request.frequency[locale]}
                          </p>
                          <p className="text-slate mt-1 text-xs">
                            {t("dataNeeds.value")} : {request.value[locale]}
                          </p>
                          {request.complementary.length > 0 && (
                            <p className="text-slate mt-1 text-xs">
                              {t("dataNeeds.complementary")} :{" "}
                              {request.complementary.map(name).join(" ; ")}
                            </p>
                          )}
                          {request.alternatives.length > 0 && (
                            <p className="text-slate mt-1 text-xs">
                              {t("dataNeeds.alternatives")} :{" "}
                              {request.alternatives.map(name).join(" ; ")}
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                    <div className="mt-4 flex flex-wrap items-end justify-between gap-3">
                      <TrackingControl
                        code={code}
                        institution={institution}
                        statuses={data.tracking_statuses}
                        canEdit={canEdit}
                      />
                      <div className="flex flex-wrap items-center gap-2 text-sm">
                        <span className="text-slate text-xs">{t("dataNeeds.generateNote")}</span>
                        {(["docx", "pdf"] as const).map((fmt) => (
                          <a
                            key={fmt}
                            href={`/api/territories/${code}/data-needs/institutions/${institution.code}/note.${fmt}`}
                            className="border-petrol text-petrol hover:bg-petrol rounded-full border px-3 py-1 hover:text-white"
                          >
                            {fmt === "docx" ? "Word" : "PDF"}
                          </a>
                        ))}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
