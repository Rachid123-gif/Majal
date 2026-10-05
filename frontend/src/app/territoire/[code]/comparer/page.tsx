import type { Metadata } from "next";
import { Suspense } from "react";
import { CompareView } from "@/components/app/CompareView";

export const metadata: Metadata = { title: "Comparaison — MAJAL" };

export default async function ComparePage({ params }: PageProps<"/territoire/[code]/comparer">) {
  const { code } = await params;
  return (
    <Suspense>
      <CompareView code={code} />
    </Suspense>
  );
}
