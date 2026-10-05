"use client";

import { useEffect, useState } from "react";
import { useInView } from "./useInView";
import { useReducedMotion } from "./useReducedMotion";

const DURATION_MS = 1600;

/** Counts from 0 to `value` when visible. Server render and reduced motion show the final value. */
export function CountUp({ value, locale }: { value: number; locale: string }) {
  const { ref, inView } = useInView<HTMLSpanElement>();
  const reduced = useReducedMotion();
  const [current, setCurrent] = useState<number | null>(null);

  useEffect(() => {
    if (!inView || reduced) return;
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / DURATION_MS);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(Math.round(eased * value));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [inView, reduced, value]);

  const shown = current ?? value;
  return (
    <span ref={ref} aria-label={String(value)}>
      <span aria-hidden>{shown.toLocaleString(locale === "ar" ? "fr-MA" : "fr-FR")}</span>
    </span>
  );
}
