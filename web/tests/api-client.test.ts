import { afterEach, describe, expect, it, vi } from "vitest";
import { asFailure, createApi } from "@/lib/api";

function stubFetch(response: Partial<Response> & { jsonBody?: unknown }) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: response.ok ?? true,
    status: response.status ?? 200,
    json: async () => response.jsonBody ?? {},
  } as Response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client — outcome classification", () => {
  it("returns parsed JSON on success", async () => {
    stubFetch({ ok: true, jsonBody: { status: "ok", model_loaded: true } });
    const api = createApi("http://svc:8080");
    await expect(api.health()).resolves.toMatchObject({ model_loaded: true });
  });

  it("classifies a network failure as unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const api = createApi("http://svc:8080");
    await expect(api.drift()).rejects.toMatchObject({ failure: { kind: "unreachable" } });
  });

  it("classifies a structured 404 as not_produced and keeps the remedy", async () => {
    stubFetch({
      ok: false,
      status: 404,
      jsonBody: {
        detail: { status: "not_produced", artifact: "drift_run", remedy: "run the drift job" },
      },
    });
    const api = createApi("http://svc:8080");
    await expect(api.drift()).rejects.toMatchObject({
      failure: { kind: "not_produced", artifact: "drift_run", remedy: "run the drift job" },
    });
  });

  it("does not treat an ordinary 404 as not_produced", async () => {
    stubFetch({ ok: false, status: 404, jsonBody: { detail: "Not Found" } });
    const api = createApi("http://svc:8080");
    await expect(api.governance()).rejects.toMatchObject({ failure: { kind: "server" } });
  });

  it("maps a 422 onto field messages", async () => {
    stubFetch({
      ok: false,
      status: 422,
      jsonBody: {
        detail: [
          { loc: ["body", "debt_to_income"], msg: "Input should be less than or equal to 2" },
          { loc: ["body", "age"], msg: "Input should be greater than or equal to 18" },
        ],
      },
    });
    const api = createApi("http://svc:8080");
    try {
      await api.score({} as never);
      expect.unreachable();
    } catch (error) {
      const failure = asFailure(error);
      expect(failure.kind).toBe("invalid");
      if (failure.kind === "invalid") {
        expect(failure.fields.debt_to_income).toMatch(/less than or equal to 2/);
        expect(failure.fields.age).toMatch(/greater than or equal to 18/);
      }
    }
  });

  it("classifies a 500 as a server fault", async () => {
    stubFetch({ ok: false, status: 500, jsonBody: {} });
    const api = createApi("http://svc:8080");
    await expect(api.governance()).rejects.toMatchObject({ failure: { kind: "server", status: 500 } });
  });

  it("builds a bounded, filtered audit query", async () => {
    const fetchMock = stubFetch({ ok: true, jsonBody: { count: 0, entries: [] } });
    const api = createApi("http://svc:8080/");
    await api.audit({ limit: 25, decision: "decline" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://svc:8080/audit?limit=25&decision=decline",
      expect.anything(),
    );
  });

  it("omits the decision parameter when none is given", async () => {
    const fetchMock = stubFetch({ ok: true, jsonBody: { count: 0, entries: [] } });
    const api = createApi("http://svc:8080");
    await api.audit();
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("limit=50");
    expect(url).not.toContain("decision=");
  });
});
