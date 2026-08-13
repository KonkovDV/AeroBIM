import type { PackageOutcome, ValidationIssue, ValidationReport } from "../lib/types";

export function formatPackageOutcome(
  outcome: PackageOutcome | null | undefined,
  passed: boolean,
): string {
  switch (outcome) {
    case "pass":
      return "PASS — нарушений не найдено (проверки выполнены)";
    case "pass_with_warnings":
      return "PASS_WITH_WARNINGS — есть предупреждения";
    case "review_required":
      return "REVIEW_REQUIRED — требуется эксперт";
    case "blocked":
      return "BLOCKED — проверка не завершена / данных недостаточно";
    case "failed":
      return "FAILED — ошибки или fail-closed";
    default:
      return passed ? "Passed (legacy)" : "Failed (legacy)";
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
}

function fragmentQuote(issue: ValidationIssue | null): string {
  const fromRemark = issue?.remark?.body?.trim();
  if (fromRemark) {
    return fromRemark;
  }
  return (issue?.message ?? "").trim() || "No fragment selected.";
}

function overlayHint(issue: ValidationIssue | null): string {
  const zone = issue?.problem_zone;
  if (!zone || zone.sheet_id == null) {
    return "No sheet overlay for this finding.";
  }
  const page = zone.page_number ?? "?";
  const hasBox =
    zone.x != null && zone.y != null && zone.width != null && zone.height != null;
  const box = hasBox ? ` · bbox (${zone.x}, ${zone.y}) ${zone.width}×${zone.height}` : "";
  return `Sheet ${zone.sheet_id} · page ${page}${box}`;
}

/**
 * KT#2 one-screen contract: original fragment, finding, evidence link, overlay
 * hint, and package outcome. Fixture demo — not customer accuracy.
 */
export default function VerticalSliceKt2({ report, issue }: VerticalSliceKt2Props) {
  const outcome = report.summary.outcome;
  const passed = report.summary.passed;
  const looksLikePass = passed === true || outcome === "pass" || outcome === "pass_with_warnings";

  return (
    <article className="kt2-slice" data-testid="kt2-vertical-slice">
      <p className="panel-kicker">KT#2 vertical slice (fixture)</p>
      <h3>Fragment → finding → evidence → verdict</h3>
      <p className="compact-copy">
        PDF text-layer / stamp-title path. Not trained CV. Not customer accuracy.
      </p>
      <p>
        <span>Package outcome</span>
        <strong
          className={`outcome-badge ${outcomeClass(outcome, passed)}`}
          data-testid="kt2-outcome"
        >
          {formatPackageOutcome(outcome, passed)}
        </strong>
      </p>
      {looksLikePass ? (
        <p className="compact-copy" role="status">
          Unexpected pass on this demo fixture — treat as a gate failure.
        </p>
      ) : (
        <p className="compact-copy" role="status">
          Verdict is not PASS. Shared-gate stays fail-closed.
        </p>
      )}
      <dl className="detail-grid">
        <div>
          <dt>Original fragment</dt>
          <dd>
            <blockquote className="kt2-slice-quote">{fragmentQuote(issue)}</blockquote>
          </dd>
        </div>
        <div>
          <dt>Finding</dt>
          <dd>
            <code>{issue?.finding_id?.trim() || "—"}</code>
            {issue?.rule_id ? ` · ${issue.rule_id}` : ""}
          </dd>
        </div>
        <div>
          <dt>Evidence</dt>
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
          <dt>Overlay</dt>
          <dd>{overlayHint(issue)}</dd>
        </div>
      </dl>
    </article>
  );
}
