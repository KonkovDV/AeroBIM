import { describe, expect, it } from "vitest";
import {
	capabilityVisualClass,
	confidenceVisualClass,
	honestyVisualLabel,
} from "./status-labels";

describe("honesty visual mapping (K2A-P0-02a)", () => {
	it("maps NOT_VERIFIED/SKIPPED away from FAILED", () => {
		expect(capabilityVisualClass("not_verified")).toBe("abstain");
		expect(capabilityVisualClass("skipped")).toBe("skipped");
		expect(capabilityVisualClass("failed")).toBe("failed");
		expect(capabilityVisualClass("ok")).toBe("ok");
		expect(capabilityVisualClass("not_implemented")).toBe("abstain");
	});

	it("marks missing confidence as abstain (uncalibrated honesty)", () => {
		expect(confidenceVisualClass(null)).toBe("abstain");
		expect(confidenceVisualClass(undefined)).toBe("abstain");
		expect(confidenceVisualClass(0.42)).toBe("abstain");
		expect(confidenceVisualClass(0.7)).toBe("mid");
		expect(confidenceVisualClass(0.95)).toBe("high");
	});

	it("exposes non-color label for every class", () => {
		for (const cls of ["high", "mid", "abstain", "skipped", "failed", "ok"] as const) {
			expect(honestyVisualLabel(cls).length).toBeGreaterThan(0);
		}
	});
});
