"use client";

import { useLocale } from "@/i18n/LocaleProvider";
import { STATUS_STYLE, type DiagnosticData, type Status } from "@/lib/diagnostic";

/** Evaluation status: colour + symbol + words (never colour alone). */
export function StatusChip({ status, data }: { status: Status; data: DiagnosticData }) {
  const { locale } = useLocale();
  const style = STATUS_STYLE[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${style.text}`}
      style={{ background: style.color }}
    >
      <span aria-hidden>{style.symbol}</span>
      {data.evaluation.statuses[status]?.[locale] ?? status}
    </span>
  );
}
