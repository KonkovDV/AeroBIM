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
