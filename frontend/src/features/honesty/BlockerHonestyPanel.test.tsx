import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchSystemCapabilitiesMock = vi.fn();

vi.mock("../../lib/api", () => ({
  fetchSystemCapabilities: (...args: unknown[]) => fetchSystemCapabilitiesMock(...args),
}));

import BlockerHonestyPanel from "./BlockerHonestyPanel";
import { INTAKE_GATE_KEYS } from "../../lib/intake-gates";

describe("BlockerHonestyPanel", () => {
  beforeEach(() => {
    fetchSystemCapabilitiesMock.mockReset();
    fetchSystemCapabilitiesMock.mockResolvedValue({
      artifact_type: "system_capabilities",
      schema_version: "1.3.0",
      customer_intake_gate: {
        status: "BLOCKED_NO_CUSTOMER_DATA",
        claim_level: "not_ready",
        true_gates: [],
        checkpoint: "GO",
        go_kind: "regulatory_measurement_mvp",
        source: "audit/evidence/customer-intake-gate.json",
      },
      auth_bff: { status: "not_implemented" },
      bcf_t2: { status: "not_verified", claim_allowed: false, raw_status: "NOT_VERIFIED" },
      samolet_mvp_answers: {
        closes_rt001: false,
        closes_rt002: false,
        closes_rt003: false,
        checkpoint: "GO",
        go_kind: "regulatory_measurement_mvp",
        customer_go: false,
        cde_integration_mvp: false,
      },
    });
  });

  it("lists intake gates as false and does not close RT", async () => {
    render(<BlockerHonestyPanel />);
    expect(await screen.findByTestId("blocker-honesty-panel")).toBeTruthy();
    expect(screen.getByTestId("rt-blocker-list").textContent).toMatch(/RT-001 ОТКРЫТ/);
    expect(screen.getByText(/RT-002 ОТКРЫТ/)).toBeTruthy();
    expect(screen.getByText(/RT-003 ОТКРЫТ/)).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByTestId("intake-gate-table").querySelectorAll("tbody tr")).toHaveLength(
        INTAKE_GATE_KEYS.length,
      );
    });
    expect(screen.getAllByText("false").length).toBeGreaterThanOrEqual(INTAKE_GATE_KEYS.length);
    expect(screen.getByText(/Checkpoint GO/i)).toBeTruthy();
  });
});
