import { useEffect, type Dispatch, type SetStateAction } from "react";
import type { ValidationIssue } from "../lib/types";
import type { IndexedIssue } from "../lib/issue-triage";
import { isTextEntryTarget, resolveTriageHotkey } from "../lib/triage-hotkeys";

/**
 * Хоткеи триажа J/K/A/R/E/? — первоклассный ввод эксперта (план §3, п.10).
 *
 * Разбор клавиш вынесен в lib/triage-hotkeys.ts, чтобы закрыть две дыры:
 * раскладку (на русской раскладке key === "к", а не "r") и модификаторы
 * (Ctrl+R «перезагрузить» попадал в обработчик и записывался как отклонение
 * замечания в журнал HITL).
 */
export function useTriageKeyboard({
  enabled,
  filteredIssues,
  selectedIssueIndex,
  hitlEnabled,
  setTriageHelpOpen,
  selectIssue,
  decideRemark,
}: {
  enabled: boolean;
  filteredIssues: IndexedIssue[];
  selectedIssueIndex: number;
  hitlEnabled: boolean;
  setTriageHelpOpen: Dispatch<SetStateAction<boolean>>;
  selectIssue: (index: number, issue: ValidationIssue) => void;
  decideRemark: (eventType: "accepted" | "rejected") => Promise<void>;
}): void {
  useEffect(() => {
    if (!enabled) {
      return;
    }

    function onKeyDown(event: KeyboardEvent): void {
      const hotkey = resolveTriageHotkey(event);
      if (hotkey === null) {
        return;
      }
      if (isTextEntryTarget(event.target)) {
        if (hotkey === "close") {
          setTriageHelpOpen(false);
        }
        return;
      }
      if (hotkey === "help") {
        event.preventDefault();
        setTriageHelpOpen((open) => !open);
        return;
      }
      if (hotkey === "close") {
        setTriageHelpOpen(false);
        return;
      }
      if (filteredIssues.length === 0) {
        return;
      }
      const currentPos = filteredIssues.findIndex(({ index }) => index === selectedIssueIndex);
      const pos = currentPos >= 0 ? currentPos : 0;
      if (hotkey === "next" || hotkey === "prev") {
        event.preventDefault();
        const target =
          hotkey === "next"
            ? filteredIssues[Math.min(pos + 1, filteredIssues.length - 1)]
            : filteredIssues[Math.max(pos - 1, 0)];
        if (target) {
          selectIssue(target.index, target.issue);
        }
        return;
      }
      if (!hitlEnabled) {
        return;
      }
      if (hotkey === "accept") {
        event.preventDefault();
        void decideRemark("accepted");
        return;
      }
      if (hotkey === "reject") {
        event.preventDefault();
        void decideRemark("rejected");
        return;
      }
      if (hotkey === "edit") {
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
    selectIssue,
    decideRemark,
  ]);
}
