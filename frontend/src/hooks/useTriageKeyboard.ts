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
export const TRIAGE_PAGE_SIZE = 10;

/**
 * Auto-next (K2A-P1-02): после решения эксперта — следующая позиция в
 * текущем (отфильтрованном, упорядоченном по приоритету) списке. В конце
 * очереди — null: фокус не прыгает назад на уже решённую находку.
 */
export function nextPosAfterDecision(length: number, pos: number): number | null {
  const next = pos + 1;
  return next < length ? next : null;
}

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
  /** Resolves true only when the decision was recorded (auto-next gate). */
  decideRemark: (eventType: "accepted" | "rejected") => Promise<boolean>;
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
      if (hotkey === "next" || hotkey === "prev" || hotkey === "first" || hotkey === "last" || hotkey === "pageNext" || hotkey === "pagePrev") {
        event.preventDefault();
        const last = filteredIssues.length - 1;
        const nextPos =
          hotkey === "first"
            ? 0
            : hotkey === "last"
              ? last
              : hotkey === "pageNext"
                ? Math.min(pos + TRIAGE_PAGE_SIZE, last)
                : hotkey === "pagePrev"
                  ? Math.max(pos - TRIAGE_PAGE_SIZE, 0)
                  : hotkey === "next"
                    ? Math.min(pos + 1, last)
                    : Math.max(pos - 1, 0);
        const target = filteredIssues[nextPos];
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
        void decideRemark("accepted").then((recorded) => {
          if (!recorded) return;
          const nextPos = nextPosAfterDecision(filteredIssues.length, pos);
          const target = nextPos === null ? undefined : filteredIssues[nextPos];
          if (target) selectIssue(target.index, target.issue);
        }, () => undefined);
        return;
      }
      if (hotkey === "reject") {
        event.preventDefault();
        void decideRemark("rejected").then((recorded) => {
          if (!recorded) return;
          const nextPos = nextPosAfterDecision(filteredIssues.length, pos);
          const target = nextPos === null ? undefined : filteredIssues[nextPos];
          if (target) selectIssue(target.index, target.issue);
        }, () => undefined);
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
