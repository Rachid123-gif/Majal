"use client";

import type { Localized } from "@/content/types";
import { useLocale } from "@/i18n/LocaleProvider";

/** Permanent notice on every screen that shows fictitious contributions (rule of the owner). */
export function CitizenBanner({ text, compact = false }: { text: Localized; compact?: boolean }) {
  const { locale } = useLocale();
  return (
    <div
      role="note"
      className={`border-terracotta bg-terracotta/10 text-terracotta-dark rounded-xl border-2 border-dashed font-medium ${
        compact ? "px-3 py-2 text-xs" : "px-4 py-3 text-sm"
      }`}
    >
      <span aria-hidden>◆ </span>
      {text[locale]}
    </div>
  );
}
