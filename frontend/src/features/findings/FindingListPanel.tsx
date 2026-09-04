import { startTransition, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import type { ValidationIssue } from "../../lib/types";
import { computeScrollTopToReveal } from "../../lib/finding-scroll";
import {
  groupFindings,
  priorityCaption,
  spatialOrMissing,
  triageBand,
  type FindingGroupBy,
  type IndexedIssue,
  type TriageBand,
} from "../../lib/issue-triage";
import { UI_COPY } from "../../lib/ui-copy";

export const VIRTUALIZE_AFTER = 40;
const ITEM_HEIGHT = 148;
const OVERSCAN = 4;

/** UI3: severity по-русски — Блокирующее / Существенное / Информация. */
export function severityLabel(severity: ValidationIssue["severity"]): string {
  if (severity === "error") {
    return UI_COPY.severityError;
  }
  if (severity === "warning") {
    return UI_COPY.severityWarning;
  }
  return UI_COPY.severityInfo;
}

function triageBandLabel(band: TriageBand): string {
  if (band === "critical") {
    return UI_COPY.triageBandCritical;
  }
  if (band === "major") {
    return UI_COPY.triageBandMajor;
  }
  if (band === "minor") {
    return UI_COPY.triageBandMinor;
  }
  return UI_COPY.triageBandNegligible;
}

export type FindingListPanelProps = {
  issues: IndexedIssue[];
  totalIssueCount: number;
  selectedIssueIndex: number;
  issueSeverityFilter: "all" | "error" | "warning" | "info";
  hitlOnlyFilter: boolean;
  hitlRegionCount: number;
  searchQuery?: string;
  groupBy: FindingGroupBy;
  onSeverityChange: (value: "all" | "error" | "warning" | "info") => void;
  onHitlOnlyChange: (value: boolean) => void;
  onSearchChange?: (value: string) => void;
  onGroupByChange: (value: FindingGroupBy) => void;
  onSelectIssue: (index: number, issue: ValidationIssue) => void;
};

function IssueCard({
  issue,
  index,
  selected,
  onSelect,
}: {
  issue: ValidationIssue;
  index: number;
  selected: boolean;
  onSelect: (index: number, issue: ValidationIssue) => void;
}) {
  const band = triageBand(issue);
  const caption = priorityCaption(issue);
  const storey = spatialOrMissing(issue.storey_name ?? issue.remark?.storey_name);
  const axis = spatialOrMissing(issue.grid_axis ?? issue.remark?.grid_axis);
  return (
    <button
      type="button"
      tabIndex={selected ? 0 : -1}
      className={`issue-card ${selected ? "active" : ""} ${issue.origin === "advisory" ? "issue-card--advisory" : ""}`}
      onClick={() => {
        startTransition(() => {
          onSelect(index, issue);
        });
      }}
    >
      <div className="issue-card-row">
        <span className={`severity-pill severity-${issue.severity}`}>{severityLabel(issue.severity)}</span>
        {band ? <span className={`triage-band triage-band-${band}`}>{triageBandLabel(band)}</span> : null}
        <strong>{issue.rule_id}</strong>
        {issue.rule_id === "AEROBIM-DRAWING-REGION-HITL" ? (
          <span className="issue-priority">HITL</span>
        ) : null}
        {issue.origin === "advisory" ? (
          <span
            className="origin-pill origin-advisory"
            title={UI_COPY.advisoryTitle}
          >
            {UI_COPY.advisory}
          </span>
        ) : issue.origin === "deterministic" ? (
          <span className="origin-pill origin-deterministic">{UI_COPY.deterministic}</span>
        ) : null}
        {typeof issue.confidence === "number" && issue.confidence < 0.6 ? (
          <span
            className="confidence-pill confidence-low"
            title={UI_COPY.lowConfidenceTitle}
          >
            {UI_COPY.lowConfidence(issue.confidence.toFixed(2))}
          </span>
        ) : null}
        {typeof issue.priority === "number" && issue.priority > 0 ? (
          <span className="issue-priority">P{issue.priority}</span>
        ) : null}
      </div>
      <p>{issue.message}</p>
      <div className="issue-card-meta">
        <span>{issue.category}</span>
        <span>{issue.target_ref ?? issue.element_guid ?? UI_COPY.noTarget}</span>
      </div>
      <div className="issue-card-meta issue-card-location" data-testid="issue-location">
        <span className={storey === UI_COPY.spatialMissing ? "issue-location-missing" : undefined}>
          {UI_COPY.findingStorey(storey)}
        </span>
        <span className={axis === UI_COPY.spatialMissing ? "issue-location-missing" : undefined}>
          {UI_COPY.findingAxis(axis)}
        </span>
      </div>
      {caption ? <p className="compact-copy">{caption}</p> : null}
    </button>
  );
}

export default function FindingListPanel({
  issues,
  totalIssueCount,
  selectedIssueIndex,
  issueSeverityFilter,
  hitlOnlyFilter,
  hitlRegionCount,
  searchQuery,
  groupBy,
  onSeverityChange,
  onHitlOnlyChange,
  onSearchChange,
  onGroupByChange,
  onSelectIssue,
}: FindingListPanelProps) {
  const groups = groupFindings(issues, groupBy);
  const flat = useMemo(() => groups.flatMap((group) => group.rows), [groups]);
  const virtualize = flat.length > VIRTUALIZE_AFTER;
  const listRef = useRef<HTMLDivElement | null>(null);
  const skipScrollRef = useRef(false);
  const prevSelectedRef = useRef(selectedIssueIndex);
  const pendingFocusAfterScrollRef = useRef<number | null>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(720);

  useEffect(() => {
    const node = listRef.current;
    if (!node || !virtualize) {
      return;
    }
    const onScroll = () => setScrollTop(node.scrollTop);
    node.addEventListener("scroll", onScroll, { passive: true });
    setViewportHeight(node.clientHeight || 720);
    return () => node.removeEventListener("scroll", onScroll);
  }, [virtualize]);

  useLayoutEffect(() => {
    const indexChanged = prevSelectedRef.current !== selectedIssueIndex;
    prevSelectedRef.current = selectedIssueIndex;
    const node = listRef.current;
    if (!node || !indexChanged) {
      return;
    }
    const selectedPos = flat.findIndex((row) => row.index === selectedIssueIndex);
    if (skipScrollRef.current) {
      skipScrollRef.current = false;
      pendingFocusAfterScrollRef.current = null;
      return;
    }
    if (virtualize) {
      const nextTop = computeScrollTopToReveal(
        selectedPos,
        ITEM_HEIGHT,
        node.clientHeight || viewportHeight,
        node.scrollTop,
      );
      if (nextTop !== node.scrollTop) {
        pendingFocusAfterScrollRef.current = nextTop;
        node.scrollTop = nextTop;
        setScrollTop(nextTop);
        return;
      }
    } else {
      const activeCard = node.querySelector<HTMLElement>(".issue-card.active");
      activeCard?.scrollIntoView?.({ block: "nearest" });
    }
    node.querySelector<HTMLElement>(".issue-card.active")?.focus?.();
  }, [selectedIssueIndex, virtualize, flat, viewportHeight]);

  useLayoutEffect(() => {
    const pending = pendingFocusAfterScrollRef.current;
    if (pending === null || scrollTop !== pending) {
      return;
    }
    pendingFocusAfterScrollRef.current = null;
    listRef.current?.querySelector<HTMLElement>(".issue-card.active")?.focus?.();
  }, [scrollTop]);

  let visible = flat;
  let padTop = 0;
  let padBottom = 0;
  if (virtualize) {
    const selectedPos = Math.max(
      0,
      flat.findIndex((row) => row.index === selectedIssueIndex),
    );
    const visibleCount = Math.max(1, Math.ceil(viewportHeight / ITEM_HEIGHT));
    let start = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - OVERSCAN);
    let end = Math.min(flat.length, start + visibleCount + OVERSCAN * 2);
    start = Math.min(start, Math.max(0, selectedPos - OVERSCAN));
    end = Math.max(end, Math.min(flat.length, selectedPos + OVERSCAN + 1));
    visible = flat.slice(start, end);
    padTop = start * ITEM_HEIGHT;
    padBottom = (flat.length - end) * ITEM_HEIGHT;
  }

  return (
    <>
      <div className="issue-toolbar">
        {onSearchChange ? (
          <label className="issue-search">
            {UI_COPY.searchFindings}
            <input
              type="search"
              value={searchQuery ?? ""}
              placeholder={UI_COPY.searchFindingsPh}
              aria-label={UI_COPY.searchFindings}
              onChange={(event) => onSearchChange(event.target.value)}
            />
          </label>
        ) : null}
        <label>
          {UI_COPY.severity}
          <select
            value={issueSeverityFilter}
            onChange={(event) =>
              onSeverityChange(event.target.value as "all" | "error" | "warning" | "info")
            }
          >
            <option value="all">{UI_COPY.severityAll}</option>
            <option value="error">{UI_COPY.severityError}</option>
            <option value="warning">{UI_COPY.severityWarning}</option>
            <option value="info">{UI_COPY.severityInfo}</option>
          </select>
        </label>
        <label>
          {UI_COPY.groupFindings}
          <select
            aria-label={UI_COPY.groupFindings}
            value={groupBy}
            onChange={(event) => onGroupByChange(event.target.value as FindingGroupBy)}
          >
            <option value="none">{UI_COPY.groupNone}</option>
            <option value="rule">{UI_COPY.groupRule}</option>
            <option value="storey">{UI_COPY.groupStorey}</option>
            <option value="axis">{UI_COPY.groupAxis}</option>
            <option value="discipline">{UI_COPY.groupCategory}</option>
          </select>
        </label>
        <label className="hitl-filter">
          <input
            type="checkbox"
            checked={hitlOnlyFilter}
            onChange={(event) => onHitlOnlyChange(event.target.checked)}
          />
          {UI_COPY.hitlOnly}
          {hitlRegionCount > 0 ? ` (${hitlRegionCount})` : ""}
        </label>
        <span className="compact-copy" role="status" aria-live="polite">
          {UI_COPY.shownCount(issues.length, totalIssueCount, virtualize)}
        </span>
      </div>

      <div className={`issue-list ${virtualize ? "issue-list-virtual" : ""}`} ref={listRef}>
        {issues.length === 0 ? (
          <div className="panel-empty compact">
            {UI_COPY.noFindings}
          </div>
        ) : virtualize ? (
          <div style={{ paddingTop: padTop, paddingBottom: padBottom }}>
            {visible.map(({ issue, index }) => (
              <IssueCard
                key={`${issue.rule_id}-${index}`}
                issue={issue}
                index={index}
                selected={index === selectedIssueIndex}
                onSelect={(nextIndex, nextIssue) => {
                  if (nextIndex !== selectedIssueIndex) {
                    skipScrollRef.current = true;
                  }
                  onSelectIssue(nextIndex, nextIssue);
                }}
              />
            ))}
          </div>
        ) : (
          groups.map((group) => (
            <section key={group.key || "flat"} className="finding-group">
              {groupBy !== "none" ? (
                <h3 className="finding-group-title">
                  {group.key} ({group.rows.length})
                </h3>
              ) : null}
              {group.rows.map(({ issue, index }) => (
                <IssueCard
                  key={`${issue.rule_id}-${index}`}
                  issue={issue}
                  index={index}
                  selected={index === selectedIssueIndex}
                  onSelect={(nextIndex, nextIssue) => {
                    if (nextIndex !== selectedIssueIndex) {
                      skipScrollRef.current = true;
                    }
                    onSelectIssue(nextIndex, nextIssue);
                  }}
                />
              ))}
            </section>
          ))
        )}
      </div>
    </>
  );
}
