"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { createContext, useContext, type ReactNode } from "react";
import { useApi } from "@/lib/config";
import { useT } from "@/lib/i18n";
import { useResource } from "@/lib/use-resource";
import type { Health } from "@/lib/types";
import { AppearanceToggle } from "./theme";
import { LanguageToggle } from "./language";

const DESTINATIONS = [
  { href: "/", key: "nav.decisioning" },
  { href: "/governance", key: "nav.governance" },
  { href: "/drift", key: "nav.drift" },
  { href: "/audit", key: "nav.audit" },
];

interface HealthState {
  health: Health | null;
  reachable: boolean;
  loading: boolean;
  reload: () => void;
}

const HealthContext = createContext<HealthState>({
  health: null,
  reachable: false,
  loading: true,
  reload: () => {},
});

export function useHealth() {
  return useContext(HealthContext);
}

/** The identity mark is the determination scale itself, at its smallest. */
function Mark() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden focusable="false">
      <rect x="0" y="2" width="16" height="3" fill="var(--color-approve)" />
      <rect x="0" y="6.5" width="16" height="3" fill="var(--color-review)" />
      <rect x="0" y="11" width="16" height="3" fill="var(--color-decline)" />
      <rect x="10.5" y="0" width="1.5" height="16" fill="var(--color-ink)" />
    </svg>
  );
}

function ServiceStatus({ health, reachable, loading }: HealthState) {
  const t = useT();
  if (loading) return <span className="label">{t("shell.status.checking")}</span>;

  if (!reachable) {
    return (
      <span className="label" style={{ color: "var(--color-decline-ink)" }}>
        {t("shell.status.unreachable")}
      </span>
    );
  }

  const degraded = !health?.model_loaded;
  return (
    <span
      className="label"
      style={{ color: degraded ? "var(--color-review-ink)" : "var(--color-approve-ink)" }}
    >
      {degraded ? t("shell.status.degraded") : t("shell.status.serving")}
    </span>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  const { api, baseUrl } = useApi();
  const pathname = usePathname();
  const t = useT();
  const { data, failure, loading, reload } = useResource<Health>(() => api.health(), [api]);

  const state: HealthState = {
    health: data,
    reachable: failure === null && data !== null,
    loading,
    reload,
  };

  return (
    <HealthContext.Provider value={state}>
      <div className="min-h-dvh">
        <header className="sticky top-0 z-20 bg-[var(--color-paper)]">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-[var(--color-rule)] px-4 py-2.5 sm:px-6">
            <span className="flex items-center gap-2">
              <Mark />
              <span className="text-[15px] font-semibold tracking-tight">CreditSentinel</span>
            </span>
            <span className="label hidden sm:inline">{t("shell.tagline")}</span>
            <span className="ml-auto flex items-center gap-4">
              <ServiceStatus {...state} />
              <LanguageToggle />
              <AppearanceToggle />
            </span>
          </div>

          {/* Provenance sits above the fold on every view (FR-011, SC-007). */}
          <p className="border-b border-[var(--color-rule)] bg-[var(--color-sunk)] px-4 py-1.5 text-[12px] text-[var(--color-graphite)] sm:px-6">
            <span className="label label-ink mr-2">{t("shell.synthetic.badge")}</span>
            {t("shell.synthetic.body")}
          </p>
        </header>

        <div className="flex flex-col lg:flex-row">
          <nav
            aria-label={t("shell.views")}
            className="flex shrink-0 gap-0 overflow-x-auto border-b border-[var(--color-rule)] lg:w-52 lg:flex-col lg:border-b-0 lg:border-r"
          >
            {DESTINATIONS.map((destination) => {
              const active = pathname === destination.href;
              return (
                <Link
                  key={destination.href}
                  href={destination.href}
                  aria-current={active ? "page" : undefined}
                  className="border-l-2 px-4 py-2.5 text-[13px] whitespace-nowrap transition-colors sm:px-6 lg:px-4"
                  style={{
                    borderLeftColor: active ? "var(--color-ink)" : "transparent",
                    color: active ? "var(--color-ink)" : "var(--color-graphite)",
                    fontWeight: active ? 600 : 400,
                    background: active ? "var(--color-sunk)" : "transparent",
                  }}
                >
                  {t(destination.key)}
                </Link>
              );
            })}

            <div className="mt-auto hidden border-t border-[var(--color-rule)] p-4 lg:block">
              <p className="label">{t("shell.serving")}</p>
              <p className="num mt-1 text-[12px] text-[var(--color-graphite)]">
                {t("shell.model", { v: state.health?.model_version ?? "—" })}
              </p>
              <p className="num text-[12px] text-[var(--color-graphite)]">
                {t("shell.pipeline", { v: state.health?.feature_pipeline_version ?? "—" })}
              </p>
              <p className="label mt-3">{t("shell.service")}</p>
              <p className="num text-[12px] break-all text-[var(--color-muted)]">{baseUrl}</p>
            </div>
          </nav>

          <main className="min-w-0 flex-1 px-4 py-6 sm:px-6">{children}</main>
        </div>
      </div>
    </HealthContext.Provider>
  );
}
