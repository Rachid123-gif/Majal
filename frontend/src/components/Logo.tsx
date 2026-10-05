export function Logo({
  size = "lg",
  tone = "dark",
}: {
  size?: "sm" | "lg" | "xl";
  tone?: "dark" | "light";
}) {
  const scale = {
    sm: "text-2xl gap-2",
    lg: "text-6xl sm:text-7xl gap-3",
    xl: "text-6xl sm:text-8xl gap-4",
  }[size];
  const color = tone === "dark" ? "text-petrol" : "text-cream";
  return (
    <span
      className={`font-heading ${color} ${scale} inline-flex items-baseline leading-none`}
      aria-label="MAJAL — مجال"
      dir="ltr"
    >
      <span lang="fr" className="logo-latin tracking-[0.12em]">
        MAJAL
      </span>
      <span aria-hidden className="font-normal opacity-40">
        /
      </span>
      <span lang="ar" className="font-arabic">
        مجال
      </span>
    </span>
  );
}
