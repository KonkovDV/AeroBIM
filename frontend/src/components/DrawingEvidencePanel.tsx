import { useEffect, useMemo, useState } from "react";
import { fetchDrawingAssetPreviewBlobUrl } from "../lib/api";
import type {
  DrawingAsset,
  DrawingRegionRef,
  ValidationIssue,
  ValidationReport,
} from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";

interface DrawingEvidencePanelProps {
  report: ValidationReport | null;
  activeIssue: ValidationIssue | null;
}

type OverlayRect = {
  key: string;
  className: string;
  style: { left: string; top: string; width: string; height: string };
  label: string;
};

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
  return UI_COPY.drawingPage(asset.sheet_id, asset.page_number);
}

function isNormalizedBBox(region: DrawingRegionRef): boolean {
  const system = (region.coordinate_system ?? "").toLowerCase();
  if (system.includes("normalized")) {
    return true;
  }
  const [x0, y0, x1, y1] = region.bbox_xyxy;
  return [x0, y0, x1, y1].every((value) => value >= 0 && value <= 1.0001);
}

function regionPixelBox(
  region: DrawingRegionRef,
  imageMetrics: { width: number; height: number },
  coordinateWidth: number,
  coordinateHeight: number,
): { left: number; top: number; width: number; height: number } | null {
  const [x0, y0, x1, y1] = region.bbox_xyxy;
  if (!(x1 > x0 && y1 > y0)) {
    return null;
  }
  if (isNormalizedBBox(region)) {
    return {
      left: x0 * imageMetrics.width,
      top: y0 * imageMetrics.height,
      width: (x1 - x0) * imageMetrics.width,
      height: (y1 - y0) * imageMetrics.height,
    };
  }
  const pageWidth = region.page_width ?? coordinateWidth;
  const pageHeight = region.page_height ?? coordinateHeight;
  if (pageWidth <= 0 || pageHeight <= 0) {
    return null;
  }
  return {
    left: (x0 / pageWidth) * imageMetrics.width,
    top: (y0 / pageHeight) * imageMetrics.height,
    width: ((x1 - x0) / pageWidth) * imageMetrics.width,
    height: ((y1 - y0) / pageHeight) * imageMetrics.height,
  };
}

function regionClassName(region: DrawingRegionRef): string {
  const role = (region.layout_role ?? "content").toLowerCase();
  if (role === "stamp") {
    return "drawing-evidence-rect drawing-evidence-rect-stamp";
  }
  if (role === "title_block") {
    return "drawing-evidence-rect drawing-evidence-rect-title";
  }
  if (region.hitl_required === true) {
    return "drawing-evidence-rect drawing-evidence-rect-hitl";
  }
  return "drawing-evidence-rect drawing-evidence-rect-region";
}

export default function DrawingEvidencePanel({ report, activeIssue }: DrawingEvidencePanelProps) {
  const [imageMetrics, setImageMetrics] = useState<{ width: number; height: number } | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

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

  useEffect(() => {
    let revokedUrl: string | null = null;
    let cancelled = false;

    if (!report || !selectedAsset) {
      setPreviewUrl(null);
      return;
    }

    fetchDrawingAssetPreviewBlobUrl(report.report_id, selectedAsset.asset_id)
      .then((url) => {
        if (cancelled) {
          URL.revokeObjectURL(url);
          return;
        }
        revokedUrl = url;
        setPreviewUrl(url);
      })
      .catch(() => {
        if (!cancelled) {
          setPreviewUrl(null);
          setImageError("Failed to load the persisted drawing preview for this issue.");
        }
      });

    return () => {
      cancelled = true;
      if (revokedUrl) {
        URL.revokeObjectURL(revokedUrl);
      }
    };
  }, [report, selectedAsset]);

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

  const issueOverlay: OverlayRect | null =
    normalizedZone !== null && imageMetrics !== null && coordinateWidth !== null && coordinateHeight !== null
      ? {
          key: "problem-zone",
          className: "drawing-evidence-rect",
          label: "problem_zone",
          style: {
            left: `${(normalizedZone.x / coordinateWidth) * imageMetrics.width}px`,
            top: `${(normalizedZone.y / coordinateHeight) * imageMetrics.height}px`,
            width: `${(normalizedZone.width / coordinateWidth) * imageMetrics.width}px`,
            height: `${(normalizedZone.height / coordinateHeight) * imageMetrics.height}px`,
          },
        }
      : null;

  const sheetRegions = useMemo(() => {
    if (!selectedAsset || !report?.drawing_regions) {
      return [] as DrawingRegionRef[];
    }
    return report.drawing_regions.filter((region) => region.sheet_id === selectedAsset.sheet_id);
  }, [report, selectedAsset]);

  const regionOverlays = useMemo(() => {
    if (!imageMetrics || coordinateWidth === null || coordinateHeight === null) {
      return [] as OverlayRect[];
    }
    const overlays: OverlayRect[] = [];
    sheetRegions.forEach((region, index) => {
      const box = regionPixelBox(region, imageMetrics, coordinateWidth, coordinateHeight);
      if (box === null) {
        return;
      }
      overlays.push({
        key: `region-${region.sheet_id}-${index}`,
        className: regionClassName(region),
        label: region.layout_role ?? region.modality,
        style: {
          left: `${box.left}px`,
          top: `${box.top}px`,
          width: `${box.width}px`,
          height: `${box.height}px`,
        },
      });
    });
    return overlays;
  }, [sheetRegions, imageMetrics, coordinateWidth, coordinateHeight]);

  const hitlRegions = useMemo(
    () => (report?.drawing_regions ?? []).filter((region) => region.hitl_required === true),
    [report],
  );

  return (
    <section className="panel drawing-evidence-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">{UI_COPY.drawingKicker}</p>
          <h2>{UI_COPY.drawingTitle}</h2>
        </div>
      </div>

      {report === null ? (
        <div className="panel-empty compact">{UI_COPY.selectReportDrawing}</div>
      ) : drawingAssets.length === 0 ? (
        <div className="panel-empty compact">{UI_COPY.noDrawingAssets}</div>
      ) : (
        <>
          <div className="drawing-evidence-meta">
            <span>{selectedAsset ? describeAsset(selectedAsset) : UI_COPY.assetNa}</span>
            <span>{selectedAsset?.media_type ?? UI_COPY.previewNa}</span>
            <span>{isOverlayTarget ? UI_COPY.overlayTarget : UI_COPY.browseMode}</span>
            {regionOverlays.length > 0 ? (
              <span className="selection-badge">{UI_COPY.regionOverlays(regionOverlays.length)}</span>
            ) : null}
            {hitlRegions.length > 0 ? (
              <span className="selection-badge">{UI_COPY.hitlRegions(hitlRegions.length)}</span>
            ) : null}
          </div>

          {hitlRegions.length > 0 && (
            <ul className="drawing-hitl-list" aria-label={UI_COPY.hitlRegionsAria}>
              {hitlRegions.map((region, index) => (
                <li key={`${region.sheet_id}-${index}`}>
                  <strong>{region.sheet_id}</strong>
                  <span>{region.modality}</span>
                  <span>{region.hitl_reason ?? "hitl_required"}</span>
                  <span>conf={region.confidence.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          )}

          {drawingAssets.length > 1 && (
            <div className="drawing-evidence-selector" role="tablist" aria-label={UI_COPY.drawingAssetsAria}>
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
                    {isMatch && <span className="selection-badge">{UI_COPY.issueMatch}</span>}
                  </button>
                );
              })}
            </div>
          )}

          <div className="drawing-evidence-stage">
            <img
              src={previewUrl ?? undefined}
              alt={UI_COPY.drawingAlt(selectedAsset?.sheet_id ?? "drawing")}
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
            {regionOverlays.map((overlay) => (
              <div
                key={overlay.key}
                className={overlay.className}
                style={overlay.style}
                data-region-label={overlay.label}
              />
            ))}
            {issueOverlay && (
              <div className={issueOverlay.className} style={issueOverlay.style} data-testid="problem-zone-overlay" />
            )}
            {imageError && (
              <div className="viewer-overlay viewer-overlay-error">
                <p>{imageError}</p>
              </div>
            )}
          </div>

          <div className="drawing-evidence-caption">
            <strong>{activeIssue?.rule_id ?? "Report drawing evidence"}</strong>
            <p>
              Finding rectangle comes from persisted `problem_zone`. Sheet regions (`DrawingRegionRef`, including stamp/title priors) are drawn for the selected asset when coordinates are present — layout priors are not a product literacy claim.
            </p>
            {problemZone === null && (
              <p>
                No active issue with `problem_zone` evidence is selected, so the panel is currently in plain drawing-preview mode.
              </p>
            )}
            {problemZone !== null && matchedAsset === null && selectedAsset !== null && (
              <p>
                {UI_COPY.unmatchedSheet(problemZone.sheet_id ?? "лист")}
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
