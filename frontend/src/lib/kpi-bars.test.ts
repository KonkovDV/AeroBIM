import { describe, expect, it } from "vitest";
import { hitlDecisionSplit, kpiBarRows } from "./kpi-bars";

describe("kpi-bars", () => {
  it("returns no bars for an empty HITL journal", () => {
    expect(kpiBarRows({})).toEqual([]);
    expect(kpiBarRows({ opened: 0, accepted: 0 })).toEqual([]);
    expect(kpiBarRows(null)).toEqual([]);
  });

  it("splits confirm vs reject without treating empty as zero error rate", () => {
    expect(hitlDecisionSplit(undefined)).toEqual({ accepted: 0, rejected: 0 });
    expect(hitlDecisionSplit({ accepted: 3, rejected: 1, opened: 4 })).toEqual({
      accepted: 3,
      rejected: 1,
    });
  });

  it("normalizes counts to percents of the journal, not product accuracy", () => {
    const rows = kpiBarRows({ accepted: 3, rejected: 1 });
    expect(rows[0]).toEqual({ key: "accepted", count: 3, percent: 75 });
    expect(rows[1]).toEqual({ key: "rejected", count: 1, percent: 25 });
  });
});
