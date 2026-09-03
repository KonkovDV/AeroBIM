import type { CSSProperties } from "react";
import type { PackageOutcome, ProblemZone, ValidationIssue, ValidationReport } from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";

export function formatPackageOutcome(
  outcome: PackageOutcome | null | undefined,
  passed: boolean,
): string {
  switch (outcome) {
    case "pass":
      return UI_COPY.outcomePass;
    case "pass_with_warnings":
      return UI_COPY.outcomePassWarnings;
    case "review_required":
      return UI_COPY.outcomeReview;
    case "blocked":
      return UI_COPY.outcomeBlocked;
    case "failed":
      return UI_COPY.outcomeFailed;
    default:
      return passed ? UI_COPY.outcomeLegacyPass : UI_COPY.outcomeLegacyFail;
  }
}

/** Colour class so FAILED (violation) is distinct from BLOCKED (missing data). */
export function outcomeClass(
  outcome: PackageOutcome | null | undefined,
  passed: boolean,
): string {
  switch (outcome) {
    case "pass":
      return "outcome-pass";
    case "pass_with_warnings":
      return "outcome-warn";
    case "review_required":
      return "outcome-review";
    case "blocked":
      return "outcome-block";
    case "failed":
      return "outcome-fail";
    default:
      return passed ? "outcome-pass" : "outcome-block";
  }
}

export interface VerticalSliceKt2Props {
  report: ValidationReport;
  issue: ValidationIssue | null;
  /** Sibling overlay PNG from the demo CLI, when the review shell has it. */
  overlaySrc?: string;
}

/** Letter-size page used by the fixture PDF generator (points). Not a measured customer sheet. */
export const KT2_OVERLAY_PAGE = { width: 612, height: 792 } as const;

export function overlayRectStyle(zone: ProblemZone | null | undefined): CSSProperties | null {
  if (
    zone == null ||
    zone.x == null ||
    zone.y == null ||
    zone.width == null ||
    zone.height == null ||
    zone.width <= 0 ||
    zone.height <= 0
  ) {
    return null;
  }
  return {
    left: `${(zone.x / KT2_OVERLAY_PAGE.width) * 100}%`,
    top: `${(zone.y / KT2_OVERLAY_PAGE.height) * 100}%`,
    width: `${(zone.width / KT2_OVERLAY_PAGE.width) * 100}%`,
    height: `${(zone.height / KT2_OVERLAY_PAGE.height) * 100}%`,
  };
}

function fragmentQuote(issue: ValidationIssue | null): string {
  const fromRemark = issue?.remark?.body?.trim();
  if (fromRemark) {
    return fromRemark;
  }
  return (issue?.message ?? "").trim() || UI_COPY.kt2NoFragment;
}

function overlayHint(issue: ValidationIssue | null): string {
  const zone = issue?.problem_zone;
  if (!zone || zone.sheet_id == null) {
    return UI_COPY.kt2NoOverlay;
  }
  const page = String(zone.page_number ?? "?");
  const hasBox =
    zone.x != null && zone.y != null && zone.width != null && zone.height != null;
  const box = hasBox ? ` · bbox (${zone.x}, ${zone.y}) ${zone.width}×${zone.height}` : "";
  return UI_COPY.kt2SheetPage(zone.sheet_id, page, box);
}

/**
 * KT#2 one-screen contract: original fragment, finding, evidence link, overlay
 * hint, and package outcome. Fixture demo — not customer accuracy.
 */
export default function VerticalSliceKt2({
  report,
  issue,
  overlaySrc,
}: VerticalSliceKt2Props) {
  const outcome = report.summary.outcome;
  const passed = report.summary.passed;
  const looksLikePass = passed === true || outcome === "pass" || outcome === "pass_with_warnings";
  const rectStyle = overlayRectStyle(issue?.problem_zone);

  return (
    <article className="kt2-slice" data-testid="kt2-vertical-slice">
      <p className="panel-kicker">{UI_COPY.kt2Kicker}</p>
      <h3>{UI_COPY.kt2Title}</h3>
      <p className="compact-copy">{UI_COPY.kt2Body}</p>
      <p>
        <span>{UI_COPY.kt2Outcome}</span>
        <strong
          className={`outcome-badge ${outcomeClass(outcome, passed)}`}
          data-testid="kt2-outcome"
        >
          {formatPackageOutcome(outcome, passed)}
        </strong>
      </p>
      {looksLikePass ? (
        <p className="compact-copy" role="status">
          {UI_COPY.kt2UnexpectedPass}
        </p>
      ) : (
        <p className="compact-copy" role="status">
          {UI_COPY.kt2NotPass}
        </p>
      )}
      <dl className="detail-grid">
        <div>
          <dt>{UI_COPY.kt2Fragment}</dt>
          <dd>
            <blockquote className="kt2-slice-quote">{fragmentQuote(issue)}</blockquote>
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.kt2Finding}</dt>
          <dd>
            <code>{issue?.finding_id?.trim() || "—"}</code>
            {issue?.source_id?.trim() ? (
              <>
                {" · source_id "}
                <code>{issue.source_id.trim()}</code>
              </>
            ) : null}
            {issue?.rule_id ? ` · ${issue.rule_id}` : ""}
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.kt2Evidence}</dt>
          <dd>
            {(issue?.evidence_refs?.length ?? 0) > 0 ? (
              <ul className="evidence-ref-list">
                {issue!.evidence_refs!.map((ref) => (
                  <li key={ref}>
                    <code>{ref}</code>
                  </li>
                ))}
              </ul>
            ) : (
              "—"
            )}
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.kt2Overlay}</dt>
          <dd>
            <figure className="kt2-overlay" data-testid="kt2-overlay">
              {overlaySrc ? (
                <img
                  src={overlaySrc}
                  alt={UI_COPY.kt2Alt}
                />
              ) : rectStyle ? (
                <div className="kt2-overlay-sheet" data-testid="kt2-overlay-bbox">
                  <div className="kt2-overlay-rect" style={rectStyle} />
                </div>
              ) : null}
              <figcaption>{overlayHint(issue)} · {UI_COPY.kt2Deterministic}</figcaption>
            </figure>
          </dd>
        </div>
      </dl>
    </article>
  );
}
