import type { Metadata } from "next";
import { DashboardView } from "@/components/app/DashboardView";

export const metadata: Metadata = { title: "Tableau de bord — MAJAL" };

export default function DashboardPage() {
  return <DashboardView />;
}
