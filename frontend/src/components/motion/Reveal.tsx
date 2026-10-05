"use client";

import type { ElementType, ReactNode } from "react";
import { useInView } from "./useInView";

/** Fades and lifts its content in when it scrolls into view (disabled by reduced motion in CSS). */
export function Reveal({
  children,
  as: Tag = "div",
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  as?: ElementType;
  delay?: number;
  className?: string;
}) {
  const { ref, inView } = useInView<HTMLElement>();
  return (
    <Tag
      ref={ref}
      data-reveal={inView ? "in" : "out"}
      style={{ transitionDelay: `${delay}ms` }}
      className={className}
    >
      {children}
    </Tag>
  );
}
