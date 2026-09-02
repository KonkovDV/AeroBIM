import { useEffect, useEffectEvent, useRef, useState } from "react";
import type { ValidationReport } from "../lib/types";
import { fetchReportIfcSource } from "../lib/api";
import { IfcSceneController } from "../lib/ifc-scene";
import { UI_COPY } from "../lib/ui-copy";

type ViewerStatus = "idle" | "initializing" | "loading" | "ready" | "error";

interface IfcViewerPanelProps {
  report: ValidationReport | null;
  selectedGuids: string[];
  selectionMode: "none" | "issue" | "clash";
  selectionHeading: string;
  selectionDetail: string;
}

export default function IfcViewerPanel({
  report,
  selectedGuids,
  selectionMode,
  selectionHeading,
  selectionDetail,
}: IfcViewerPanelProps) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const controllerRef = useRef<IfcSceneController | null>(null);
  const [viewerStatus, setViewerStatus] = useState<ViewerStatus>("idle");
  const [viewerError, setViewerError] = useState<string | null>(null);
  const [controllerReady, setControllerReady] = useState(false);
  const [isolateSelection, setIsolateSelection] = useState(false);

  const applySelection = useEffectEvent(() => {
    const controller = controllerRef.current;
    if (controller === null || !controllerReady) {
      return;
    }
    controller.setSelectedGuids(selectedGuids);
    controller.setIsolateSelection(isolateSelection);
  });

  useEffect(() => {
    const viewport = viewportRef.current;
    if (viewport === null) {
      return;
    }

    const controller = new IfcSceneController(viewport);
    controllerRef.current = controller;
    let cancelled = false;

    setViewerStatus((current) => (current === "idle" ? "initializing" : current));
    controller
      .init()
      .then(() => {
        if (cancelled) {
          return;
        }
        setControllerReady(true);
        setViewerStatus((current) => (current === "initializing" ? "idle" : current));
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        setViewerStatus("error");
        setViewerError(error instanceof Error ? error.message : "Failed to initialize IFC viewer.");
      });

    return () => {
      cancelled = true;
      controller.dispose();
      controllerRef.current = null;
      setControllerReady(false);
    };
  }, []);

  const reportId = report?.report_id ?? null;

  useEffect(() => {
    const controller = controllerRef.current;
    if (!controllerReady || controller === null) {
      return;
    }
    if (reportId === null) {
      controller.clearModel();
      setViewerStatus("idle");
      setViewerError(null);
      return;
    }

    let cancelled = false;
    setViewerStatus("loading");
    setViewerError(null);
    setIsolateSelection(false);

    fetchReportIfcSource(reportId)
      .then((ifcBytes) => controller.loadModel(ifcBytes))
      .then(() => {
        if (cancelled) {
          return;
        }
        setViewerStatus("ready");
        applySelection();
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        setViewerStatus("error");
        setViewerError(error instanceof Error ? error.message : "Failed to load IFC source for the report.");
      });

    return () => {
      cancelled = true;
    };
  }, [controllerReady, reportId]);

  useEffect(() => {
    applySelection();
  }, [isolateSelection, selectedGuids]);

  const canInteractWithSelection = viewerStatus === "ready" && selectedGuids.length > 0;

  return (
    <section className="panel viewer-panel">
      <div className="panel-header viewer-header">
        <div>
          <p className="panel-kicker">{UI_COPY.viewerKicker}</p>
          <h2>{UI_COPY.viewerTitle}</h2>
        </div>
        <div className="viewer-toolbar">
          <button
            type="button"
            className="viewer-button"
            disabled={viewerStatus !== "ready"}
            onClick={() => controllerRef.current?.resetView()}
          >
            {UI_COPY.resetView}
          </button>
          <button
            type="button"
            className="viewer-button"
            disabled={!canInteractWithSelection}
            onClick={() => setIsolateSelection((current) => !current)}
          >
            {isolateSelection ? UI_COPY.showAll : UI_COPY.isolateSelected}
          </button>
        </div>
      </div>

      <div className="viewer-meta">
        <span className={`viewer-status viewer-status-${viewerStatus}`}>{viewerStatus}</span>
        <span>{report ? `Report ${report.report_id.slice(0, 8)}` : UI_COPY.noReportShort}</span>
        <span>
          {selectionMode === "clash"
            ? UI_COPY.clashPairMode
            : selectionMode === "issue"
              ? UI_COPY.issueFocusMode
              : UI_COPY.noSelectionMode}
        </span>
      </div>

      <div className="viewer-selection-card">
        <strong>{selectionHeading}</strong>
        <p>{selectionDetail}</p>
        {selectedGuids.length > 0 && (
          <div className="viewer-selection-list">
            {selectedGuids.map((guid, index) => (
              <span key={guid} className="selection-badge selection-badge-active">
                {selectionMode === "clash" ? UI_COPY.elementN(index + 1) : UI_COPY.element} · {guid}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="viewer-stage">
        <div ref={viewportRef} className="viewer-viewport" />
        {viewerStatus === "idle" && (
          <div className="viewer-overlay">
            <p>{UI_COPY.viewerNeedReport}</p>
          </div>
        )}
        {viewerStatus === "initializing" && (
          <div className="viewer-overlay">
            <p>{UI_COPY.viewerInit}</p>
          </div>
        )}
        {viewerStatus === "loading" && (
          <div className="viewer-overlay">
            <p>{UI_COPY.viewerLoad}</p>
          </div>
        )}
        {viewerStatus === "error" && (
          <div className="viewer-overlay viewer-overlay-error">
            <p>{viewerError ?? UI_COPY.viewerError}</p>
          </div>
        )}
      </div>

      <p className="viewer-caption">
        {UI_COPY.viewerFooter}
      </p>
    </section>
  );
}