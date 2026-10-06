"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/app/AppHeader";
import { CitizenBanner } from "@/components/app/CitizenBanner";
import { useLocale } from "@/i18n/LocaleProvider";
import {
  fetchReview,
  saveReview,
  type ReviewChoice,
  type ReviewItem,
  type ReviewQueue,
} from "@/lib/citizens";

const RTL_LANGUAGES = new Set(["ar", "darija_ar"]);
const select = "border-petrol/20 rounded-lg border bg-white px-2 py-1.5 text-sm";

function ReviewCard({
  code,
  item,
  queue,
  onSaved,
}: {
  code: string;
  item: ReviewItem;
  queue: ReviewQueue;
  onSaved: (saved: ReviewItem) => void;
}) {
  const { locale, t } = useLocale();
  const [main, setMain] = useState(item.current.themes[0] ?? "autres");
  const [second, setSecond] = useState(item.current.themes[1] ?? "");
  const [tonality, setTonality] = useState(item.current.tonality);
  const [unit, setUnit] = useState<number | null>(item.current.unit?.id ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const rtl = RTL_LANGUAGES.has(item.language);
  const themeLabel = (c: string) => queue.themes.find((th) => th.code === c)?.label[locale] ?? c;
  const unitName = (u: { name_fr: string; name_ar: string | null } | null) =>
    u ? (locale === "ar" && u.name_ar) || u.name_fr : t("citizens.notLocated");

  const save = (choice: ReviewChoice) => {
    setBusy(true);
    setError(null);
    saveReview(code, item.id, choice)
      .then(onSaved)
      .catch((exc: Error) => setError(exc.message))
      .finally(() => setBusy(false));
  };
  const proposal: ReviewChoice = {
    themes: item.proposal.themes,
    tonality: item.proposal.tonality,
    territory_id: item.proposal.unit?.id ?? null,
  };

  return (
    <article className="border-petrol/10 rounded-2xl border bg-white p-5 text-sm">
      <div className="text-slate flex flex-wrap items-center gap-2 text-xs">
        <span className="text-petrol font-medium">{item.external_id}</span>
        {item.reasons.map((r) => (
          <span key={r.code} className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-900">
            ? {r.label[locale]}
          </span>
        ))}
        {item.validated_by && (
          <span className="bg-petrol/10 text-petrol rounded-full px-2 py-0.5">
            ✓ {t("citizens.validatedBy", { by: item.validated_by })}
          </span>
        )}
      </div>

      <div className={`mt-3 grid gap-3 ${item.translation_fr ? "md:grid-cols-2" : ""}`}>
        <blockquote>
          <p className="text-slate text-[11px] font-medium uppercase tracking-wide">
            {t("citizens.original")}
          </p>
          <p
            lang={rtl ? "ar" : undefined}
            dir={rtl ? "rtl" : "ltr"}
            className={`text-petrol mt-1 ${rtl ? "font-arabic text-base" : ""}`}
          >
            {item.original}
          </p>
          {item.language_note && (
            <p className="text-terracotta-dark mt-1 text-[11px]">{item.language_note[locale]}</p>
          )}
        </blockquote>
        {item.translation_fr && (
          <div>
            <p className="text-slate text-[11px] font-medium uppercase tracking-wide">
              {t("citizens.translation")} — {item.translation_note?.[locale]}
            </p>
            <p lang="fr" dir="ltr" className="text-petrol mt-1">
              {item.translation_fr}
            </p>
          </div>
        )}
      </div>

      <div className="bg-cream/60 mt-4 rounded-xl p-3 text-xs">
        <p className="text-petrol font-medium">{t("citizens.proposal")}</p>
        <p className="text-slate mt-1">
          {item.proposal.themes.map(themeLabel).join(" + ")} ·{" "}
          {queue.tonalities[item.proposal.tonality]?.[locale] ?? item.proposal.tonality} ·{" "}
          {unitName(item.proposal.unit)}
          {item.proposal.place ? ` (${item.proposal.place})` : ""}
        </p>
        {item.keywords.themes && (
          <p className="text-slate mt-1">
            {t("citizens.keywordsSaid", {
              themes: item.keywords.themes.map(themeLabel).join(" + "),
            })}
          </p>
        )}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="text-slate grid gap-1 text-xs">
          {t("citizens.reviewMainTheme")}
          <select className={select} value={main} onChange={(e) => setMain(e.target.value)}>
            {queue.themes.map((th) => (
              <option key={th.code} value={th.code}>
                {th.label[locale]}
              </option>
            ))}
          </select>
        </label>
        <label className="text-slate grid gap-1 text-xs">
          {t("citizens.reviewSecondTheme")}
          <select className={select} value={second} onChange={(e) => setSecond(e.target.value)}>
            <option value="">{t("citizens.reviewNone")}</option>
            {queue.themes
              .filter((th) => th.code !== main)
              .map((th) => (
                <option key={th.code} value={th.code}>
                  {th.label[locale]}
                </option>
              ))}
          </select>
        </label>
        <fieldset className="text-slate grid gap-1 text-xs">
          <legend>{t("citizens.reviewTonality")}</legend>
          <div className="flex flex-wrap gap-1">
            {Object.entries(queue.tonalities).map(([key, value]) => (
              <button
                key={key}
                type="button"
                aria-pressed={tonality === key}
                onClick={() => setTonality(key)}
                className={`rounded-full border px-2 py-1 ${
                  tonality === key
                    ? "border-petrol bg-petrol text-white"
                    : "border-petrol/20 text-petrol bg-white"
                }`}
              >
                {value[locale]}
              </button>
            ))}
          </div>
        </fieldset>
        <label className="text-slate grid gap-1 text-xs">
          {t("citizens.unitField")}
          <select
            className={select}
            value={unit ?? ""}
            onChange={(e) => setUnit(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">{t("citizens.notLocated")}</option>
            {queue.units.map((u) => (
              <option key={u.id} value={u.id}>
                {unitName(u)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => save(proposal)}
          className="border-petrol text-petrol rounded-full border px-4 py-1.5 text-sm disabled:opacity-50"
        >
          ✓ {t("citizens.confirm")}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            save({ themes: second ? [main, second] : [main], tonality, territory_id: unit })
          }
          className="bg-petrol rounded-full px-4 py-1.5 text-sm text-white disabled:opacity-50"
        >
          {t("citizens.saveCorrection")}
        </button>
      </div>
      {error && (
        <p role="alert" className="text-terracotta-dark mt-2 text-xs">
          {error}
        </p>
      )}
    </article>
  );
}

/** « À vérifier »: the tool proposes, the urban planner validates (professor and admin only). */
export function ReviewView({ code }: { code: string }) {
  const { t } = useLocale();
  const [status, setStatus] = useState<"pending" | "validated">("pending");
  const [queue, setQueue] = useState<ReviewQueue | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchReview(code, status)
      .then((q) => {
        if (!cancelled) {
          setQueue(q);
          setError(null);
        }
      })
      .catch((exc: Error) => !cancelled && setError(exc.message));
    return () => {
      cancelled = true;
    };
  }, [code, status]);

  const onSaved = (saved: ReviewItem) => {
    setMessage(t("citizens.saved", { by: saved.validated_by ?? "" }));
    setQueue((q) => {
      if (!q) return q;
      const wasPending = q.status === "pending";
      return {
        ...q,
        counts: wasPending
          ? { pending: q.counts.pending - 1, validated: q.counts.validated + 1 }
          : q.counts,
        items: wasPending
          ? q.items.filter((i) => i.id !== saved.id)
          : q.items.map((i) => (i.id === saved.id ? saved : i)),
      };
    });
  };

  const tab = (value: "pending" | "validated", text: string) => (
    <button
      type="button"
      role="tab"
      aria-selected={status === value}
      onClick={() => {
        setMessage(null);
        setStatus(value);
      }}
      className={`rounded-full px-4 py-1.5 text-sm ${
        status === value ? "bg-petrol text-white" : "text-petrol border-petrol/20 border bg-white"
      }`}
    >
      {text}
    </button>
  );

  return (
    <div className="min-h-screen">
      <AppHeader territory={code} />
      <main className="mx-auto max-w-5xl px-5 py-8 sm:px-8">
        <Link
          href={`/territoire/${code}/citoyens`}
          className="text-slate hover:text-petrol text-sm"
        >
          <span aria-hidden className="inline-block rtl:rotate-180">
            ←
          </span>{" "}
          {t("citizens.backToDashboard")}
        </Link>
        <h1 className="font-heading text-petrol mt-3 text-5xl">{t("citizens.reviewTitle")}</h1>
        <p className="text-slate mt-2 max-w-3xl text-sm">{t("citizens.reviewIntro")}</p>
        {queue?.banner && (
          <div className="mt-4">
            <CitizenBanner text={queue.banner} />
          </div>
        )}
        {error && (
          <p role="alert" className="bg-terracotta/10 text-terracotta-dark mt-6 rounded-xl p-4">
            {error}
          </p>
        )}
        {queue && (
          <>
            <div role="tablist" className="mt-6 flex flex-wrap gap-2">
              {tab("pending", t("citizens.reviewPending", { n: String(queue.counts.pending) }))}
              {tab("validated", t("citizens.reviewDone", { n: String(queue.counts.validated) }))}
            </div>
            {message && (
              <p role="status" className="text-petrol mt-3 text-sm">
                ✓ {message}
              </p>
            )}
            {queue.items.length === 0 && (
              <p className="text-slate mt-6">{t("citizens.reviewEmpty")}</p>
            )}
            <div className="mt-6 grid gap-4">
              {queue.items.map((item) => (
                <ReviewCard
                  key={`${item.id}-${item.validated_at ?? ""}`}
                  code={code}
                  item={item}
                  queue={queue}
                  onSaved={onSaved}
                />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
