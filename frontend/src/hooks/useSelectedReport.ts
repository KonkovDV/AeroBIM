import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { fetchReport, postReviewEvent } from "../lib/api";
import type { ValidationIssue, ValidationReport } from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";

export type RemarkSaveState = "idle" | "saving" | "saved" | "failed";
export type HitlDecisionState = "idle" | "saving" | "accepted" | "rejected" | "failed";

export type SelectedReportState = {
  selectedReport: ValidationReport | null;
  reportLoading: boolean;
  reportError: string | null;
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
export function useSelectedReport(selectedReportId: string | null): SelectedReportState {
  const [selectedReport, setSelectedReport] = useState<ValidationReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [selectedIssueIndex, setSelectedIssueIndex] = useState(0);
  const [selectedClashIndex, setSelectedClashIndex] = useState<number | null>(null);
  const [remarkDraft, setRemarkDraft] = useState("");
  const [remarkSaveState, setRemarkSaveState] = useState<RemarkSaveState>("idle");
  const [hitlDecisionState, setHitlDecisionState] = useState<HitlDecisionState>("idle");

  useEffect(() => {
    if (selectedReportId === null) {
      setSelectedReport(null);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;
    setReportLoading(true);
    fetchReport(selectedReportId, { signal: controller.signal })
      .then((report) => {
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
      })
      .catch((error: unknown) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setReportError(error instanceof Error ? error.message : UI_COPY.loadReportFailed);
        setSelectedReport(null);
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
  }, [selectedReportId]);

  const selectIssue = useCallback((index: number, issue: ValidationIssue) => {
    setSelectedIssueIndex(index);
    setSelectedClashIndex(null);
    setRemarkDraft(issue.remark?.body ?? "");
    setRemarkSaveState("idle");
    setHitlDecisionState("idle");
  }, []);

  const saveRemarkEdit = useCallback(
    async (issue: ValidationIssue | null) => {
      if (!selectedReport || !issue) {
        return;
      }
      setRemarkSaveState("saving");
      try {
        await postReviewEvent(selectedReport.report_id, {
          event_type: "edited_remark",
          issue_rule_id: issue.rule_id,
          finding_id: issue.finding_id ?? undefined,
          note: remarkDraft,
        });
        setRemarkSaveState("saved");
      } catch {
        setRemarkSaveState("failed");
      }
    },
    [selectedReport, remarkDraft],
  );

  const decideRemark = useCallback(
    async (eventType: "accepted" | "rejected", issue: ValidationIssue | null) => {
      if (!selectedReport || !issue) {
        return;
      }
      setHitlDecisionState("saving");
      try {
        await postReviewEvent(selectedReport.report_id, {
          event_type: eventType,
          issue_rule_id: issue.rule_id,
          finding_id: issue.finding_id ?? undefined,
          note: remarkDraft,
        });
        setHitlDecisionState(eventType);
      } catch {
        setHitlDecisionState("failed");
      }
    },
    [selectedReport, remarkDraft],
  );

  return {
    selectedReport,
    reportLoading,
    reportError,
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
