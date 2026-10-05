"use client";

import { useCallback, useEffect, useState } from "react";
import { useLocale } from "@/i18n/LocaleProvider";
import { fetchMe } from "@/lib/api";
import {
  changeReportStatus,
  exportUrl,
  fetchLlmStatus,
  fetchReport,
  fetchUnitReports,
  requestReport,
  type LlmStatus,
  type Report,
} from "@/lib/reports";

type Lang = "fr" | "ar";
const POLL_MS = 2000;

function isActive(report: Report | null) {
  return report !== null && (report.state === "pending" || report.state === "running");
}

function ModeBadge({ report }: { report: Report }) {
  const { t } = useLocale();
  if (!report.writing_mode) return null;
  const key =
    report.writing_mode === "ai"
      ? "report.modeAi"
      : report.writing_mode === "mixed"
        ? "report.modeMixed"
        : "report.modeFallback";
  const tone =
    report.writing_mode === "fallback"
      ? "bg-terracotta/10 text-terracotta-dark"
      : "bg-petrol/10 text-petrol";
  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${tone}`}>
      {t(key, { model: report.model })}
    </span>
  );
}

function ReportBody({ report }: { report: Report }) {
  const { t } = useLocale();
  const lang = report.language;
  const sections = report.content.sections ?? [];
  return (
    <article
      lang={lang}
      dir={lang === "ar" ? "rtl" : "ltr"}
      className={`mt-6 ${lang === "ar" ? "font-arabic text-lg leading-loose" : "leading-relaxed"}`}
    >
      {sections.map((section) => (
        <section key={section.code} className="mt-6 first:mt-0">
          <h3 className="font-heading text-petrol text-2xl">
            <span className="text-terracotta">{section.number}.</span> {section.title}
          </h3>
          {section.mode === "fallback" && (
            <p className="text-terracotta-dark mt-1 text-xs">
              <span aria-hidden>◆ </span>
              {t("report.sectionFallback")}
            </p>
          )}
          {section.paragraphs.map((paragraph, index) => (
            <p key={index} className="text-petrol mt-2">
              {paragraph.text}
            </p>
          ))}
          {section.code === "sources" && (
            <>
              <ul className="text-petrol mt-2 list-disc ps-6 text-sm">
                {(section.sources ?? []).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              {(section.notes ?? []).map((line) => (
                <p key={line} className="text-slate mt-2 text-xs">
                  {line}
                </p>
              ))}
            </>
          )}
        </section>
      ))}
    </article>
  );
}

export function ReportPanel({ code, unitId }: { code: string; unitId: number }) {
  const { locale, t } = useLocale();
  const [reports, setReports] = useState<Partial<Record<Lang, Report>>>({});
  const [lang, setLang] = useState<Lang>(locale);
  const [llm, setLlm] = useState<LlmStatus | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const report = reports[lang] ?? null;

  const store = useCallback((next: Report) => {
    setReports((current) => ({ ...current, [next.language]: next }));
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchUnitReports(code, unitId)
      .then((list) => !cancelled && list.forEach(store))
      .catch(() => undefined);
    fetchLlmStatus()
      .then((status) => !cancelled && setLlm(status))
      .catch(() => undefined);
    fetchMe()
      .then((me) => !cancelled && setRoles(me.roles))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [code, unitId, store]);

  // Follow a report while it is being written.
  useEffect(() => {
    if (!report || !isActive(report)) return;
    const timer = setTimeout(() => {
      fetchReport(report.id)
        .then(store)
        .catch((exc: Error) => setError(exc.message));
    }, POLL_MS);
    return () => clearTimeout(timer);
  }, [report, store]);

  const generate = (force: boolean) => {
    setError(null);
    requestReport(code, unitId, lang, force)
      .then(store)
      .catch((exc: Error) => setError(exc.message));
  };

  const setStatus = (status: Report["status"]) => {
    if (!report) return;
    setError(null);
    changeReportStatus(report.id, status)
      .then(store)
      .catch((exc: Error) => setError(exc.message));
  };

  const busy = isActive(report);
  const done = report?.state === "done";
  const canValidate = roles.includes("referent");

  return (
    <section className="border-petrol/10 mt-10 rounded-2xl border bg-white p-6 print:hidden">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="font-heading text-petrol text-3xl">{t("report.title")}</h2>
        <div role="tablist" className="bg-cream flex rounded-lg p-1 text-sm">
          {(["fr", "ar"] as const).map((l) => (
            <button
              key={l}
              role="tab"
              aria-selected={lang === l}
              onClick={() => setLang(l)}
              className={`rounded-md px-3 py-1 ${lang === l ? "text-petrol bg-white shadow-sm" : "text-slate"}`}
            >
              {l === "fr" ? t("report.french") : t("report.arabic")}
            </button>
          ))}
        </div>
      </div>

      {llm && (
        <p className="text-slate mt-2 text-xs">
          {llm.sovereign_mode && (
            <>
              <span aria-hidden>● </span>
              {t("report.sovereign")}
            </>
          )}
          {!llm.reachable && <span className="text-terracotta-dark"> · {t("report.aiOff")}</span>}
        </p>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          onClick={() => generate(false)}
          disabled={busy}
          className="bg-petrol text-cream hover:bg-petrol/90 rounded-lg px-5 py-2.5 text-sm font-medium disabled:opacity-50"
        >
          {t("report.generate")} {lang === "fr" ? t("report.french") : t("report.arabic")}
        </button>
        {report && !busy && (
          <button
            onClick={() => generate(true)}
            className="border-petrol/30 text-petrol hover:bg-petrol/5 rounded-lg border px-4 py-2 text-sm"
          >
            {t("report.regenerate")}
          </button>
        )}
      </div>

      {error && (
        <p
          role="alert"
          className="bg-terracotta/10 text-terracotta-dark mt-4 rounded-xl p-3 text-sm"
        >
          {error}
        </p>
      )}

      {busy && report && (
        <div className="mt-6" aria-live="polite">
          <p className="text-petrol text-sm font-medium">{t("report.running")}</p>
          <p className="text-slate mt-1 text-sm">
            {report.progress.section && report.progress.total
              ? t("report.section", {
                  n: String(report.progress.section),
                  total: String(report.progress.total),
                  title: report.progress.title ?? "",
                })
              : t("report.pending")}
          </p>
          <div className="bg-cream mt-3 h-2 overflow-hidden rounded-full">
            <div
              className="bg-terracotta h-full transition-all"
              style={{
                width: `${report.progress.total ? ((report.progress.section ?? 0) / report.progress.total) * 100 : 5}%`,
              }}
            />
          </div>
        </div>
      )}

      {report?.state === "failed" && (
        <p
          role="alert"
          className="bg-terracotta/10 text-terracotta-dark mt-4 rounded-xl p-3 text-sm"
        >
          {t("report.failed")} {report.error}
        </p>
      )}

      {report && (report.state === "done" || report.state === "blocked") && (
        <div className="mt-6">
          <div className="flex flex-wrap items-center gap-2">
            <ModeBadge report={report} />
            {report.cached && report.finished_at && (
              <span className="text-slate text-xs">
                {t("report.cached", {
                  date: new Date(report.finished_at).toLocaleDateString(
                    locale === "ar" ? "ar-MA-u-nu-latn" : "fr-FR",
                  ),
                })}
              </span>
            )}
            {report.duration_s != null && (
              <span className="text-slate text-xs">
                · {t("report.duration", { s: String(Math.round(report.duration_s)) })}
              </span>
            )}
          </div>

          {report.outdated && (
            <p className="bg-cream text-petrol mt-4 rounded-xl p-3 text-sm">
              <span aria-hidden>↻ </span>
              {t("report.outdated")}
            </p>
          )}

          {report.state === "blocked" && (
            <div
              role="alert"
              className="bg-terracotta/10 text-terracotta-dark mt-4 rounded-xl p-3 text-sm"
            >
              <p className="font-medium">{t("report.blocked")}</p>
              <ul className="mt-1 list-disc ps-5 text-xs">
                {(report.content.verification?.issues ?? []).map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            </div>
          )}

          {report.status !== "valide" && (
            <p className="border-terracotta/40 text-terracotta-dark mt-4 rounded-lg border border-dashed px-3 py-2 text-center text-xs font-medium">
              {t("report.watermark")}
            </p>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
            <span className="text-slate">{t("report.status")} :</span>
            <span className="bg-petrol/10 text-petrol rounded-full px-3 py-1 text-xs font-medium">
              {t(`report.statuses.${report.status}`)}
            </span>
            {done && report.status === "brouillon" && (
              <button onClick={() => setStatus("relu")} className="text-petrol underline">
                {t("report.markRead")}
              </button>
            )}
            {done && report.status !== "valide" && canValidate && (
              <button onClick={() => setStatus("valide")} className="text-petrol underline">
                {t("report.validate")}
              </button>
            )}
            {done && report.status !== "brouillon" && (
              <button onClick={() => setStatus("brouillon")} className="text-slate underline">
                {t("report.backToDraft")}
              </button>
            )}
          </div>

          {done && (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              {report.language === "fr" ? (
                <>
                  <a
                    href={exportUrl(report.id, "docx")}
                    className="border-petrol/30 text-petrol hover:bg-petrol/5 rounded-lg border px-4 py-2 text-sm"
                  >
                    {t("report.downloadDocx")}
                  </a>
                  <a
                    href={exportUrl(report.id, "pdf")}
                    className="border-petrol/30 text-petrol hover:bg-petrol/5 rounded-lg border px-4 py-2 text-sm"
                  >
                    {t("report.downloadPdf")}
                  </a>
                </>
              ) : (
                <p className="text-slate text-xs">{t("report.arabicExports")}</p>
              )}
            </div>
          )}

          <ReportBody report={report} />
        </div>
      )}

      {!report && !busy && <p className="text-slate mt-4 text-sm">{t("report.noReport")}</p>}
    </section>
  );
}
