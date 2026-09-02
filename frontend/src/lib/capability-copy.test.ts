import { describe, expect, it } from "vitest";
import { engineGroupStatus, RUN_ENGINE_GROUPS } from "./capability-copy";
import type { ReportCapabilities } from "./types";

const caps = {
  ifc_schema: { status: "ok" },
  ifc_validation: { status: "ok" },
  unit_scale: { status: "ok" },
  ids: { status: "skipped" },
  clash: { status: "failed" },
} as ReportCapabilities;

describe("engineGroupStatus", () => {
  it("returns pending without capabilities and worst status within a group", () => {
    expect(engineGroupStatus(null, RUN_ENGINE_GROUPS[0].keys)).toBe("pending");
    expect(engineGroupStatus(caps, RUN_ENGINE_GROUPS[0].keys)).toBe("ok");
    expect(engineGroupStatus(caps, RUN_ENGINE_GROUPS[1].keys)).toBe("failed");
  });
});
