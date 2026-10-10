import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CalibrationPlot } from "@/components/calibration-plot";
import type { CalibrationBin } from "@/lib/types";

const BINS: CalibrationBin[] = [
  { bin: 0, n: 317, mean_pred: 0.07, observed: 0.088 },
  { bin: 1, n: 638, mean_pred: 0.148, observed: 0.166 },
  { bin: 2, n: 4, mean_pred: 0.86, observed: 0.25 },
];

describe("calibration plot", () => {
  it("plots one marker per bin", () => {
    const { container } = render(
      <CalibrationPlot bins={BINS} expectedCalibrationError={0.114} />,
    );
    expect(container.querySelectorAll("circle").length).toBe(BINS.length);
  });

  it("maps predicted vs observed to plausible plot coordinates", () => {
    const { container } = render(
      <CalibrationPlot bins={BINS} expectedCalibrationError={0.114} />,
    );
    const circles = Array.from(container.querySelectorAll("circle"));
    // Higher predicted PD → further right (larger cx).
    const cx = circles.map((c) => Number(c.getAttribute("cx")));
    expect(cx[0]).toBeLessThan(cx[1]);
    expect(cx[1]).toBeLessThan(cx[2]);
    // Higher observed rate → higher on the plot (smaller cy, y is inverted).
    const cy0 = Number(circles[0].getAttribute("cy"));
    const cy1 = Number(circles[1].getAttribute("cy"));
    expect(cy1).toBeLessThan(cy0); // bin 1 has the higher observed rate
  });

  it("tolerates a short bin list without assuming a fixed length", () => {
    const { container } = render(
      <CalibrationPlot bins={BINS.slice(0, 1)} expectedCalibrationError={0.05} />,
    );
    expect(container.querySelectorAll("circle").length).toBe(1);
  });

  it("shows the overall calibration error", () => {
    render(<CalibrationPlot bins={BINS} expectedCalibrationError={0.114} />);
    expect(screen.getByText("0.1140")).toBeInTheDocument();
  });
});
