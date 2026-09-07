import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { fetchReport, fetchReviewEvents, postReviewEvent, type ReviewEventRow, type ReviewEventType } from "../lib/api";
import { asReviewEventRow, effectiveRemarkText, hitlOperationFingerprint, latestHitlState, latestReviewSequence } from "../lib/hitl-state";
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
  const hitlOpRef = useRef<{ fingerprint: string; key: string } | null>(null);

  // Синхронизация ref со state — побочный эффект, а не работа тела рендера.
  useEffect(() => {
    reviewEventsRef.current = reviewEvents;
  }, [reviewEvents]);

  useEffect(() => {
    if (selectedReportId === null) {
      setSelectedReport(null);
      setReviewEvents([]);
      setReviewEventsError(null);
      // Без сброса ошибки баннер прошлого отчёта висел над пустым экраном,
      // а непустой черновик держал beforeunload-предупреждение при уходе.
      setReportError(null);
      setRemarkDraft("");
      setRemarkSaveState("idle");
      setHitlDecisionState("idle");
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
        const firstIssue = report.issues[0];
        setRemarkDraft(firstIssue ? effectiveRemarkText(firstIssue, []) : "");
        setRemarkSaveState("idle");
        setHitlDecisionState("idle");
        const eventsResult = await eventsPromise;
        if (cancelled || controller.signal.aborted) {
          return;
        }
        if (eventsResult.ok) {
          setReviewEvents(eventsResult.payload.events);
          setReviewEventsError(null);
          if (firstIssue) {
            setRemarkDraft(effectiveRemarkText(firstIssue, eventsResult.payload.events));
          }
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
    setRemarkDraft(effectiveRemarkText(issue, reviewEventsRef.current));
    setRemarkSaveState("idle");
    setHitlDecisionState("idle");
  }, []);

  const rememberEvent = useCallback((event: Record<string, unknown>) => {
    const row = asReviewEventRow(event);
    if (row === null) {
      return;
    }
    // Ref обновляем здесь, а не внутри updater: updater обязан быть чистым,
    // React вправе вызвать его дважды (StrictMode) или отбросить результат.
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
    async (issue: ValidationIssue, eventType: ReviewEventType, note: string) => {
      if (!selectedReport) {
        return;
      }
      let previous = latestHitlState(reviewEventsRef.current, issue);
      if (previous === null && eventType !== "opened") {
        const openedVersion = latestReviewSequence(reviewEventsRef.current, issue) ?? 0;
        const openedFingerprint = hitlOperationFingerprint({
          reportId: selectedReport.report_id,
          findingId: issue.finding_id ?? "",
          eventType: "opened",
          note: "",
          previousState: "",
          expectedReviewVersion: openedVersion,
        });
        const opened = await postReviewEvent(selectedReport.report_id, {
          event_type: "opened",
          issue_rule_id: issue.rule_id,
          finding_id: issue.finding_id ?? undefined,
          idempotency_key: keyForFingerprint(openedFingerprint),
          expected_review_version: openedVersion,
        });
        hitlOpRef.current = null;
        rememberEvent(opened.event);
        previous = "opened";
      }
      const expectedReviewVersion = latestReviewSequence(reviewEventsRef.current, issue) ?? 0;
      const fingerprint = hitlOperationFingerprint({
        reportId: selectedReport.report_id,
        findingId: issue.finding_id ?? "",
        eventType,
        note,
        previousState: previous ?? "",
        expectedReviewVersion,
      });
      const result = await postReviewEvent(selectedReport.report_id, {
        event_type: eventType,
        issue_rule_id: issue.rule_id,
        finding_id: issue.finding_id ?? undefined,
        note,
        previous_state: previous ?? undefined,
        idempotency_key: keyForFingerprint(fingerprint),
        expected_review_version: expectedReviewVersion,
      });
      rememberEvent(result.event);
      hitlOpRef.current = null;
    },
    [rememberEvent, selectedReport],
  );

  const saveRemarkEdit = useCallback(
    async (issue: ValidationIssue | null) => {
      if (!selectedReport || !issue) {
        return;
      }
      if (!remarkDraft.trim()) {
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

  useEffect(() => {
    const selectedIssue = selectedReport?.issues[selectedIssueIndex];
    const original = selectedIssue ? effectiveRemarkText(selectedIssue, reviewEvents) : "";
    const dirty = remarkDraft !== original && remarkSaveState !== "saved";
    if (!dirty) {
      return;
    }
    function onBeforeUnload(event: BeforeUnloadEvent): void {
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [remarkDraft, remarkSaveState, reviewEvents, selectedIssueIndex, selectedReport]);

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
