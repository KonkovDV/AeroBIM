import { useEffect, useState } from "react";
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

export default function DrawingEvidencePanel({ report, activeIssue }: DrawingEvidencePanelProps) {
  const [imageMetrics, setImageMetrics] = useState<{ width: number; height: number } | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);

  const problemZone = activeIssue?.problem_zone ?? null;
  const matchedAsset = report ? findMatchingAsset(report, activeIssue) : null;
  const previewUrl = report && matchedAsset ? buildDrawingAssetPreviewUrl(report.report_id, matchedAsset.asset_id) : null;

  useEffect(() => {
    setImageMetrics(null);
    setImageError(null);
  }, [previewUrl]);

  const coordinateWidth = matchedAsset?.coordinate_width ?? imageMetrics?.width ?? null;
  const coordinateHeight = matchedAsset?.coordinate_height ?? imageMetrics?.height ?? null;
  const canDrawOverlay =
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
      ) : problemZone === null ? (
        <div className="panel-empty compact">The active issue has no persisted drawing problem zone.</div>
      ) : matchedAsset === null ? (
        <div className="panel-empty compact">No persisted drawing asset matches the active issue sheet and page.</div>
      ) : (
        <>
          <div className="drawing-evidence-meta">
            <span>{matchedAsset.sheet_id}</span>
            <span>{matchedAsset.page_number ? `page ${matchedAsset.page_number}` : "page n/a"}</span>
            <span>{matchedAsset.media_type}</span>
          </div>

          <div className="drawing-evidence-stage">
            <img
              src={previewUrl ?? undefined}
              alt={`Drawing evidence preview for ${matchedAsset.sheet_id}`}
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
            <strong>{activeIssue?.rule_id ?? "Active issue"}</strong>
            <p>
              Overlay coordinates come from the persisted `problem_zone`, scaled against the stored drawing asset coordinate space instead of any browser-side heuristic.
            </p>
            {!canDrawOverlay && !imageError && (
              <p>
                Preview loaded, but the issue does not yet have a complete rectangle payload for x/y/width/height.
              </p>
            )}
          </div>
        </>
      )}
    </section>
  );
}