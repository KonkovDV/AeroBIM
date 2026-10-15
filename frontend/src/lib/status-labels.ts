/** Visible status words for jobs, coverage, and TZ git — not API enum dumps. */
import { UI_COPY } from "./ui-copy";

export function coverageStatusLabel(status: string): string {
  switch (status) {
    case "no_findings":
    case "done":
      return UI_COPY.covFilterNoFindings;
    case "findings":
      return UI_COPY.covFilterFindings;
    case "not_checked":
    case "not_done":
      return UI_COPY.covFilterNotChecked;
    case "insufficient_data":
    case "partial":
      return UI_COPY.covFilterInsufficient;
    case "expert_required":
    case "needs_expert":
      return UI_COPY.covFilterExpert;
    default:
      return status;
  }
}

export function coverageFamilyLabel(key: string): string {
  switch (key) {
    case "geometry":
      return UI_COPY.covFamilyGeometry;
    case "mep":
      return UI_COPY.covFamilyMep;
    case "drawing":
      return UI_COPY.covFamilyDrawing;
    case "ids":
      return "IDS";
    case "clash":
      return UI_COPY.covFamilyClash;
    default:
      return key.replaceAll("-", " ").replaceAll("_", " ");
  }
}

export function tzGitLabel(git: string): string {
  if (git === "partial") {
    return UI_COPY.tzGitPartial;
  }
  if (git === "missing") {
    return UI_COPY.tzGitMissing;
  }
  return git;
}

export function jobStatusLabel(status: string): string {
  switch (status.toLowerCase()) {
    case "queued":
      return UI_COPY.runJobQueued;
    case "pending":
      return UI_COPY.runJobPending;
    case "running":
      return UI_COPY.runJobRunning;
    case "succeeded":
      return UI_COPY.runJobSucceeded;
    case "failed":
      return UI_COPY.runJobFailed;
    case "cancelled":
      return UI_COPY.runJobCancelled;
    case "dead_letter":
      return UI_COPY.runJobDeadLetter;
    default:
      return status;
  }
}

export function claimLevelLabel(level: string): string {
  if (level === "not_ready") {
    return UI_COPY.blockersClaimNotReady;
  }
  return level;
}

export function divergenceResolutionLabel(value: string): string {
  if (value === "engine_wins") {
    return UI_COPY.capResolutionEngineWins;
  }
  return value;
}

export function intakeGateValueLabel(isTrue: boolean): string {
  return isTrue ? UI_COPY.blockersYes : UI_COPY.blockersNo;
}


/** Visual honesty class for findings/capabilities (K2A-P0-02a). Not a verdict. */
export type HonestyVisualClass =
	| "high"
	| "mid"
	| "abstain"
	| "skipped"
	| "failed"
	| "ok";

const CAPABILITY_TO_VISUAL: Record<string, HonestyVisualClass> = {
	ok: "ok",
	skipped: "skipped",
	failed: "failed",
	missing: "failed",
	not_verified: "abstain",
	not_implemented: "abstain",
};

/** One backend capability status → one UI class (NOT_VERIFIED ≠ FAILED). */
export function capabilityVisualClass(status: string): HonestyVisualClass {
	return CAPABILITY_TO_VISUAL[status.toLowerCase()] ?? "abstain";
}

/**
 * Confidence → CVD-safe band. Thresholds are **uncalibrated** defaults
 * (fixture/open only; not product accuracy). Hidden/customer must not tune them.
 */
export function confidenceVisualClass(
	confidence: number | null | undefined,
): HonestyVisualClass {
	if (confidence == null || Number.isNaN(confidence)) {
		return "abstain";
	}
	if (confidence < 0.6) {
		return "abstain";
	}
	if (confidence < 0.85) {
		return "mid";
	}
	return "high";
}

export function honestyVisualLabel(cls: HonestyVisualClass): string {
	switch (cls) {
		case "high":
			return "высокая";
		case "mid":
			return "средняя";
		case "abstain":
			return "отказ / не проверено";
		case "skipped":
			return "пропущено";
		case "failed":
			return "не выполнено";
		case "ok":
			return "выполнено";
		default:
			return cls;
	}
}
