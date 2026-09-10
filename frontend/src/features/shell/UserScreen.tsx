import BlockerHonestyPanel from "../honesty/BlockerHonestyPanel";
import CoverageMapPanel from "../../components/CoverageMapPanel";
import ReviewKpiPanel from "../../components/ReviewKpiPanel";
import TzWorkplaceCoveragePanel from "../../components/TzWorkplaceCoveragePanel";
import type { WorkspaceView } from "../../components/WorkspaceNav";
import type { ValidationReport } from "../../lib/types";
import { UI_COPY } from "../../lib/ui-copy";

type UserScreenProps = {
  selectedReportId: string | null;
  selectedReport: ValidationReport | null;
  onOpenScreen: (view: WorkspaceView) => void;
  onNavigateToFindings: () => void;
};

/** Экран «Эффект»: сначала «что не проверялось», затем блокеры, карта ТЗ, KPI. Только чтение. */
export default function UserScreen({
  selectedReportId,
  selectedReport,
  onOpenScreen,
  onNavigateToFindings,
}: UserScreenProps) {
  return (
    <div className="workspace-alt">
      {selectedReport ? (
        <CoverageMapPanel
          reportId={selectedReport.report_id}
          onNavigateToFindings={onNavigateToFindings}
        />
      ) : (
        <p className="panel-empty">{UI_COPY.selectReport}</p>
      )}
      <BlockerHonestyPanel />
      <TzWorkplaceCoveragePanel onOpenScreen={onOpenScreen} />
      <ReviewKpiPanel reportId={selectedReportId} />
    </div>
  );
}
