import type { Metadata } from "next";
import { TerritoryMapView } from "@/components/app/TerritoryMapView";

export const metadata: Metadata = { title: "Carte du territoire — MAJAL" };

export default async function TerritoryPage({ params }: PageProps<"/territoire/[code]">) {
  const { code } = await params;
  return <TerritoryMapView code={code} />;
}
