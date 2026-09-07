import { describe, expect, it } from "vitest";
import { UI_COPY } from "./ui-copy";

describe("product copy safety boundaries", () => {
  it("removes developer contracts from primary workspace messages", () => {
    const primary = [UI_COPY.headerLede, UI_COPY.roleBanner, UI_COPY.roleBannerLab,
      UI_COPY.capabilityMissing, UI_COPY.engineFlag, UI_COPY.hitlSeparate, UI_COPY.diffNote];
    for (const text of primary) expect(text).not.toMatch(/summary\.passed|customer_go|Checkpoint|GET \/v1|SSE|review-events/);
  });
  it("does not equate empty filtered results with complete validation", () => {
    expect(UI_COPY.noFindings).toContain("фильтрам");
    expect(UI_COPY.noFindings).toContain("Полноту");
    expect(UI_COPY.diffNote).toContain("не доказывает исправление");
    expect(UI_COPY.capabilityMissing).toContain("неизвестна");
  });
  it("keeps browser limits, customer approval and timing uncertainty explicit", () => {
    expect(UI_COPY.viewerOverWasmCap).toContain("256 МиБ");
    expect(UI_COPY.runSizeHonesty).toContain("специальной настройки");
    expect(UI_COPY.runTimer("00:30")).toContain("Цель ТЗ записана как 30:00");
    expect(UI_COPY.runTimer("00:30")).toContain("SLA не заявляем");
    expect(UI_COPY.runTimer("00:30")).not.toMatch(/до\s*30\s*мин/);
    expect(UI_COPY.headerLede).not.toMatch(/до\s*30\s*мин/);
    expect(UI_COPY.headerLede).toContain("Внедрение у заказчика ещё не подтверждено");
    expect(UI_COPY.trainingRulesBanner).toContain("ещё не согласован");
  });
});
