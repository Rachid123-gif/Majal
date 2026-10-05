"use client";

import { useLocale } from "@/i18n/LocaleProvider";

export type BadgeKind = "official" | "open" | "estimated" | "fictitious";

const STYLES: Record<BadgeKind, { className: string; symbol: string }> = {
  official: { className: "bg-petrol text-cream", symbol: "◆" },
  open: { className: "bg-sea text-petrol border border-petrol/20", symbol: "●" },
  estimated: { className: "bg-land text-petrol border border-petrol/20", symbol: "≈" },
  fictitious: { className: "bg-terracotta/15 text-terracotta-dark", symbol: "!" },
};

/** Confidence badge: the level is given by text and symbol, never by colour alone. */
export function ConfidenceBadge({ kind }: { kind: BadgeKind }) {
  const { t } = useLocale();
  const style = STYLES[kind] ?? STYLES.open;
  return (
    <span
      title={t(`badge.help.${kind}`)}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${style.className}`}
    >
      <span aria-hidden>{style.symbol}</span>
      {t(`badge.${kind}`)}
    </span>
  );
}
