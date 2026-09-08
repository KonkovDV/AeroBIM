import { startTransition, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import type { ValidationIssue } from "../../lib/types";
import {
  FINDING_GROUP_HEADER_HEIGHT,
  buildFindingListItems,
  buildItemOffsets,
  buildVisibleRuns,
  computeFindingWindow,
  computeScrollTopToRevealItem,
  findItemIndexForIssue,
} from "../../lib/finding-window";
import {
  CLAUSE_FILTER_ALL,
  CLAUSE_FILTER_MISSING,
  clauseFilterKey,
  clauseLine,
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
const DEFAULT_VIEWPORT_HEIGHT = 720;

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

/** Стабильный id заголовка группы: по ключу, а не по позиции в окне прокрутки. */
function groupHeaderId(groupKey: string): string {
  return `finding-group-${groupKey.replace(/\s+/g, "-") || "flat"}`;
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
  clauseFilter?: string;
  clauseOptions?: string[];
  onSeverityChange: (value: "all" | "error" | "warning" | "info") => void;
  onHitlOnlyChange: (value: boolean) => void;
  onSearchChange?: (value: string) => void;
  onGroupByChange: (value: FindingGroupBy) => void;
  onClauseChange?: (value: string) => void;
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
  const clause = clauseLine(issue);
  return (
    <button
      type="button"
      id={`finding-row-${index}`}
      role="option"
      aria-selected={selected}
      tabIndex={selected ? 0 : -1}
      className={`issue-card ${selected ? "active" : ""} ${issue.origin === "advisory" ? "issue-card--advisory" : ""}`}
      data-testid="issue-card"
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
        <span
          className={clauseFilterKey(issue) === CLAUSE_FILTER_MISSING ? "issue-location-missing" : undefined}
          data-testid="issue-clause"
        >
          {UI_COPY.findingClause(clause)}
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
  clauseFilter = CLAUSE_FILTER_ALL,
  clauseOptions = [],
  onSeverityChange,
  onHitlOnlyChange,
  onSearchChange,
  onGroupByChange,
  onClauseChange,
  onSelectIssue,
}: FindingListPanelProps) {
  // groupFindings() без useMemo пересчитывался каждый рендер и менял идентичность
  // groups, из-за чего useMemo ниже никогда не попадал в кэш.
  const groups = useMemo(() => groupFindings(issues, groupBy), [issues, groupBy]);
  const showHeaders = groupBy !== "none";
  const virtualize = issues.length > VIRTUALIZE_AFTER;
  const listRef = useRef<HTMLDivElement | null>(null);
  const skipScrollRef = useRef(false);
  const prevSelectedRef = useRef(selectedIssueIndex);
  const pendingFocusAfterScrollRef = useRef<number | null>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(DEFAULT_VIEWPORT_HEIGHT);
  const [itemHeight, setItemHeight] = useState(ITEM_HEIGHT);

  // Заголовок группы — такой же элемент списка, как строка. Поэтому окно
  // прокрутки считается по смешанному списку и группировка не пропадает.
  const items = useMemo(
    () => buildFindingListItems(groups, showHeaders),
    [groups, showHeaders],
  );
  const offsets = useMemo(
    () => buildItemOffsets(items, itemHeight, FINDING_GROUP_HEADER_HEIGHT),
    [items, itemHeight],
  );
  const selectedItemIndex = useMemo(
    () => findItemIndexForIssue(items, selectedIssueIndex),
    [items, selectedIssueIndex],
  );

  function applyMeasuredGeometry(node: HTMLDivElement): void {
    setViewportHeight(node.clientHeight || DEFAULT_VIEWPORT_HEIGHT);
    const card = node.querySelector(".issue-card");
    if (!(card instanceof HTMLElement) || card.offsetHeight < 8) {
      return;
    }
    const next = card.offsetHeight;
    setItemHeight((current) => (Math.abs(next - current) > 1 ? next : current));
  }

  useEffect(() => {
    const node = listRef.current;
    if (!node || !virtualize) {
      return;
    }
    const onScroll = () => setScrollTop(node.scrollTop);
    const measure = () => applyMeasuredGeometry(node);
    node.addEventListener("scroll", onScroll, { passive: true });
    measure();
    // Ширина панели меняет перенос текста; offsets нельзя оставлять на старой
    // высоте строки, иначе после ресайза появляются пропуски и наложения.
    if (typeof ResizeObserver === "function") {
      const observer = new ResizeObserver(measure);
      observer.observe(node);
      return () => {
        observer.disconnect();
        node.removeEventListener("scroll", onScroll);
      };
    }
    window.addEventListener("resize", measure);
    return () => {
      window.removeEventListener("resize", measure);
      node.removeEventListener("scroll", onScroll);
    };
  }, [virtualize]);

  useLayoutEffect(() => {
    const indexChanged = prevSelectedRef.current !== selectedIssueIndex;
    prevSelectedRef.current = selectedIssueIndex;
    const node = listRef.current;
    if (!node || !indexChanged) {
      return;
    }
    if (skipScrollRef.current) {
      skipScrollRef.current = false;
      pendingFocusAfterScrollRef.current = null;
      return;
    }
    if (virtualize) {
      const nextTop = computeScrollTopToRevealItem(
        offsets,
        selectedItemIndex,
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
  }, [selectedIssueIndex, virtualize, offsets, selectedItemIndex, viewportHeight]);

  useLayoutEffect(() => {
    const pending = pendingFocusAfterScrollRef.current;
    if (pending === null || scrollTop !== pending) {
      return;
    }
    pendingFocusAfterScrollRef.current = null;
    listRef.current?.querySelector<HTMLElement>(".issue-card.active")?.focus?.();
  }, [scrollTop]);

  useLayoutEffect(() => {
    const node = listRef.current;
    if (!node) {
      return;
    }
    applyMeasuredGeometry(node);
  }, [itemHeight, items, viewportHeight]);

  const viewWindow = virtualize
    ? computeFindingWindow(offsets, scrollTop, viewportHeight, OVERSCAN, selectedItemIndex)
    : { start: 0, end: items.length, padTop: 0, padBottom: 0 };
  const visibleRuns = buildVisibleRuns(items.slice(viewWindow.start, viewWindow.end));
  // Ссылаться на неотрисованный id нельзя: скринридер уводит фокус в пустоту.
  const selectedRendered =
    selectedItemIndex >= 0 &&
    selectedItemIndex >= viewWindow.start &&
    selectedItemIndex < viewWindow.end;

  function handleSelect(nextIndex: number, nextIssue: ValidationIssue): void {
    if (nextIndex !== selectedIssueIndex) {
      skipScrollRef.current = true;
    }
    onSelectIssue(nextIndex, nextIssue);
  }

  function renderRows(rows: IndexedIssue[]) {
    return rows.map(({ issue, index }) => (
      <IssueCard
        key={`${issue.rule_id}-${index}`}
        issue={issue}
        index={index}
        selected={index === selectedIssueIndex}
        onSelect={handleSelect}
      />
    ));
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
            <option value="clause">{UI_COPY.groupClause}</option>
          </select>
        </label>
        {onClauseChange ? (
          <label>
            {UI_COPY.filterClause}
            <select
              aria-label={UI_COPY.filterClause}
              aria-controls="finding-list"
              data-testid="clause-filter"
              value={clauseFilter}
              onChange={(event) => onClauseChange(event.target.value)}
            >
              <option value={CLAUSE_FILTER_ALL}>{UI_COPY.clauseAll}</option>
              <option value={CLAUSE_FILTER_MISSING}>{UI_COPY.clauseMissing}</option>
              {clauseOptions.map((key) => (
                <option key={key} value={key}>
                  {key}
                </option>
              ))}
            </select>
          </label>
        ) : null}
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

      <div
        className={`issue-list ${virtualize ? "issue-list-virtual" : ""}`}
        ref={listRef}
        id="finding-list"
        role="listbox"
        aria-label={UI_COPY.findingsListAria}
        data-item-height={itemHeight}
        aria-activedescendant={selectedRendered ? `finding-row-${selectedIssueIndex}` : undefined}
      >
        {issues.length === 0 ? (
          <div className="panel-empty compact">
            {UI_COPY.noFindings}
          </div>
        ) : (
          // role="presentation" обязателен: у listbox дочерними допустимы только
          // option и group, а распорка окна прокрутки — обычный div.
          <div
            role="presentation"
            style={
              virtualize
                ? { paddingTop: viewWindow.padTop, paddingBottom: viewWindow.padBottom }
                : undefined
            }
          >
            {visibleRuns.map((run) =>
              showHeaders ? (
                <section
                  key={run.groupKey || "flat"}
                  className="finding-group"
                  role="group"
                  aria-labelledby={run.headerCount === null ? undefined : groupHeaderId(run.groupKey)}
                >
                  {run.headerCount === null ? null : (
                    <h3 className="finding-group-title" id={groupHeaderId(run.groupKey)}>
                      {run.groupKey} ({run.headerCount})
                    </h3>
                  )}
                  {renderRows(run.rows)}
                </section>
              ) : (
                <section key={run.groupKey || "flat"} className="finding-group" role="presentation">
                  {renderRows(run.rows)}
                </section>
              ),
            )}
          </div>
        )}
      </div>
    </>
  );
}
