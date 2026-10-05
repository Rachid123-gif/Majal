import type { Locale } from "@/content/types";

const tag = (locale: Locale) => (locale === "ar" ? "ar-MA" : "fr-FR");

/** French rules: narrow no-break space for thousands, decimal comma. */
export function formatNumber(value: number, locale: Locale, digits = 0): string {
  return new Intl.NumberFormat(tag(locale), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatDate(iso: string | null | undefined, locale: Locale): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat(tag(locale), {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(iso));
}
