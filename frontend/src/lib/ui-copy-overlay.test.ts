import { describe, expect, it } from "vitest";
import { EVIDENCE_COPY } from "./i18n/evidence";
import { ERGONOMICS_COPY } from "./i18n/ergonomics";
import { RU_COPY } from "./i18n/ru";
import { WORKPLACE_COPY } from "./i18n/workplace";
import { UI_COPY } from "./ui-copy";

/**
 * FW-01 / FW-02: `UI_COPY` is `{ ...RU_COPY, ...WORKPLACE_COPY, ...EVIDENCE_COPY,
 * ...ERGONOMICS_COPY }`. Later layers win. Keys that still exist in `ru.ts`
 * but are hidden on screen must be listed here, or a new silent overlay
 * will land without a test failure.
 */
function overlayKeys(base: object, later: object): string[] {
  const laterKeys = new Set(Object.keys(later));
  return Object.keys(base).filter((key) => laterKeys.has(key)).sort();
}

const LATER_COPY = {
  ...WORKPLACE_COPY,
  ...EVIDENCE_COPY,
  ...ERGONOMICS_COPY,
};

describe("FW-01/FW-02 copy overlay", () => {
  it("pins which RU_COPY keys later layers hide from the screen", () => {
    expect(overlayKeys(RU_COPY, LATER_COPY)).toEqual([
      "capabilityMissing",
      "capabilityOkBanner",
      "clashTitle",
      "clauseMissingCard",
      "diffNote",
      "drawingCaptionBody",
      "drawingNoZone",
      "drawingTitle",
      "drawingZoomHint",
      "dropHint",
      "elementPropsHonesty",
      "engineFail",
      "engineFlag",
      "engineGateway",
      "enginePass",
      "exportPdfHint",
      "failClosedBefore",
      "findingsKicker",
      "findingsTitle",
      "focusClash",
      "headerEyebrow",
      "headerLede",
      "headerTitle",
      "historyFailed",
      "hitlHistory",
      "hitlNone",
      "hitlNotRecorded",
      "hitlOnly",
      "hitlRecording",
      "hitlRegions",
      "hitlSeparate",
      "hitlUserAlias",
      "hitlVerdict",
      "keyboardHelp",
      "noClash",
      "noFindings",
      "noReportSelected",
      "noReqMatch",
      "outcomeBlocked",
      "outcomeFailed",
      "outcomeLegacyFail",
      "outcomeLegacyPass",
      "outcomePass",
      "outcomePassWarnings",
      "outcomeReview",
      "provenanceGap",
      "provenanceOk",
      "rawStep",
      "regionOverlays",
      "rehearsalOneClick",
      "remarkSaved",
      "reportsLoaded",
      "roleBanner",
      "roleBannerLab",
      "roleBannerLoading",
      "roleBannerUnknown",
      "roleSelectLabel",
      "runCellGate",
      "runEvidenceNone",
      "runGateNone",
      "runHonesty",
      "runJournalHonesty",
      "runSizeHonesty",
      "runStagesHonesty",
      "runTimer",
      "runTimerIdle",
      "runTitle",
      "selectReportClash",
      "shownCount",
      "silenceIsNotSuccess",
      "statusFailed",
      "statusPassed",
      "storeyFilterHonesty",
      "syntheticMark",
      "trainingRulesBanner",
      "uploadAccepted",
      "uploadHint",
      "uploadSizeHonesty",
      "viewerCaption",
      "viewerFocusOn",
      "viewerFooter",
      "viewerInit",
      "viewerLoad",
      "viewerLoading",
      "viewerNeedReport",
      "viewerOverWasmCap",
      "viewerRenderError",
      "viewerRenderErrorHint",
      "viewerTitle",
      "xlsxNotMvp",
    ]);
  });

  it("serves workplace header copy, not the ru.ts checkpoint line", () => {
    expect(UI_COPY.headerEyebrow).toBe(WORKPLACE_COPY.headerEyebrow);
    expect(UI_COPY.headerEyebrow).not.toBe(RU_COPY.headerEyebrow);
    expect(UI_COPY.headerTitle).toBe(WORKPLACE_COPY.headerTitle);
    expect(UI_COPY.roleSelectLabel).toBe(WORKPLACE_COPY.roleSelectLabel);
    expect(String(UI_COPY.headerEyebrow)).not.toMatch(/checkpoint/i);
    expect(String(UI_COPY.headerEyebrow)).not.toMatch(/customer_go/i);
  });
});
