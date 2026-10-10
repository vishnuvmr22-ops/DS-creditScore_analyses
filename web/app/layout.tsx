import type { Metadata } from "next";
import { Archivo, Archivo_Narrow, IBM_Plex_Mono } from "next/font/google";
import { Shell } from "@/components/shell";
import { THEME_BOOTSTRAP } from "@/components/theme";
import { ApiProvider } from "@/lib/config";
import { resolveApiBaseUrl } from "@/lib/config-server";
import { LOCALE_BOOTSTRAP, LocaleProvider } from "@/lib/i18n";
import "./globals.css";

const archivo = Archivo({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-archivo",
  display: "swap",
});

const archivoNarrow = Archivo_Narrow({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-archivo-narrow",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "CreditSentinel — decisioning console",
  description:
    "Operator console for CreditSentinel: score an applicant, read the grounded reason, and inspect model governance, drift and the decision audit trail. Synthetic data only.",
};

// Resolve the service address per request, not at build time. Without this the
// root layout is statically prerendered and the address is frozen to its build
// -time value, defeating the one-image-any-environment contract (FR-023).
export const dynamic = "force-dynamic";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // Resolved per request, never inlined at build time (FR-023).
  const baseUrl = resolveApiBaseUrl();

  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
        <script dangerouslySetInnerHTML={{ __html: LOCALE_BOOTSTRAP }} />
      </head>
      <body className={`${archivo.variable} ${archivoNarrow.variable} ${plexMono.variable}`}>
        <ApiProvider baseUrl={baseUrl}>
          <LocaleProvider>
            <Shell>{children}</Shell>
          </LocaleProvider>
        </ApiProvider>
      </body>
    </html>
  );
}
