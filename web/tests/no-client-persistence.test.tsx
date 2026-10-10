import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import DecisioningPage from "@/app/page";
import { Shell } from "@/components/shell";
import { makeApi, renderWithApi, SCORE } from "./helpers";

/**
 * FR-012 — the console holds applicant values in transient state only. After a
 * score it must leave nothing behind in storage, and it must issue requests to
 * no host other than the scoring service.
 */
describe("no client-side persistence of applicant data", () => {
  it("writes no applicant attribute value to local or session storage", async () => {
    const user = userEvent.setup();
    const api = makeApi({ score: () => Promise.resolve(SCORE) });
    renderWithApi(
      <Shell>
        <DecisioningPage />
      </Shell>,
      api,
    );

    // The impaired preset carries a distinctive income; score it.
    await user.click(await screen.findByRole("button", { name: /score applicant/i }));
    await screen.findByText("0.7622");

    const dumped = JSON.stringify({
      local: { ...localStorage },
      session: { ...sessionStorage },
    });
    // No submitted applicant value — id or attributes — may appear in storage.
    for (const leaked of ["APP-IMPAIR-01", "21000", "0.95", "debt_to_income"]) {
      expect(dumped).not.toContain(leaked);
    }
  });

  it("only ever fetches the scoring service, never another host", async () => {
    const user = userEvent.setup();
    const seen: string[] = [];
    const api = makeApi({
      score: () => {
        seen.push("score");
        return Promise.resolve(SCORE);
      },
    });

    // Guard: fetch must not be called to any other origin from the page.
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    renderWithApi(
      <Shell>
        <DecisioningPage />
      </Shell>,
      api,
    );
    await user.click(await screen.findByRole("button", { name: /score applicant/i }));
    await screen.findByText("0.7622");

    // The stub client intercepts calls, so the page itself opened no raw fetch.
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(seen).toContain("score");
    vi.unstubAllGlobals();
  });
});
