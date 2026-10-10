import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/api";
import GovernancePage from "@/app/governance/page";
import { GOVERNANCE, makeApi, MODEL_CARD, renderWithApi } from "./helpers";

describe("governance view", () => {
  it("renders metrics, fairness and the model card for the served version", async () => {
    const api = makeApi({
      governance: () => Promise.resolve(GOVERNANCE),
      modelCard: () => Promise.resolve(MODEL_CARD),
    });
    renderWithApi(<GovernancePage />, api);

    expect(await screen.findByText("0.6830")).toBeInTheDocument(); // AUC
    expect(screen.getByText("0.2840")).toBeInTheDocument(); // KS
    expect(screen.getAllByText(/model 1/i).length).toBeGreaterThan(0);

    // Fairness figures with both group rates.
    expect(screen.getByText("87.90%")).toBeInTheDocument();
    expect(screen.getByText("89.70%")).toBeInTheDocument();
    expect(screen.getByText("0.0179")).toBeInTheDocument();

    // Injected-disparity note is present.
    expect(screen.getByText(/injected into the synthetic data deliberately/i)).toBeInTheDocument();

    // Model card content rendered.
    expect(await screen.findByText(/pinned seed with no real PII/i)).toBeInTheDocument();
  });

  it("shows the not-produced state with the remedy when no model is registered", async () => {
    const notProduced = new ApiError({
      kind: "not_produced",
      artifact: "governance",
      remedy: "run `uv run creditsentinel-train`",
      message: "No governance produced yet.",
    });
    const api = makeApi({
      governance: () => Promise.reject(notProduced),
      modelCard: () => Promise.reject(notProduced),
    });
    renderWithApi(<GovernancePage />, api);

    // Both the governance section and the model-card section report not-produced.
    expect((await screen.findAllByText(/Nothing recorded yet/i)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/creditsentinel-train/i).length).toBeGreaterThan(0);
  });
});
