/**
 * The console's only outbound edge.
 *
 * Everything the console knows comes through here, and it talks to exactly one
 * host: the scoring service (FR-012). Its job beyond fetching is to tell four
 * outcomes apart, because each one deserves a different thing on screen:
 *
 *   unreachable   — the service isn't answering. Offer a retry.
 *   not_produced  — the service is fine; the artifact hasn't been made yet.
 *                   The response carries the command that would make it.
 *   invalid       — the submitted applicant was rejected, per field.
 *   server        — a genuine fault. Say so plainly.
 */

import type {
  AuditPage,
  Decision,
  DecisionPolicy,
  DriftRun,
  Governance,
  Health,
  ModelCard,
  ScoreRequest,
  ScoreResponse,
} from "./types";

export interface NotProduced {
  kind: "not_produced";
  artifact: string;
  remedy: string;
  message: string;
}
export interface Unreachable {
  kind: "unreachable";
  message: string;
}
export interface Invalid {
  kind: "invalid";
  fields: Record<string, string>;
  message: string;
}
export interface ServerFault {
  kind: "server";
  status: number;
  message: string;
}

export type Failure = NotProduced | Unreachable | Invalid | ServerFault;

export class ApiError extends Error {
  readonly failure: Failure;

  constructor(failure: Failure) {
    super(failure.message);
    this.name = "ApiError";
    this.failure = failure;
  }
}

export function asFailure(error: unknown): Failure {
  if (error instanceof ApiError) return error.failure;
  return {
    kind: "server",
    status: 0,
    message: error instanceof Error ? error.message : "Something went wrong.",
  };
}

interface NotProducedBody {
  status: "not_produced";
  artifact: string;
  remedy: string;
}

function readNotProduced(body: unknown): NotProducedBody | null {
  const detail = (body as { detail?: unknown })?.detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const candidate = detail as Partial<NotProducedBody>;
    if (candidate.status === "not_produced" && candidate.artifact && candidate.remedy) {
      return candidate as NotProducedBody;
    }
  }
  return null;
}

/** FastAPI reports validation errors as `detail: [{loc, msg}]`; map them onto fields. */
function readFieldErrors(body: unknown): Record<string, string> {
  const detail = (body as { detail?: unknown })?.detail;
  const fields: Record<string, string> = {};
  if (!Array.isArray(detail)) return fields;
  for (const item of detail) {
    const loc = (item as { loc?: unknown })?.loc;
    const msg = (item as { msg?: unknown })?.msg;
    if (!Array.isArray(loc) || typeof msg !== "string") continue;
    const name = [...loc].reverse().find((p) => typeof p === "string" && p !== "body" && p !== "query");
    if (typeof name === "string") fields[name] = msg;
  }
  return fields;
}

export interface Api {
  health(): Promise<Health>;
  decisionPolicy(): Promise<DecisionPolicy>;
  governance(): Promise<Governance>;
  modelCard(): Promise<ModelCard>;
  drift(): Promise<DriftRun>;
  audit(options?: { limit?: number; decision?: Decision | null }): Promise<AuditPage>;
  score(applicant: ScoreRequest): Promise<ScoreResponse>;
}

export function createApi(baseUrl: string): Api {
  const root = baseUrl.replace(/\/+$/, "");

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response;
    try {
      response = await fetch(`${root}${path}`, {
        ...init,
        headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      });
    } catch {
      throw new ApiError({
        kind: "unreachable",
        message: `Can't reach the scoring service at ${root}.`,
      });
    }

    if (response.ok) return (await response.json()) as T;

    const body = await response.json().catch(() => null);

    const missing = response.status === 404 ? readNotProduced(body) : null;
    if (missing) {
      throw new ApiError({
        kind: "not_produced",
        artifact: missing.artifact,
        remedy: missing.remedy,
        message: `No ${missing.artifact.replace(/_/g, " ")} has been produced yet.`,
      });
    }

    if (response.status === 422) {
      const fields = readFieldErrors(body);
      throw new ApiError({
        kind: "invalid",
        fields,
        message: "The service rejected this application. Check the highlighted fields.",
      });
    }

    throw new ApiError({
      kind: "server",
      status: response.status,
      message: `The scoring service returned ${response.status}.`,
    });
  }

  return {
    health: () => request<Health>("/health"),
    decisionPolicy: () => request<DecisionPolicy>("/decision-policy"),
    governance: () => request<Governance>("/governance"),
    modelCard: () => request<ModelCard>("/governance/model-card"),
    drift: () => request<DriftRun>("/drift"),
    audit: ({ limit = 50, decision = null } = {}) => {
      const query = new URLSearchParams({ limit: String(limit) });
      if (decision) query.set("decision", decision);
      return request<AuditPage>(`/audit?${query.toString()}`);
    },
    score: (applicant) =>
      request<ScoreResponse>("/score", { method: "POST", body: JSON.stringify(applicant) }),
  };
}
