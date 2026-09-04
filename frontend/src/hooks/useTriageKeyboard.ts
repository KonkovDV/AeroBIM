import { useEffect, type Dispatch, type SetStateAction } from "react";
import type { IndexedIssue } from "../lib/issue-triage";

export function useTriageKeyboard({
  enabled,
  filteredIssues,
  selectedIssueIndex,
  hitlEnabled,
  setTriageHelpOpen,
  setSelectedIssueIndex,
  setSelectedClashIndex,
  setRemarkDraft,
  decideRemark,
}: {
  enabled: boolean;
  filteredIssues: IndexedIssue[];
  selectedIssueIndex: number;
  hitlEnabled: boolean;
  setTriageHelpOpen: Dispatch<SetStateAction<boolean>>;
  setSelectedIssueIndex: Dispatch<SetStateAction<number>>;
  setSelectedClashIndex: Dispatch<SetStateAction<number | null>>;
  setRemarkDraft: Dispatch<SetStateAction<string>>;
  decideRemark: (eventType: "accepted" | "rejected") => Promise<void>;
}): void {
  useEffect(() => {
    if (!enabled) {
      return;
    }

    function onKeyDown(event: KeyboardEvent): void {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target?.isContentEditable) {
        if (event.key === "Escape") {
          setTriageHelpOpen(false);
        }
        return;
      }
      if (event.key === "?" || (event.shiftKey && event.key === "/")) {
        event.preventDefault();
        setTriageHelpOpen((open) => !open);
        return;
      }
      if (event.key === "Escape") {
        setTriageHelpOpen(false);
        return;
      }
      if (filteredIssues.length === 0) {
        return;
      }
      const currentPos = filteredIssues.findIndex(({ index }) => index === selectedIssueIndex);
      const pos = currentPos >= 0 ? currentPos : 0;
      if (event.key === "j" || event.key === "J" || event.key === "ArrowDown") {
        event.preventDefault();
        const next = filteredIssues[Math.min(pos + 1, filteredIssues.length - 1)];
        if (next) {
          setSelectedIssueIndex(next.index);
          setSelectedClashIndex(null);
          setRemarkDraft(next.issue.remark?.body ?? "");
        }
        return;
      }
      if (event.key === "k" || event.key === "K" || event.key === "ArrowUp") {
        event.preventDefault();
        const prev = filteredIssues[Math.max(pos - 1, 0)];
        if (prev) {
          setSelectedIssueIndex(prev.index);
          setSelectedClashIndex(null);
          setRemarkDraft(prev.issue.remark?.body ?? "");
        }
        return;
      }
      if (event.key === "a" || event.key === "A") {
        if (!hitlEnabled) {
          return;
        }
        event.preventDefault();
        void decideRemark("accepted");
        return;
      }
      if (event.key === "r" || event.key === "R") {
        if (!hitlEnabled) {
          return;
        }
        event.preventDefault();
        void decideRemark("rejected");
        return;
      }
      if (event.key === "e" || event.key === "E") {
        if (!hitlEnabled) {
          return;
        }
        event.preventDefault();
        document.getElementById("remark-editor")?.focus();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    enabled,
    filteredIssues,
    selectedIssueIndex,
    hitlEnabled,
    setTriageHelpOpen,
    setSelectedIssueIndex,
    setSelectedClashIndex,
    setRemarkDraft,
    decideRemark,
  ]);
}
