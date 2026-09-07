import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import {
  ApiHttpError,
  fetchReport,
  fetchReviewEvents,
  postReviewEvent,
  type ReviewEventRow,
  type ReviewEventType,
} from "../lib/api";
import {
  asReviewEventRow,
  effectiveRemarkText,
  hitlOperationFingerprint,
  latestHitlState,
  latestReviewSequence,
} from "../lib/hitl-state";
import type { ValidationIssue, ValidationReport } from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";

export type RemarkSaveState = "idle" | "saving" | "saved" | "failed";
export type HitlDecisionState = "idle" | "saving" | "accepted" | "rejected" | "failed";

/**
 * Ключ идемпотентности для событий HITL.
 *
 * crypto.randomUUID есть только на защищённом источнике (https или localhost).
 * На http-хосте в лаборатории его нет, поэтому нужен запасной вариант — иначе
 * запись решения эксперта падала уже ПОСЛЕ успешного POST.
 */
function newHitlIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `hitl-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export type PendingFindingSelect = { index: number; issue: ValidationIssue };

export type SelectedReportState = {
  selectedReport: ValidationReport | null;
  reportLoading: boolean;
  reportError: string | null;
  reviewEvents: ReviewEventRow[];
  reviewEventsError: string | null;
  historyPending: boolean;
  selectedIssueIndex: number;
  selectedClashIndex: number | null;
  remarkDraft: string;
  remarkSaveState: RemarkSaveState;
  hitlDecisionState: HitlDecisionState;
  pendingSelect: PendingFindingSelect | null;
  conflictMessage: string | null;
  setSelectedIssueIndex: Dispatch<SetStateAction<number>>;
  setSelectedClashIndex: Dispatch<SetStateAction<number | null>>;
  setRemarkDraft: Dispatch<SetStateAction<string>>;
  setRemarkSaveState: Dispatch<SetStateAction<RemarkSaveState>>;
  setHitlDecisionState: Dispatch<SetStateAction<HitlDecisionState>>;
  selectIssue: (index: number, issue: ValidationIssue, options?: { force?: boolean }) => void;
  confirmPendingSelect: (mode: "save" | "discard") => Promise<void>;
  dismissPendingSelect: () => void;
  saveRemarkEdit: (issue: ValidationIssue | null) => Promise<boolean>;
  decideRemark: (eventType: "accepted" | "rejected", issue: ValidationIssue | null) => Promise<void>;
  isDirty: boolean;
};

function resetEditor(
  setSelectedReport: Dispatch<SetStateAction<ValidationReport | null>>,
  setReviewEvents: Dispatch<SetStateAction<ReviewEventRow[]>>,
  setReviewEventsError: Dispatch<SetStateAction<string | null>>,
  setReportError: Dispatch<SetStateAction<string | null>>,
  setRemarkDraft: Dispatch<SetStateAction<string>>,
  setRemarkSaveState: Dispatch<SetStateAction<RemarkSaveState>>,
  setHitlDecisionState: Dispatch<SetStateAction<HitlDecisionState>>,
  setPendingSelect: Dispatch<SetStateAction<PendingFindingSelect | null>>,
  setConflictMessage: Dispatch<SetStateAction<string | null>>,
): void {
  setSelectedReport(null);
  setReviewEvents([]);
  setReviewEventsError(null);
  setReportError(null);
  setRemarkDraft("");
  setRemarkSaveState("idle");
  setHitlDecisionState("idle");
  setPendingSelect(null);
  setConflictMessage(null);
}

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
  const [historyPending, setHistoryPending] = useState(false);
  const [selectedIssueIndex, setSelectedIssueIndex] = useState(0);
  const [selectedClashIndex, setSelectedClashIndex] = useState<number | null>(null);
  const [remarkDraft, setRemarkDraft] = useState("");
  const [remarkSaveState, setRemarkSaveState] = useState<RemarkSaveState>("idle");
  const [hitlDecisionState, setHitlDecisionState] = useState<HitlDecisionState>("idle");
  const [pendingSelect, setPendingSelect] = useState<PendingFindingSelect | null>(null);
  const [conflictMessage, setConflictMessage] = useState<string | null>(null);
  const reviewEventsRef = useRef<ReviewEventRow[]>([]);
  const selectedReportRef = useRef<ValidationReport | null>(null);
  const selectedIssueIndexRef = useRef(0);
  const remarkDraftRef = useRef("");
  const hitlOpRef = useRef<{ fingerprint: string; key: string } | null>(null);
  const hitlBusyRef = useRef(false);
  const historyPendingRef = useRef(false);

  selectedReportRef.current = selectedReport;
  selectedIssueIndexRef.current = selectedIssueIndex;
  remarkDraftRef.current = remarkDraft;

  useEffect(() => {
    reviewEventsRef.current = reviewEvents;
  }, [reviewEvents]);

  useEffect(() => {
    if (selectedReportId === null) {
      resetEditor(
        setSelectedReport,
        setReviewEvents,
        setReviewEventsError,
        setReportError,
        setRemarkDraft,
        setRemarkSaveState,
        setHitlDecisionState,
        setPendingSelect,
        setConflictMessage,
      );
      setReportLoading(false);
      historyPendingRef.current = false;
      setHistoryPending(false);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;
    historyPendingRef.current = true;
    setHistoryPending(true);
    resetEditor(
      setSelectedReport,
      setReviewEvents,
      setReviewEventsError,
      setReportError,
      setRemarkDraft,
      setRemarkSaveState,
      setHitlDecisionState,
      setPendingSelect,
      setConflictMessage,
    );
    selectedReportRef.current = null;
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
        selectedReportRef.current = report;
        setReportError(null);
        setSelectedIssueIndex(0);
        setSelectedClashIndex(null);
        const firstIssue = report.issues[0];
        setRemarkDraft(firstIssue ? effectiveRemarkText(firstIssue, []) : "");
        setRemarkSaveState("idle");
        setHitlDecisionState("idle");
        setReportLoading(false);
        const eventsResult = await eventsPromise;
        if (cancelled || controller.signal.aborted) {
          return;
        }
        if (eventsResult.ok) {
          setReviewEvents(eventsResult.payload.events);
          setReviewEventsError(null);
          const current = selectedReportRef.current?.issues[selectedIssueIndexRef.current];
          if (current) {
            const withoutEvents = effectiveRemarkText(current, []);
            if (remarkDraftRef.current === withoutEvents) {
              setRemarkDraft(effectiveRemarkText(current, eventsResult.payload.events));
            }
          }
        } else {
          setReviewEvents([]);
          setReviewEventsError(
            eventsResult.error instanceof Error ? eventsResult.error.message : UI_COPY.historyFailed,
          );
        }
        historyPendingRef.current = false;
        setHistoryPending(false);
      })
      .catch((error: unknown) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setReportError(error instanceof Error ? error.message : UI_COPY.loadReportFailed);
        setSelectedReport(null);
        selectedReportRef.current = null;
        setReviewEvents([]);
        historyPendingRef.current = false;
        setHistoryPending(false);
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

  const applySelect = useCallback((index: number, issue: ValidationIssue) => {
    setSelectedIssueIndex(index);
    setSelectedClashIndex(null);
    setRemarkDraft(effectiveRemarkText(issue, reviewEventsRef.current));
    setRemarkSaveState("idle");
    setHitlDecisionState("idle");
    setPendingSelect(null);
    setConflictMessage(null);
  }, []);

  const selectIssue = useCallback(
    (index: number, issue: ValidationIssue, options?: { force?: boolean }) => {
      const current = selectedReportRef.current?.issues[selectedIssueIndexRef.current];
      const original = current ? effectiveRemarkText(current, reviewEventsRef.current) : "";
      const dirty = remarkDraftRef.current !== original;
      if (dirty && options?.force !== true) {
        setPendingSelect({ index, issue });
        return;
      }
      applySelect(index, issue);
    },
    [applySelect],
  );

  const rememberEvent = useCallback((event: Record<string, unknown>, reportId: string) => {
    if (selectedReportRef.current?.report_id !== reportId) {
      return;
    }
    const row = asReviewEventRow(event);
    if (row === null) {
      return;
    }
    if (!reviewEventsRef.current.some((item) => item.event_id === row.event_id)) {
      reviewEventsRef.current = [...reviewEventsRef.current, row];
    }
    setReviewEvents((current) =>
      current.some((item) => item.event_id === row.event_id) ? current : [...current, row],
    );
  }, []);

  const keyForFingerprint = (fingerprint: string): string => {
    if (hitlOpRef.current?.fingerprint === fingerprint) {
      return hitlOpRef.current.key;
    }
    const key = newHitlIdempotencyKey();
    hitlOpRef.current = { fingerprint, key };
    return key;
  };

  const postHitlEvent = useCallback(
    async (issue: ValidationIssue, eventType: ReviewEventType, note: string, reportId: string) => {
      let previous = latestHitlState(reviewEventsRef.current, issue);
      if (previous === null && eventType !== "opened") {
        const openedVersion = latestReviewSequence(reviewEventsRef.current, issue) ?? 0;
        const openedFingerprint = hitlOperationFingerprint({
          reportId,
          findingId: issue.finding_id ?? "",
          eventType: "opened",
          note: "",
          previousState: "",
          expectedReviewVersion: openedVersion,
        });
        const opened = await postReviewEvent(reportId, {
          event_type: "opened",
          issue_rule_id: issue.rule_id,
          finding_id: issue.finding_id ?? undefined,
          idempotency_key: keyForFingerprint(openedFingerprint),
          expected_review_version: openedVersion,
        });
        hitlOpRef.current = null;
        rememberEvent(opened.event, reportId);
        previous = "opened";
      }
      const expectedReviewVersion = latestReviewSequence(reviewEventsRef.current, issue) ?? 0;
      const fingerprint = hitlOperationFingerprint({
        reportId,
        findingId: issue.finding_id ?? "",
        eventType,
        note,
        previousState: previous ?? "",
        expectedReviewVersion,
      });
      const result = await postReviewEvent(reportId, {
        event_type: eventType,
        issue_rule_id: issue.rule_id,
        finding_id: issue.finding_id ?? undefined,
        note,
        previous_state: previous ?? undefined,
        idempotency_key: keyForFingerprint(fingerprint),
        expected_review_version: expectedReviewVersion,
      });
      rememberEvent(result.event, reportId);
      hitlOpRef.current = null;
    },
    [rememberEvent],
  );

  const stillOnFinding = (reportId: string, issue: ValidationIssue): boolean => {
    if (selectedReportRef.current?.report_id !== reportId) {
      return false;
    }
    const current = selectedReportRef.current?.issues[selectedIssueIndexRef.current];
    return (current?.finding_id ?? current?.rule_id) === (issue.finding_id ?? issue.rule_id);
  };

  const saveRemarkEdit = useCallback(
    async (issue: ValidationIssue | null): Promise<boolean> => {
      const report = selectedReportRef.current;
      if (!report || !issue || reportLoading || historyPendingRef.current || hitlBusyRef.current) {
        return false;
      }
      const draft = remarkDraftRef.current;
      if (!draft.trim()) {
        return false;
      }
      const reportId = report.report_id;
      hitlBusyRef.current = true;
      setRemarkSaveState("saving");
      try {
        await postHitlEvent(issue, "edited_remark", draft, reportId);
        if (!stillOnFinding(reportId, issue)) {
          return true;
        }
        // The response confirms the submitted draft, not text typed while saving.
        const draftUnchanged = remarkDraftRef.current === draft;
        setRemarkSaveState(draftUnchanged ? "saved" : "idle");
        setConflictMessage(null);
        return draftUnchanged;
      } catch (error: unknown) {
        if (!stillOnFinding(reportId, issue)) {
          return false;
        }
        setRemarkSaveState("failed");
        if (error instanceof ApiHttpError && error.status === 409) {
          setConflictMessage(UI_COPY.hitlConflict);
        }
        return false;
      } finally {
        hitlBusyRef.current = false;
      }
    },
    [postHitlEvent, reportLoading],
  );

  const decideRemark = useCallback(
    async (eventType: "accepted" | "rejected", issue: ValidationIssue | null) => {
      const report = selectedReportRef.current;
      if (!report || !issue || reportLoading || historyPendingRef.current || hitlBusyRef.current) {
        return;
      }
      const reportId = report.report_id;
      const draft = remarkDraftRef.current;
      hitlBusyRef.current = true;
      setHitlDecisionState("saving");
      try {
        const note = eventType === "rejected" && !draft.trim() ? UI_COPY.rejectDefaultNote : draft;
        await postHitlEvent(issue, eventType, note, reportId);
        if (!stillOnFinding(reportId, issue)) {
          return;
        }
        setHitlDecisionState(eventType);
        setConflictMessage(null);
      } catch (error: unknown) {
        if (!stillOnFinding(reportId, issue)) {
          return;
        }
        setHitlDecisionState("failed");
        if (error instanceof ApiHttpError && error.status === 409) {
          setConflictMessage(UI_COPY.hitlConflict);
        }
      } finally {
        hitlBusyRef.current = false;
      }
    },
    [postHitlEvent, reportLoading],
  );

  const confirmPendingSelect = useCallback(
    async (mode: "save" | "discard") => {
      const pending = pendingSelect;
      if (!pending) {
        return;
      }
      if (mode === "save") {
        const current = selectedReportRef.current?.issues[selectedIssueIndexRef.current] ?? null;
        const saved = await saveRemarkEdit(current);
        if (!saved) {
          return;
        }
      }
      applySelect(pending.index, pending.issue);
    },
    [applySelect, pendingSelect, saveRemarkEdit],
  );

  const dismissPendingSelect = useCallback(() => {
    setPendingSelect(null);
  }, []);

  useEffect(() => {
    const selectedIssue = selectedReport?.issues[selectedIssueIndex];
    const original = selectedIssue ? effectiveRemarkText(selectedIssue, reviewEvents) : "";
    const dirty = remarkDraft !== original;
    if (!dirty) {
      return;
    }
    function onBeforeUnload(event: BeforeUnloadEvent): void {
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [remarkDraft, reviewEvents, selectedIssueIndex, selectedReport]);

  const selectedIssue = selectedReport?.issues[selectedIssueIndex];
  const originalRemark = selectedIssue ? effectiveRemarkText(selectedIssue, reviewEvents) : "";
  const isDirty = remarkDraft !== originalRemark;

  return {
    selectedReport,
    reportLoading,
    reportError,
    reviewEvents,
    reviewEventsError,
    historyPending,
    selectedIssueIndex,
    selectedClashIndex,
    remarkDraft,
    remarkSaveState,
    hitlDecisionState,
    pendingSelect,
    conflictMessage,
    setSelectedIssueIndex,
    setSelectedClashIndex,
    setRemarkDraft,
    setRemarkSaveState,
    setHitlDecisionState,
    selectIssue,
    confirmPendingSelect,
    dismissPendingSelect,
    saveRemarkEdit,
    decideRemark,
    isDirty,
  };
}
