import type { Metadata } from "next";
import { ReviewView } from "@/components/app/ReviewView";

export const metadata: Metadata = { title: "À vérifier — MAJAL" };

export default async function ReviewPage({
  params,
}: PageProps<"/territoire/[code]/citoyens/verifier">) {
  const { code } = await params;
  return <ReviewView code={code} />;
}
