import AnalyzeRunPanel from "../../components/AnalyzeRunPanel";
import PackUploadPanel from "../../components/PackUploadPanel";
import type { WorkspaceView } from "../../components/WorkspaceNav";
import type { ReportCapabilities } from "../../lib/types";
import type { usePackDraft } from "../../hooks/usePackDraft";

type PackScreensProps = {
  workspaceView: "upload" | "run";
  pack: ReturnType<typeof usePackDraft>;
  capabilities: ReportCapabilities | null;
  onReportReady: (reportId: string) => void;
  onNavigate: (view: WorkspaceView) => void;
};

/** Экраны «Загрузка» и «Прогон»: приём файлов комплекта и запуск анализа. */
export default function PackScreens({
  workspaceView,
  pack,
  capabilities,
  onReportReady,
  onNavigate,
}: PackScreensProps) {
  const { packDraft, draftApplyNote, applyUpload } = pack;

  if (workspaceView === "upload") {
    return (
      <div className="workspace-alt">
        <PackUploadPanel
          draftApplyNote={draftApplyNote}
          onUploadedPath={(path, filename) => {
            const note = applyUpload(path, filename);
            if (note.kind === "filled" && note.slot === "ifc") {
              onNavigate("run");
            }
          }}
          onContinueToRun={() => onNavigate("run")}
        />
      </div>
    );
  }

  return (
    <div className="workspace-alt">
      <AnalyzeRunPanel
        ifcPath={packDraft.ifcPath}
        packDraft={packDraft}
        onReportReady={onReportReady}
        onNeedUpload={() => onNavigate("upload")}
        onContinueToExpert={() => onNavigate("review")}
        capabilities={capabilities}
      />
    </div>
  );
}
