import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DeterminationScale } from "@/components/determination-scale";
import { DriverBars } from "@/components/driver-bars";
import { sortWorstFirst } from "@/components/psi-bars";
import type { Driver } from "@/lib/types";

describe("determination scale", () => {
  const props = { approveBelow: 0.15, declineAtOrAbove: 0.45 };

  it("labels the outcome and value for assistive tech in each band", () => {
    const { rerender } = render(
      <DeterminationScale pd={0.05} {...props} decision="approve" />,
    );
    expect(screen.getByRole("img").getAttribute("aria-label")).toMatch(/Approve/);

    rerender(<DeterminationScale pd={0.3} {...props} decision="review" />);
    expect(screen.getByRole("img").getAttribute("aria-label")).toMatch(/review/i);

    rerender(<DeterminationScale pd={0.8} {...props} decision="decline" />);
    expect(screen.getByRole("img").getAttribute("aria-label")).toMatch(/Decline/);
  });

  it("states the probability in the accessible label", () => {
    render(<DeterminationScale pd={0.762} {...props} decision="decline" />);
    expect(screen.getByRole("img").getAttribute("aria-label")).toMatch(/0\.7620/);
  });
});

describe("driver bars", () => {
  const drivers: Driver[] = [
    { feature: "debt_to_income", label: "debt-to-income ratio", shap: 1.2, direction: "increases_risk" },
    { feature: "num_delinquencies", label: "recent delinquencies", shap: 0.6, direction: "increases_risk" },
    { feature: "annual_income", label: "annual income", shap: -0.3, direction: "reduces_risk" },
  ];

  it("scales each bar relative to the largest driver", () => {
    render(<DriverBars drivers={drivers} />);
    const bars = screen.getAllByRole("img");
    const fill = (index: number) =>
      (bars[index].querySelector("span") as HTMLElement).style.width;
    // 1.2 is the widest → 100%; 0.6 → 50%; 0.3 → 25%.
    expect(fill(0)).toBe("100%");
    expect(fill(1)).toBe("50%");
    expect(fill(2)).toBe("25%");
  });

  it("names the risk direction in words, not colour alone (FR-014b)", () => {
    render(<DriverBars drivers={drivers} />);
    expect(screen.getAllByText("increases risk").length).toBe(2);
    expect(screen.getByText("reduces risk")).toBeInTheDocument();
  });

  it("shows the signed contribution for each driver", () => {
    render(<DriverBars drivers={drivers} />);
    expect(screen.getByText("+1.200")).toBeInTheDocument();
    expect(screen.getByText("−0.300")).toBeInTheDocument();
  });
});

describe("psi ordering", () => {
  it("sorts features worst-first", () => {
    const rows = sortWorstFirst({
      age: { psi: 0.01, breach: false },
      debt_to_income: { psi: 0.31, breach: true },
      utilization: { psi: 0.12, breach: false },
    });
    expect(rows.map((r) => r.feature)).toEqual(["debt_to_income", "utilization", "age"]);
  });
});
