import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginView } from "@/components/app/LoginView";

export const metadata: Metadata = { title: "Se connecter — MAJAL" };

export default function LoginPage() {
  return (
    <Suspense>
      <LoginView />
    </Suspense>
  );
}
