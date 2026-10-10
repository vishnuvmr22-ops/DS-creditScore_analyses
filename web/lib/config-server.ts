/**
 * Server-only configuration.
 *
 * The scoring service address is resolved here, per request, on the server, then
 * handed to the client provider. Keeping it out of the "use client" module is
 * what lets one built image target any environment (FR-023) — the address is
 * never inlined at build time.
 */

export const DEFAULT_API_BASE_URL = "http://localhost:8080";

export function resolveApiBaseUrl(): string {
  return process.env.CS_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;
}
