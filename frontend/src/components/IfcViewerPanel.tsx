import { useEffect, useEffectEvent, useRef, useState } from "react";
import type { ValidationReport } from "../lib/types";
import { fetchReportIfcSource } from "../lib/api";
import { IfcSceneController } from "../lib/ifc-scene";

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

  useEffect(() => {
    const controller = controllerRef.current;
    if (!controllerReady || controller === null) {
      return;
    }
    if (report === null) {
      controller.clearModel();
      setViewerStatus("idle");
      setViewerError(null);
      return;
    }

    let cancelled = false;
    setViewerStatus("loading");
    setViewerError(null);
    setIsolateSelection(false);

    fetchReportIfcSource(report.report_id)
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
  }, [applySelection, controllerReady, report]);

  useEffect(() => {
    applySelection();
  }, [applySelection, isolateSelection, selectedGuids]);

  const canInteractWithSelection = viewerStatus === "ready" && selectedGuids.length > 0;

  return (
    <section className="panel viewer-panel">
      <div className="panel-header viewer-header">
        <div>
          <p className="panel-kicker">Spatial Review</p>
          <h2>IFC viewer</h2>
        </div>
        <div className="viewer-toolbar">
          <button
            type="button"
            className="viewer-button"
            disabled={viewerStatus !== "ready"}
            onClick={() => controllerRef.current?.resetView()}
          >
            Reset view
          </button>
          <button
            type="button"
            className="viewer-button"
            disabled={!canInteractWithSelection}
            onClick={() => setIsolateSelection((current) => !current)}
          >
            {isolateSelection ? "Show all" : "Isolate selected"}
          </button>
        </div>
      </div>

      <div className="viewer-meta">
        <span className={`viewer-status viewer-status-${viewerStatus}`}>{viewerStatus}</span>
        <span>{report ? `Report ${report.report_id.slice(0, 8)}` : "No report selected"}</span>
        <span>{selectionMode === "clash" ? "clash pair" : selectionMode === "issue" ? "issue focus" : "no selection"}</span>
      </div>

      <div className="viewer-selection-card">
        <strong>{selectionHeading}</strong>
        <p>{selectionDetail}</p>
        {selectedGuids.length > 0 && (
          <div className="viewer-selection-list">
            {selectedGuids.map((guid, index) => (
              <span key={guid} className="selection-badge selection-badge-active">
                {selectionMode === "clash" ? `element ${index + 1}` : "element"} · {guid}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="viewer-stage">
        <div ref={viewportRef} className="viewer-viewport" />
        {viewerStatus === "idle" && (
          <div className="viewer-overlay">
            <p>Select a persisted report to load its IFC source into the browser viewer.</p>
          </div>
        )}
        {viewerStatus === "initializing" && (
          <div className="viewer-overlay">
            <p>Initializing `web-ifc` and the scene runtime…</p>
          </div>
        )}
        {viewerStatus === "loading" && (
          <div className="viewer-overlay">
            <p>Loading IFC bytes and streaming geometry for the selected report…</p>
          </div>
        )}
        {viewerStatus === "error" && (
          <div className="viewer-overlay viewer-overlay-error">
            <p>{viewerError ?? "The viewer failed to load the selected IFC source."}</p>
          </div>
        )}
      </div>

      <p className="viewer-caption">
        The viewer remains downstream of the persisted validation report. Selection is driven by persisted IFC GUID evidence from either a single issue or a clash pair, not by ad hoc browser-side model inspection.
      </p>
    </section>
  );
}