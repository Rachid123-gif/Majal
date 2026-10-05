import type { Metadata } from "next";
// Fonts are bundled from npm packages, so the app works fully offline (no Google Fonts call).
import "@fontsource/eb-garamond/400.css";
import "@fontsource/eb-garamond/500.css";
import "@fontsource/eb-garamond/400-italic.css";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans-arabic/400.css";
import "@fontsource/ibm-plex-sans-arabic/500.css";
import "@fontsource/ibm-plex-sans-arabic/600.css";
import "./globals.css";
import { LocaleProvider } from "@/i18n/LocaleProvider";

export const metadata: Metadata = {
  title: "MAJAL — Copilote d'intelligence territoriale",
  description: "Démonstrateur MAJAL : diagnostics territoriaux sourcés et vérifiables.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="fr" dir="ltr" className="h-full antialiased">
      <body className="min-h-full">
        <LocaleProvider>{children}</LocaleProvider>
      </body>
    </html>
  );
}
