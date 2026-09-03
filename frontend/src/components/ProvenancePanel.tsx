import type { ValidationIssue } from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";

export function isFindingAuditReady(issue: ValidationIssue): boolean {
  return Boolean(
    (issue.finding_id ?? "").trim() &&
      (issue.source_id ?? "").trim() &&
      (issue.evidence_refs?.length ?? 0) > 0,
  );
}

function dash(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const text = String(value).trim();
  return text.length > 0 ? text : "—";
}

export interface ProvenancePanelProps {
  activeIssue: ValidationIssue | null;
}

export default function ProvenancePanel({ activeIssue }: ProvenancePanelProps) {
  if (!activeIssue) {
    return (
      <article className="detail-block" data-testid="provenance-active-issue">
        <h3>{UI_COPY.activeIssue}</h3>
        <p className="compact-copy">{UI_COPY.noActiveIssue}</p>
      </article>
    );
  }

  const auditReady = isFindingAuditReady(activeIssue);
  const zone = activeIssue.problem_zone;
  const bbox =
    zone && zone.x != null && zone.y != null && zone.width != null && zone.height != null
      ? `(${zone.x}, ${zone.y}) ${zone.width}×${zone.height}`
      : null;

  return (
    <article className="detail-block" data-testid="provenance-active-issue">
      <h3>{UI_COPY.activeIssue}</h3>
      {!auditReady && (
        <p className="provenance-gap-banner" role="status">
          {UI_COPY.provenanceGap}
        </p>
      )}
      {auditReady && (
        <p className="provenance-ok-banner" role="status">
          {UI_COPY.provenanceOk}
        </p>
      )}
      <dl className="detail-grid">
        <div>
          <dt>{UI_COPY.provFindingId}</dt>
          <dd>
            <code>{dash(activeIssue.finding_id)}</code>
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.provSourceId}</dt>
          <dd>
            <code>{dash(activeIssue.source_id)}</code>
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.provEvidenceRefs}</dt>
          <dd>
            {(activeIssue.evidence_refs?.length ?? 0) > 0 ? (
              <ul className="evidence-ref-list">
                {activeIssue.evidence_refs!.map((ref) => (
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
          <dt>{UI_COPY.provRule}</dt>
          <dd>{activeIssue.rule_id}</dd>
        </div>
        <div>
          <dt>{UI_COPY.provCategory}</dt>
          <dd>{activeIssue.category}</dd>
        </div>
        <div>
          <dt>{UI_COPY.provPriority}</dt>
          <dd>{dash(activeIssue.priority)}</dd>
        </div>
        <div>
          <dt>{UI_COPY.provConflictKind}</dt>
          <dd>{dash(activeIssue.conflict_kind)}</dd>
        </div>
        <div>
          <dt>{UI_COPY.provEntity}</dt>
          <dd>{dash(activeIssue.ifc_entity)}</dd>
        </div>
        <div>
          <dt>GlobalId</dt>
          <dd>
            <code>{dash(activeIssue.element_guid)}</code>
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.provTarget}</dt>
          <dd>{dash(activeIssue.target_ref)}</dd>
        </div>
        <div>
          <dt>{UI_COPY.provProperty}</dt>
          <dd>
            {dash(activeIssue.property_set)}
            {activeIssue.property_name ? ` · ${activeIssue.property_name}` : ""}
            {activeIssue.operator ? ` · ${activeIssue.operator}` : ""}
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.provExpected}</dt>
          <dd>{dash(activeIssue.expected_value)}</dd>
        </div>
        <div>
          <dt>{UI_COPY.provObserved}</dt>
          <dd>{dash(activeIssue.observed_value)}</dd>
        </div>
        <div>
          <dt>{UI_COPY.provUnit}</dt>
          <dd>{dash(activeIssue.unit)}</dd>
        </div>
        <div>
          <dt>{UI_COPY.provEvidenceModality}</dt>
          <dd>{dash(activeIssue.evidence_modality)}</dd>
        </div>
        <div>
          <dt>{UI_COPY.provConfidence}</dt>
          <dd>
            {activeIssue.confidence == null ? "—" : activeIssue.confidence.toFixed(3)}
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.provNorm}</dt>
          <dd>
            {[activeIssue.norm_source, activeIssue.norm_edition, activeIssue.norm_clause]
              .filter(Boolean)
              .join(" · ") || "—"}
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.provApproval}</dt>
          <dd>
            {dash(activeIssue.approval_status)}
            {activeIssue.approval_ref ? ` · ${activeIssue.approval_ref}` : ""}
          </dd>
        </div>
        <div>
          <dt>RASE</dt>
          <dd>
            {(activeIssue.rase_elements?.length ?? 0) > 0
              ? activeIssue.rase_elements!.join(", ")
              : dash(activeIssue.rase_summary)}
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.provTenantProject}</dt>
          <dd>
            {dash(activeIssue.tenant_id)} / {dash(activeIssue.project_id)}
          </dd>
        </div>
        <div>
          <dt>{UI_COPY.provProblemZone}</dt>
          <dd>
            {zone
              ? `${zone.sheet_id ?? "лист?"} · стр. ${zone.page_number ?? "?"}${
                  bbox ? ` · bbox ${bbox}` : ""
                }`
              : "—"}
          </dd>
        </div>
      </dl>
    </article>
  );
}
