import { useEffect, useMemo, useState } from "react";
import { buildDrawingAssetPreviewUrl } from "../lib/api";
import type { DrawingAsset, ValidationIssue, ValidationReport } from "../lib/types";

interface DrawingEvidencePanelProps {
  report: ValidationReport | null;
  activeIssue: ValidationIssue | null;
}

function findMatchingAsset(report: ValidationReport, issue: ValidationIssue | null): DrawingAsset | null {
  const problemZone = issue?.problem_zone;
  if (problemZone?.sheet_id === null || problemZone?.sheet_id === undefined) {
    return null;
  }

  const exactMatch = report.drawing_assets.find(
    (asset) =>
      asset.sheet_id === problemZone.sheet_id &&
      (problemZone.page_number === null || asset.page_number === problemZone.page_number),
  );
  if (exactMatch) {
    return exactMatch;
  }

  return report.drawing_assets.find((asset) => asset.sheet_id === problemZone.sheet_id) ?? null;
}

function describeAsset(asset: DrawingAsset): string {
  return `${asset.sheet_id}${asset.page_number ? ` · page ${asset.page_number}` : ""}`;
}

export default function DrawingEvidencePanel({ report, activeIssue }: DrawingEvidencePanelProps) {
  const [imageMetrics, setImageMetrics] = useState<{ width: number; height: number } | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);

  const problemZone = activeIssue?.problem_zone ?? null;
  const matchedAsset = report ? findMatchingAsset(report, activeIssue) : null;
  const drawingAssets = report?.drawing_assets ?? [];

  useEffect(() => {
    if (report === null || drawingAssets.length === 0) {
      setSelectedAssetId(null);
      return;
    }

    const nextAssetId = matchedAsset?.asset_id ?? drawingAssets[0]?.asset_id ?? null;
    setSelectedAssetId(nextAssetId);
  }, [report, matchedAsset, drawingAssets]);

  const selectedAsset = useMemo(() => {
    if (drawingAssets.length === 0) {
      return null;
    }
    return drawingAssets.find((asset) => asset.asset_id === selectedAssetId) ?? drawingAssets[0] ?? null;
  }, [drawingAssets, selectedAssetId]);

  const previewUrl = report && selectedAsset ? buildDrawingAssetPreviewUrl(report.report_id, selectedAsset.asset_id) : null;
  const isOverlayTarget = selectedAsset !== null && matchedAsset !== null && selectedAsset.asset_id === matchedAsset.asset_id;

  useEffect(() => {
    setImageMetrics(null);
    setImageError(null);
  }, [previewUrl]);

  const coordinateWidth = selectedAsset?.coordinate_width ?? imageMetrics?.width ?? null;
  const coordinateHeight = selectedAsset?.coordinate_height ?? imageMetrics?.height ?? null;
  const canDrawOverlay =
    isOverlayTarget &&
    imageMetrics !== null &&
    coordinateWidth !== null &&
    coordinateHeight !== null &&
    problemZone?.x !== null &&
    problemZone?.y !== null &&
    problemZone?.width !== null &&
    problemZone?.height !== null;

  const normalizedZone = canDrawOverlay && problemZone !== null
    ? {
        x: problemZone.x ?? 0,
        y: problemZone.y ?? 0,
        width: problemZone.width ?? 0,
        height: problemZone.height ?? 0,
      }
    : null;

  const overlayStyle = normalizedZone !== null && imageMetrics !== null && coordinateWidth !== null && coordinateHeight !== null
    ? {
        left: `${(normalizedZone.x / coordinateWidth) * imageMetrics.width}px`,
        top: `${(normalizedZone.y / coordinateHeight) * imageMetrics.height}px`,
        width: `${(normalizedZone.width / coordinateWidth) * imageMetrics.width}px`,
        height: `${(normalizedZone.height / coordinateHeight) * imageMetrics.height}px`,
      }
    : undefined;

  return (
    <section className="panel drawing-evidence-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">2D Evidence</p>
          <h2>Problem zone overlay</h2>
        </div>
      </div>

      {report === null ? (
        <div className="panel-empty compact">Select a report to inspect drawing evidence.</div>
      ) : drawingAssets.length === 0 ? (
        <div className="panel-empty compact">No persisted drawing preview assets were materialized for this report.</div>
      ) : (
        <>
          <div className="drawing-evidence-meta">
            <span>{selectedAsset ? describeAsset(selectedAsset) : "asset n/a"}</span>
            <span>{selectedAsset?.media_type ?? "preview n/a"}</span>
            <span>{isOverlayTarget ? "overlay target" : "browse mode"}</span>
          </div>

          {drawingAssets.length > 1 && (
            <div className="drawing-evidence-selector" role="tablist" aria-label="Persisted drawing assets">
              {drawingAssets.map((asset) => {
                const isActive = selectedAsset?.asset_id === asset.asset_id;
                const isMatch = matchedAsset?.asset_id === asset.asset_id;
                return (
                  <button
                    key={asset.asset_id}
                    type="button"
                    className={`drawing-evidence-chip ${isActive ? "active" : ""}`}
                    onClick={() => {
                      setSelectedAssetId(asset.asset_id);
                    }}
                  >
                    <span>{describeAsset(asset)}</span>
                    {isMatch && <span className="selection-badge">issue match</span>}
                  </button>
                );
              })}
            </div>
          )}

          <div className="drawing-evidence-stage">
            <img
              src={previewUrl ?? undefined}
              alt={`Drawing evidence preview for ${selectedAsset?.sheet_id ?? "drawing asset"}`}
              className="drawing-evidence-image"
              onLoad={(event) => {
                setImageMetrics({
                  width: event.currentTarget.naturalWidth,
                  height: event.currentTarget.naturalHeight,
                });
              }}
              onError={() => {
                setImageError("Failed to load the persisted drawing preview for this issue.");
              }}
            />
            {overlayStyle && <div className="drawing-evidence-rect" style={overlayStyle} />}
            {imageError && (
              <div className="viewer-overlay viewer-overlay-error">
                <p>{imageError}</p>
              </div>
            )}
          </div>

          <div className="drawing-evidence-caption">
            <strong>{activeIssue?.rule_id ?? "Report drawing evidence"}</strong>
            <p>
              Overlay coordinates come from the persisted `problem_zone`, scaled against the stored drawing asset coordinate space instead of any browser-side heuristic.
            </p>
            {problemZone === null && (
              <p>
                No active issue with `problem_zone` evidence is selected, so the panel is currently in plain drawing-preview mode.
              </p>
            )}
            {problemZone !== null && matchedAsset === null && selectedAsset !== null && (
              <p>
                The active issue points to {problemZone.sheet_id ?? "an unknown sheet"}, but no persisted preview asset matches that sheet/page exactly. You can still browse the available report assets here.
              </p>
            )}
            {!isOverlayTarget && selectedAsset !== null && matchedAsset !== null && (
              <p>
                You are browsing {describeAsset(selectedAsset)}. The active issue overlay belongs to {describeAsset(matchedAsset)}, so the rectangle is intentionally hidden until you switch back to the matching asset.
              </p>
            )}
            {problemZone !== null && matchedAsset !== null && !canDrawOverlay && !imageError && (
              <p>
                Preview loaded, but the current issue does not yet have a complete rectangle payload for x/y/width/height on the selected asset.
              </p>
            )}
          </div>
        </>
      )}
    </section>
  );
}