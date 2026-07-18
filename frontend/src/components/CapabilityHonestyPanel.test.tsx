import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import CapabilityHonestyPanel from "./CapabilityHonestyPanel";
import type { ReportCapabilities } from "../lib/types";

const baseCapabilities: ReportCapabilities = {
  clash: { status: "ok", reason: "ifcclash" },
  ids: { status: "ok" },
  ifc_validation: { status: "ok" },
  unit_scale: { status: "ok" },
  raster: { status: "skipped", reason: "no drawings" },
  ifc_schema: { status: "ok" },
  mep_system_clash: { status: "not_verified", reason: "unconfigured provider" },
  calculation_correctness: { status: "not_implemented" },
  dwg_dxf: { status: "failed", reason: "DWG present without ODA" },
};

describe("CapabilityHonestyPanel", () => {
  it("renders capability rows and blocking banner", () => {
    render(
      <CapabilityHonestyPanel
        capabilities={baseCapabilities}
        divergences={[
          {
            finding_key: "IDS-1",
            engine_verdict: "error",
            advisory_verdict: "ok",
            resolution: "engine_wins",
          },
        ]}
      />,
    );

    expect(screen.getByTestId("capability-honesty")).toBeTruthy();
    expect(screen.getByText(/1 blocking capability status/i)).toBeTruthy();
    expect(screen.getByText(/dwg dxf=failed/i)).toBeTruthy();
    expect(screen.getByTestId("divergence-list").textContent).toMatch(/engine_wins/);
  });

  it("shows incomplete-evidence message when capabilities missing", () => {
    render(<CapabilityHonestyPanel capabilities={null} />);
    expect(screen.getByText(/No capability matrix/i)).toBeTruthy();
  });
});
