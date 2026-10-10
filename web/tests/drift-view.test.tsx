import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/api";
import DriftPage from "@/app/drift/page";
import { DRIFT_BREACHING, DRIFT_STABLE, makeApi, renderWithApi } from "./helpers";

describe("drift view", () => {
  it("renders a stable verdict with run time and scenario", async () => {
    const api = makeApi({ drift: () => Promise.resolve(DRIFT_STABLE) });
    renderWithApi(<DriftPage />, api);

    // The verdict reads Stable (the PsiBars rows also carry "Stable" labels).
    expect(await screen.findByText("Stable", { selector: ".verdict" })).toBeInTheDocument();
    expect(screen.getByText(/within the alert threshold/i)).toBeInTheDocument();
    expect(screen.getByText("stable")).toBeInTheDocument(); // scenario
  });

  it("renders a drifted verdict and distinguishes the breaching feature", async () => {
    const api = makeApi({ drift: () => Promise.resolve(DRIFT_BREACHING) });
    renderWithApi(<DriftPage />, api);

    expect(await screen.findByText("Drifted")).toBeInTheDocument();
    // Breaching feature is labelled "Breach", not colour alone (FR-014b).
    expect(screen.getByText("Breach")).toBeInTheDocument();
    expect(screen.getByText("Stable")).toBeInTheDocument(); // the non-breaching feature's label
  });

  it("notes when the scenario is the injected-drift batch", async () => {
    const api = makeApi({ drift: () => Promise.resolve(DRIFT_BREACHING) });
    renderWithApi(<DriftPage />, api);
    expect(await screen.findByText(/covariate shift injected on purpose/i)).toBeInTheDocument();
  });

  it("shows the not-produced empty state with the command that records one", async () => {
    const api = makeApi({
      drift: () =>
        Promise.reject(
          new ApiError({
            kind: "not_produced",
            artifact: "drift_run",
            remedy: "run `uv run creditsentinel-drift --scenario stable`",
            message: "No drift run yet.",
          }),
        ),
    });
    renderWithApi(<DriftPage />, api);

    expect(await screen.findByText(/Nothing recorded yet/i)).toBeInTheDocument();
    expect(screen.getByText(/creditsentinel-drift --scenario stable/i)).toBeInTheDocument();
  });
});
