import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/api";
import DecisioningPage from "@/app/page";
import { HEALTHY, makeApi, POLICY, renderWithApi, SCORE } from "./helpers";
import { Shell } from "@/components/shell";

function renderPage(api = makeApi({ score: () => Promise.resolve(SCORE) })) {
  return renderWithApi(
    <Shell>
      <DecisioningPage />
    </Shell>,
    api,
  );
}

describe("decisioning view", () => {
  it("renders every field of a scored response (SC-002)", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /score applicant/i }));

    // pd, decision, both versions, audit id, pseudonymized reference, reason, generator.
    expect(await screen.findByText("0.7622")).toBeInTheDocument();
    expect(screen.getAllByText(/Decline/i).length).toBeGreaterThan(0);
    expect(screen.getByText("audit-xyz")).toBeInTheDocument();
    expect(screen.getAllByText("pseudo_abc123").length).toBeGreaterThan(0);
    expect(screen.getByText(/weighed heavily against approval/i)).toBeInTheDocument();
    expect(screen.getByText(/Deterministic template/i)).toBeInTheDocument();
    // Policy reference passage is shown.
    expect(screen.getByText(/debt-to-income above 0\.5 are declined/i)).toBeInTheDocument();
  });

  it("shows every reason-cited driver in the driver list (SC-003)", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: /score applicant/i }));

    await screen.findByText("0.7622");
    // grounded_in cites debt_to_income and num_delinquencies; both must be visible as drivers.
    expect(screen.getByText("debt-to-income ratio")).toBeInTheDocument();
    expect(screen.getByText("recent delinquencies")).toBeInTheDocument();
  });

  it("maps a server 422 back onto the offending field", async () => {
    const user = userEvent.setup();
    const api = makeApi({
      score: () =>
        Promise.reject(
          new ApiError({
            kind: "invalid",
            fields: { debt_to_income: "Input should be less than or equal to 2" },
            message: "rejected",
          }),
        ),
    });
    renderPage(api);

    await user.click(await screen.findByRole("button", { name: /score applicant/i }));
    expect(await screen.findByText(/less than or equal to 2/i)).toBeInTheDocument();
    const input = screen.getByLabelText(/Debt-to-income/i);
    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("disables scoring when the service is degraded", async () => {
    const api = makeApi({
      health: () => Promise.resolve({ ...HEALTHY, status: "degraded", model_loaded: false }),
      score: () => Promise.resolve(SCORE),
    });
    renderPage(api);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /score applicant/i })).toBeDisabled(),
    );
    expect(screen.getByText(/until a governed model is trained/i)).toBeInTheDocument();
  });

  it("positions the probability against the thresholds from the policy", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: /score applicant/i }));

    const scale = await screen.findByRole("img", { name: /Probability of default 0\.7622/i });
    expect(scale.getAttribute("aria-label")).toMatch(/Approve below 0\.15/);
    expect(scale.getAttribute("aria-label")).toMatch(/decline at or above 0\.45/i);
    // Sanity: policy fixture matches.
    expect(POLICY.decline_at_or_above).toBe(0.45);
  });
});

describe("shell", () => {
  it("shows the synthetic-data provenance statement", async () => {
    renderPage();
    expect(screen.getAllByText(/Synthetic data/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/nothing shown is a real lending decision/i)).toBeInTheDocument();
  });

  it("distinguishes a healthy service from an unreachable one", async () => {
    const api = makeApi({ health: () => Promise.reject(new Error("down")) });
    renderPage(api);
    expect(await screen.findByText(/Service unreachable/i)).toBeInTheDocument();
  });

  it("names the served model version when healthy", async () => {
    renderPage();
    const nav = screen.getByRole("navigation", { name: /views/i });
    await waitFor(() => expect(within(nav).getByText(/model 1/)).toBeInTheDocument());
  });
});
