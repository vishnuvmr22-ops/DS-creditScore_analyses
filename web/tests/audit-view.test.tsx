import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import AuditPageView from "@/app/audit/page";
import { AUDIT_PAGE, makeApi, POLICY, renderWithApi } from "./helpers";

describe("audit view", () => {
  it("renders recorded decisions with drivers and pseudonymized references", async () => {
    const api = makeApi({
      audit: () => Promise.resolve(AUDIT_PAGE),
      decisionPolicy: () => Promise.resolve(POLICY),
    });
    renderWithApi(<AuditPageView />, api);

    expect(await screen.findByText("pseudo_e6cae956dbeb")).toBeInTheDocument();
    expect(screen.getByText("debt-to-income ratio")).toBeInTheDocument();
    expect(screen.getByText(/1 · 1\.0\.0/)).toBeInTheDocument(); // versions
  });

  it("passes the selected outcome filter to the service", async () => {
    const user = userEvent.setup();
    const audit = vi.fn().mockResolvedValue(AUDIT_PAGE);
    const api = makeApi({ audit, decisionPolicy: () => Promise.resolve(POLICY) });
    renderWithApi(<AuditPageView />, api);

    await screen.findByText("pseudo_e6cae956dbeb");
    await user.click(screen.getByRole("button", { name: "Declined" }));

    await waitFor(() =>
      expect(audit).toHaveBeenLastCalledWith({ limit: 50, decision: "decline" }),
    );
  });

  it("shows a normal empty state when nothing matches (count 0, not an error)", async () => {
    const api = makeApi({
      audit: () => Promise.resolve({ count: 0, entries: [] }),
      decisionPolicy: () => Promise.resolve(POLICY),
    });
    renderWithApi(<AuditPageView />, api);
    expect(await screen.findByText(/No decisions match/i)).toBeInTheDocument();
  });

  it("shows the not-produced state distinctly from an empty result", async () => {
    const api = makeApi({
      audit: () =>
        Promise.reject(
          new ApiError({
            kind: "not_produced",
            artifact: "audit_log",
            remedy: "score an applicant",
            message: "No audit log yet.",
          }),
        ),
      decisionPolicy: () => Promise.resolve(POLICY),
    });
    renderWithApi(<AuditPageView />, api);
    expect(await screen.findByText(/Nothing recorded yet/i)).toBeInTheDocument();
    expect(screen.getByText(/score an applicant/i)).toBeInTheDocument();
  });

  it("never shows a raw applicant identifier", async () => {
    const api = makeApi({
      audit: () => Promise.resolve(AUDIT_PAGE),
      decisionPolicy: () => Promise.resolve(POLICY),
    });
    const { container } = renderWithApi(<AuditPageView />, api);
    await screen.findByText("pseudo_e6cae956dbeb");
    expect(container.textContent).not.toMatch(/APP-/);
  });
});
