"use client";

import { createContext, useContext, useMemo, type ReactNode } from "react";
import { createApi, type Api } from "./api";

/** Exported so tests can inject a stub client directly (see tests/helpers). */
export const ApiContext = createContext<{ api: Api; baseUrl: string } | null>(null);

/**
 * The service address is resolved on the server per request and handed down
 * here, so one built image runs against any environment (FR-023). Nothing about
 * the address is baked in at build time.
 */
export function ApiProvider({ baseUrl, children }: { baseUrl: string; children: ReactNode }) {
  const value = useMemo(() => ({ api: createApi(baseUrl), baseUrl }), [baseUrl]);
  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
}

export function useApi(): { api: Api; baseUrl: string } {
  const value = useContext(ApiContext);
  if (!value) throw new Error("useApi must be used inside ApiProvider");
  return value;
}
