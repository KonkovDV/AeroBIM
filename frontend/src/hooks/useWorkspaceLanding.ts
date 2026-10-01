import { useCallback, useEffect, useRef, useState } from "react";
import type { WorkspaceView } from "../components/WorkspaceNav";
import { scrollExpertWorkplaceIntoView, scrollFindingListIntoView } from "../lib/rehearsal-land";

export type WorkspaceLanding = {
  /** После следующего перехода на «Ревью» приземлиться на рабочее место эксперта. */
  landOnExpert: () => void;
  /** Перейти на «Ревью» и прокрутить к списку находок. */
  landOnFindings: () => void;
};

/**
 * Приземление на нужную панель после смены экрана.
 *
 * Прежний navigateToFindings() искал узел сразу за setWorkspaceView("review") — в тот
 * момент React ещё не смонтировал панель, querySelector возвращал null, и прокрутка
 * молча не случалась. Здесь цель ищется в эффекте, то есть уже после коммита.
 */
export function useWorkspaceLanding({
  workspaceView,
  hasReport,
  setWorkspaceView,
}: {
  workspaceView: WorkspaceView;
  hasReport: boolean;
  setWorkspaceView: (view: WorkspaceView) => void;
}): WorkspaceLanding {
  const pendingExpert = useRef(false);
  const pendingFindings = useRef(false);
  /** Счётчик нужен, чтобы эффект сработал и тогда, когда экран уже «Ревью». */
  const [landEpoch, setLandEpoch] = useState(0);

  useEffect(() => {
    if (workspaceView === "remark") {
      document.getElementById("remark-editor")?.focus?.();
    }
    if (workspaceView === "export") {
      document.getElementById("export-actions")?.scrollIntoView?.({ block: "nearest" });
    }
    if (workspaceView !== "review") {
      return;
    }
    if (pendingExpert.current && hasReport) {
      pendingExpert.current = false;
      scrollExpertWorkplaceIntoView();
    }
    if (pendingFindings.current) {
      pendingFindings.current = false;
      scrollFindingListIntoView();
    }
  }, [workspaceView, hasReport, landEpoch]);

  const landOnExpert = useCallback(() => {
    pendingExpert.current = true;
  }, []);

  const landOnFindings = useCallback(() => {
    pendingFindings.current = true;
    setWorkspaceView("review");
    setLandEpoch((value) => value + 1);
  }, [setWorkspaceView]);

  return { landOnExpert, landOnFindings };
}
