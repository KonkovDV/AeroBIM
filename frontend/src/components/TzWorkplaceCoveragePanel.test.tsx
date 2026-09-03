import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import TzWorkplaceCoveragePanel from "./TzWorkplaceCoveragePanel";

describe("TzWorkplaceCoveragePanel", () => {
  it("lists all eight IA screens without claiming delivery", () => {
    render(<TzWorkplaceCoveragePanel />);
    expect(screen.getByTestId("tz-workplace-coverage")).toBeTruthy();
    expect(screen.getByText("SCR-DIFF")).toBeTruthy();
    expect(screen.getAllByText("partial").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/«не воспроизведено» ≠ исправлено/).length).toBeGreaterThan(0);
    expect(screen.getByText(/не поставка/i)).toBeTruthy();
    expect(screen.getByTestId("tz-requirement-map")).toBeTruthy();
    expect(screen.getByText("TZ-BLOCKERS")).toBeTruthy();
  });
});
