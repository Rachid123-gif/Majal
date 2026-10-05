import type { Metadata } from "next";
import { Suspense } from "react";
import { PresentationView } from "@/components/app/PresentationView";

export const metadata: Metadata = { title: "Mode présentation — MAJAL" };

export default function PresentationPage() {
  return (
    <Suspense>
      <PresentationView />
    </Suspense>
  );
}
