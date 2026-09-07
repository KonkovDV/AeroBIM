import AnalyzeRunPanel from "../../components/AnalyzeRunPanel";
import PackUploadPanel from "../../components/PackUploadPanel";
import type { WorkspaceView } from "../../components/WorkspaceNav";
import type { ReportCapabilities } from "../../lib/types";
import type { usePackDraft } from "../../hooks/usePackDraft";
import type { RunPolling } from "../../hooks/useRunPolling";

type PackScreensProps = {
  workspaceView: "upload" | "run";
  pack: ReturnType<typeof usePackDraft>;
  capabilities: ReportCapabilities | null;
  capabilitiesReportId: string | null;
  onReportReady: (reportId: string) => void;
  onNavigate: (view: WorkspaceView) => void;
  runPolling?: RunPolling;
};

/** Экраны «Загрузка» и «Прогон»: приём файлов комплекта и запуск анализа. */
export default function PackScreens({
  workspaceView,
  pack,
  capabilities,
  capabilitiesReportId,
  onReportReady,
  onNavigate,
  runPolling,
}: PackScreensProps) {
  const { packDraft, draftApplyNote, pendingRole, applyUpload, chooseRole } = pack;

  if (workspaceView === "upload") {
    return (
      <div className="workspace-alt">
        <PackUploadPanel
          draftApplyNote={draftApplyNote}
          packDraft={packDraft}
          pendingRole={pendingRole}
          onChooseRole={chooseRole}
          onUploadedPath={(path, filename) => {
            applyUpload(path, filename);
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
        capabilitiesReportId={capabilitiesReportId}
        polling={runPolling}
      />
    </div>
  );
}
