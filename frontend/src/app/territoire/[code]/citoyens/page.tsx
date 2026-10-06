import type { Metadata } from "next";
import { CitizensView } from "@/components/app/CitizensView";

export const metadata: Metadata = { title: "Écoute citoyenne — MAJAL" };

export default async function CitizensPage({ params }: PageProps<"/territoire/[code]/citoyens">) {
  const { code } = await params;
  return <CitizensView code={code} />;
}
