import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import AnalyzeRunPanel from "./AnalyzeRunPanel";
import type { ReportCapabilities } from "../lib/types";

describe("AnalyzeRunPanel", () => {
  it("shows elapsed-timer copy without claiming SLA", () => {
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    const timer = screen.getByTestId("analyze-elapsed");
    expect(timer.textContent).toMatch(/30:00/);
    expect(timer.textContent).toMatch(/не измеренный SLA|не SLA/);
  });

  it("shows engine groups as pending until capabilities exist", () => {
    render(<AnalyzeRunPanel ifcPath={null} />);
    const list = screen.getByTestId("analyze-engine-groups");
    expect(list.textContent).toMatch(/модель: ожидание/);
    expect(list.textContent).toMatch(/правила: ожидание/);
  });

  it("maps skipped and failed engines without calling them success", () => {
    const capabilities = {
      ifc_schema: { status: "ok" },
      ifc_validation: { status: "ok" },
      unit_scale: { status: "ok" },
      ids: { status: "ok" },
      clash: { status: "skipped" },
      raster: { status: "failed" },
    } as ReportCapabilities;
    render(<AnalyzeRunPanel ifcPath="walls.ifc" capabilities={capabilities} />);
    const list = screen.getByTestId("analyze-engine-groups");
    expect(list.textContent).toMatch(/модель: ok/);
    expect(list.textContent).toMatch(/правила: skipped/);
    expect(list.textContent).toMatch(/документы: failed/);
  });
});
