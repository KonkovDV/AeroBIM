import { describe, expect, it } from "vitest";
import {
  engineGroupStatus,
  formatEngineGroupStatus,
  humanCapabilityLine,
  RUN_ENGINE_GROUPS,
} from "./capability-copy";
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

describe("humanCapabilityLine", () => {
  it("does not echo English capability enums in the visible line", () => {
    expect(humanCapabilityLine({ key: "clash", status: "skipped" })).toBe(
      "Проверка «коллизии» не выполнена → тишина ≠ успех",
    );
    expect(humanCapabilityLine({ key: "dwg_dxf", status: "failed" })).toMatch(
      /Проверка «DWG» не выполнена → вердикт отрицательный/,
    );
    expect(humanCapabilityLine({ key: "ids", status: "ok" })).toBe("Проверка «IDS» выполнена");
    expect(humanCapabilityLine({ key: "clash", status: "skipped" })).not.toMatch(/skipped|failed|ok/);
  });

  it("states MEP gap in human language without calling silence success", () => {
    expect(humanCapabilityLine({ key: "mep_system_clash", status: "not_verified" })).toBe(
      "Проверка коллизий инженерных сетей не выполнена (сети в IFC не переданы) → тишина ≠ успех",
    );
  });
});

describe("formatEngineGroupStatus", () => {
  it("renders group status in Russian", () => {
    expect(formatEngineGroupStatus("pending")).toBe("ожидание");
    expect(formatEngineGroupStatus("ok")).toBe("выполнена");
    expect(formatEngineGroupStatus("skipped")).toBe("пропущена");
    expect(formatEngineGroupStatus("failed")).toBe("не выполнена");
  });
});
