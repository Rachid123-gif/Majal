"use client";

import type { DiagnosticData } from "@/lib/diagnostic";
import { useLocale } from "@/i18n/LocaleProvider";

/** Mandatory notices: provisional grid, and relative evaluation without official norm. */
export function GridBanner({ data, compact = false }: { data: DiagnosticData; compact?: boolean }) {
  const { locale } = useLocale();
  return (
    <div
      role="note"
      className={`border-terracotta/30 bg-terracotta/5 text-petrol rounded-xl border ${
        compact ? "px-3 py-2 text-xs" : "px-4 py-3 text-sm"
      }`}
    >
      <p className="font-medium">
        <span aria-hidden className="text-terracotta">
          ◆{" "}
        </span>
        {data.grid.label[locale]}
      </p>
      <p className="text-slate mt-0.5">{data.evaluation.label[locale]}</p>
    </div>
  );
}
