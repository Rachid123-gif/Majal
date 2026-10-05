import type { Metadata } from "next";
import { UnitSheetView } from "@/components/app/UnitSheetView";

export const metadata: Metadata = { title: "Fiche — MAJAL" };

export default async function UnitPage({ params }: PageProps<"/territoire/[code]/unite/[id]">) {
  const { code, id } = await params;
  return <UnitSheetView code={code} unitId={Number(id)} />;
}
