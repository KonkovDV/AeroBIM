import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { fetchReport, fetchReviewEvents, postReviewEvent, type ReviewEventRow, type ReviewEventType } from "../lib/api";
import { asReviewEventRow, latestHitlState } from "../lib/hitl-state";
import type { ValidationIssue, ValidationReport } from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";

export type RemarkSaveState = "idle" | "saving" | "saved" | "failed";
export type HitlDecisionState = "idle" | "saving" | "accepted" | "rejected" | "failed";

export type SelectedReportState = {
  selectedReport: ValidationReport | null;
  reportLoading: boolean;
  reportError: string | null;
  reviewEvents: ReviewEventRow[];
  reviewEventsError: string | null;
  selectedIssueIndex: number;
  selectedClashIndex: number | null;
  remarkDraft: string;
  remarkSaveState: RemarkSaveState;
  hitlDecisionState: HitlDecisionState;
  setSelectedIssueIndex: Dispatch<SetStateAction<number>>;
  setSelectedClashIndex: Dispatch<SetStateAction<number | null>>;
  setRemarkDraft: Dispatch<SetStateAction<string>>;
  setRemarkSaveState: Dispatch<SetStateAction<RemarkSaveState>>;
  setHitlDecisionState: Dispatch<SetStateAction<HitlDecisionState>>;
  selectIssue: (index: number, issue: ValidationIssue) => void;
  saveRemarkEdit: (issue: ValidationIssue | null) => Promise<void>;
  decideRemark: (eventType: "accepted" | "rejected", issue: ValidationIssue | null) => Promise<void>;
};

/** Выбранный отчёт: загрузка, выбор замечания/клэша, черновик HITL-замечания и решения. */
export function useSelectedReport(
  selectedReportId: string | null,
  reloadEpoch = 0,
): SelectedReportState {
  const [selectedReport, setSelectedReport] = useState<ValidationReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [reviewEvents, setReviewEvents] = useState<ReviewEventRow[]>([]);
  const [reviewEventsError, setReviewEventsError] = useState<string | null>(null);
  const [selectedIssueIndex, setSelectedIssueIndex] = useState(0);
  const [selectedClashIndex, setSelectedClashIndex] = useState<number | null>(null);
  const [remarkDraft, setRemarkDraft] = useState("");
  const [remarkSaveState, setRemarkSaveState] = useState<RemarkSaveState>("idle");
  const [hitlDecisionState, setHitlDecisionState] = useState<HitlDecisionState>("idle");
  const reviewEventsRef = useRef<ReviewEventRow[]>([]);
  reviewEventsRef.current = reviewEvents;

  useEffect(() => {
    if (selectedReportId === null) {
      setSelectedReport(null);
      setReviewEvents([]);
      setReviewEventsError(null);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;
    setReportLoading(true);
    const eventsPromise = fetchReviewEvents(selectedReportId, { signal: controller.signal }).then(
      (payload) => ({ ok: true as const, payload }),
      (error: unknown) => ({ ok: false as const, error }),
    );
    fetchReport(selectedReportId, { signal: controller.signal })
      .then(async (report) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setSelectedReport(report);
        setReportError(null);
        setSelectedIssueIndex(0);
        setSelectedClashIndex(null);
        setRemarkDraft(report.issues[0]?.remark?.body ?? "");
        setRemarkSaveState("idle");
        setHitlDecisionState("idle");
        const eventsResult = await eventsPromise;
        if (cancelled || controller.signal.aborted) {
          return;
        }
        if (eventsResult.ok) {
          setReviewEvents(eventsResult.payload.events);
          setReviewEventsError(null);
        } else {
          setReviewEvents([]);
          setReviewEventsError(
            eventsResult.error instanceof Error ? eventsResult.error.message : UI_COPY.historyFailed,
          );
        }
      })
      .catch((error: unknown) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setReportError(error instanceof Error ? error.message : UI_COPY.loadReportFailed);
        setSelectedReport(null);
        setReviewEvents([]);
      })
      .finally(() => {
        if (!cancelled && !controller.signal.aborted) {
          setReportLoading(false);
        }
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [selectedReportId, reloadEpoch]);

  const selectIssue = useCallback((index: number, issue: ValidationIssue) => {
    setSelectedIssueIndex(index);
    setSelectedClashIndex(null);
    setRemarkDraft(issue.remark?.body ?? "");
    setRemarkSaveState("idle");
    setHitlDecisionState("idle");
  }, []);

  const rememberEvent = useCallback((event: Record<string, unknown>) => {
    const row = asReviewEventRow(event);
    if (row === null) {
      return;
    }
    setReviewEvents((current) => {
      if (current.some((item) => item.event_id === row.event_id)) {
        return current;
      }
      const next = [...current, row];
      reviewEventsRef.current = next;
      return next;
    });
  }, []);

  const postHitlEvent = useCallback(
    async (issue: ValidationIssue, eventType: ReviewEventType, note: string) => {
      if (!selectedReport) {
        return;
      }
      let previous = latestHitlState(reviewEventsRef.current, issue);
      if (previous === null && eventType !== "opened") {
        const opened = await postReviewEvent(selectedReport.report_id, {
          event_type: "opened",
          issue_rule_id: issue.rule_id,
          finding_id: issue.finding_id ?? undefined,
        });
        rememberEvent(opened.event);
        previous = "opened";
      }
      const result = await postReviewEvent(selectedReport.report_id, {
        event_type: eventType,
        issue_rule_id: issue.rule_id,
        finding_id: issue.finding_id ?? undefined,
        note,
        previous_state: previous ?? undefined,
      });
      rememberEvent(result.event);
    },
    [rememberEvent, selectedReport],
  );

  const saveRemarkEdit = useCallback(
    async (issue: ValidationIssue | null) => {
      if (!selectedReport || !issue) {
        return;
      }
      setRemarkSaveState("saving");
      try {
        await postHitlEvent(issue, "edited_remark", remarkDraft);
        setRemarkSaveState("saved");
      } catch {
        setRemarkSaveState("failed");
      }
    },
    [postHitlEvent, remarkDraft, selectedReport],
  );

  const decideRemark = useCallback(
    async (eventType: "accepted" | "rejected", issue: ValidationIssue | null) => {
      if (!selectedReport || !issue) {
        return;
      }
      setHitlDecisionState("saving");
      try {
        const note =
          eventType === "rejected" && !remarkDraft.trim() ? UI_COPY.rejectDefaultNote : remarkDraft;
        await postHitlEvent(issue, eventType, note);
        setHitlDecisionState(eventType);
      } catch {
        setHitlDecisionState("failed");
      }
    },
    [postHitlEvent, remarkDraft, selectedReport],
  );

  return {
    selectedReport,
    reportLoading,
    reportError,
    reviewEvents,
    reviewEventsError,
    selectedIssueIndex,
    selectedClashIndex,
    remarkDraft,
    remarkSaveState,
    hitlDecisionState,
    setSelectedIssueIndex,
    setSelectedClashIndex,
    setRemarkDraft,
    setRemarkSaveState,
    setHitlDecisionState,
    selectIssue,
    saveRemarkEdit,
    decideRemark,
  };
}
