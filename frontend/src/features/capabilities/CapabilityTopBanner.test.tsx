import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import CapabilityTopBanner from "./CapabilityTopBanner";
import type { ReportCapabilities } from "../../lib/types";
import { UI_COPY } from "../../lib/ui-copy";

const capabilities: ReportCapabilities = {
  clash: { status: "skipped", reason: "no tessellation" },
  ids: { status: "ok" },
  ifc_validation: { status: "ok" },
  unit_scale: { status: "ok" },
  raster: { status: "ok" },
  ifc_schema: { status: "ok" },
  dwg_dxf: { status: "failed", reason: "native" },
};

describe("CapabilityTopBanner", () => {
  it("states skipped clash in human language above the report", () => {
    render(<CapabilityTopBanner capabilities={capabilities} />);
    const text = screen.getByTestId("capability-top-banner").textContent ?? "";
    expect(text).toMatch(/коллизии/);
    expect(text).toContain(UI_COPY.silenceIsNotSuccess);
    expect(text).toMatch(/DWG/);
    expect(text).not.toMatch(/\bskipped\b|\bfailed\b/);
  });

  it("states missing MEP IFC without calling silence success", () => {
    render(
      <CapabilityTopBanner
        capabilities={{
          ...capabilities,
          mep_system_clash: { status: "not_verified", reason: "no MEP IFC" },
        }}
      />,
    );
    const text = screen.getByTestId("capability-top-banner").textContent ?? "";
    expect(text).toMatch(/коллизий инженерных сетей/);
    expect(text).toMatch(/сети в IFC не переданы/);
    expect(text).not.toMatch(/not_verified/);
  });

  it("does not label an empty capability response as complete", () => {
    render(<CapabilityTopBanner capabilities={{} as ReportCapabilities} />);
    const banner = screen.getByTestId("capability-top-banner");
    expect(banner.textContent).toBe(UI_COPY.capabilityMissing);
    expect(banner.className).not.toContain("capability-top-banner-ok");
  });

  it("keeps the complete nonempty case distinct", () => {
    render(<CapabilityTopBanner capabilities={{ ...capabilities, clash: { status: "ok" }, dwg_dxf: { status: "ok" } }} />);
    const banner = screen.getByTestId("capability-top-banner");
    expect(banner.textContent).toBe(UI_COPY.capabilityOkBanner);
    expect(banner.className).toContain("capability-top-banner-ok");
  });
});
