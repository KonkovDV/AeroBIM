import { describe, expect, it } from "vitest";
import { hitlEventTypeLabel } from "./hitl-event-copy";
import { UI_COPY } from "./ui-copy";

describe("hitlEventTypeLabel", () => {
  it("maps known HITL event types to RU_COPY and leaves unknown tokens", () => {
    expect(hitlEventTypeLabel("accepted")).toBe(UI_COPY.kpiTypeAccepted);
    expect(hitlEventTypeLabel("edited_remark")).toBe(UI_COPY.kpiTypeEditedRemark);
    expect(hitlEventTypeLabel("opened")).toBe(UI_COPY.kpiTypeOpened);
    expect(hitlEventTypeLabel("custom_token")).toBe("custom_token");
  });
});
