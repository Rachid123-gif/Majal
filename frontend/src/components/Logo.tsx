export function Logo({ size = "lg" }: { size?: "sm" | "lg" }) {
  const scale = size === "lg" ? "text-6xl sm:text-7xl" : "text-2xl";
  return (
    <span
      className={`font-heading text-petrol ${scale} inline-flex items-baseline gap-3 leading-none`}
      aria-label="MAJAL — مجال"
    >
      <span lang="fr" dir="ltr" className="logo-latin tracking-[0.12em]">
        MAJAL
      </span>
      <span aria-hidden className="text-petrol/40 font-normal">
        /
      </span>
      <span lang="ar" dir="rtl" className="font-arabic">
        مجال
      </span>
    </span>
  );
}
