import type { Metadata } from "next";
import { DataNeedsView } from "@/components/app/DataNeedsView";

export const metadata: Metadata = { title: "Besoins en données — MAJAL" };

export default async function DataNeedsPage({
  params,
}: PageProps<"/territoire/[code]/besoins-donnees">) {
  const { code } = await params;
  return <DataNeedsView code={code} />;
}
