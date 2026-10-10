import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { Shell } from "@/components/shell";
import { THEME_KEY } from "@/components/theme";
import { HEALTHY, makeApi, renderWithApi } from "./helpers";

function renderShell(api = makeApi()) {
  return renderWithApi(
    <Shell>
      <p>child</p>
    </Shell>,
    api,
  );
}

describe("shell", () => {
  it("shows the provenance statement", () => {
    renderShell();
    expect(screen.getAllByText(/Synthetic data/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/no real PII/i)).toBeInTheDocument();
  });

  it("offers all four destinations", () => {
    renderShell();
    const nav = screen.getByRole("navigation", { name: /views/i });
    for (const label of ["Decisioning", "Governance", "Drift", "Audit"]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
    expect(nav).toBeInTheDocument();
  });

  it("shows the serving state when a governed model is loaded", async () => {
    renderShell();
    expect(await screen.findByText(/Serving/i)).toBeInTheDocument();
  });

  it("shows the degraded state when no governed model is loaded", async () => {
    renderShell(makeApi({ health: () => Promise.resolve({ ...HEALTHY, model_loaded: false }) }));
    expect(await screen.findByText(/Degraded/i)).toBeInTheDocument();
  });

  it("persists the appearance choice across a remount", async () => {
    const user = userEvent.setup();
    renderShell();

    await user.click(screen.getByRole("button", { name: "dark" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem(THEME_KEY)).toBe("dark");

    // A fresh mount reads the stored preference.
    renderShell();
    await waitFor(() => {
      const darkButtons = screen.getAllByRole("button", { name: "dark" });
      expect(darkButtons.some((b) => b.getAttribute("aria-pressed") === "true")).toBe(true);
    });
  });
});
