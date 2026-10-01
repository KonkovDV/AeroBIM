import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import MachineGatewayStrip from "./MachineGatewayStrip";
import { UI_COPY } from "../../lib/ui-copy";
import type { ValidationReport } from "../../lib/types";

function report(): ValidationReport {
  return {
    report_id: "r".repeat(32),
    request_id: "req",
    created_at: "2026-09-16T00:00:00Z",
    project_name: "demo-pack",
    requirements: [],
    issues: [],
    summary: {
      requirement_count: 0,
      issue_count: 1,
      error_count: 1,
      warning_count: 0,
      passed: false,
      drawing_annotation_count: 0,
      generated_remark_count: 0,
    },
    drawing_annotations: [],
    drawing_assets: [],
    clash_results: [],
  };
}

describe("MachineGatewayStrip", () => {
  it("keeps the persisted finding decision visible while a retry is saving or failed", () => {
    const { rerender } = render(
      <MachineGatewayStrip report={report()} hitlDecisionState="failed" persistedHitlState="accepted" />,
    );
    expect(screen.getByText(new RegExp(UI_COPY.hitlConfirmed))).toBeTruthy();
    expect(screen.getByText(new RegExp(UI_COPY.hitlNotRecorded))).toBeTruthy();
    expect(screen.getByText(UI_COPY.hitlSeparate)).toBeTruthy();
    rerender(
      <MachineGatewayStrip report={report()} hitlDecisionState="saving" persistedHitlState="accepted" />,
    );
    expect(screen.getByText(new RegExp(UI_COPY.hitlConfirmed))).toBeTruthy();
    expect(screen.getByText(new RegExp(UI_COPY.hitlRecording))).toBeTruthy();
  });
});
